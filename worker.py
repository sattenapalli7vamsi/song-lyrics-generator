import json
import boto3
import time
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from app.services.database import SessionLocal, Job, Song
from app.services.storage import download_file, upload_file, generate_presigned_url
from app.services.vocalprint import save_audio_temp, cleanup_temp
from app.services.cache import save_vocalprint, release_lock
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
import whisper

load_dotenv()

SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SES_SENDER_EMAIL = os.getenv("SES_SENDER_EMAIL")

sqs_client = boto3.client(
    "sqs",
    region_name = AWS_REGION,
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY
)

ses_client = boto3.client(
    "ses",
    region_name = AWS_REGION,
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY
)

whisper_model = whisper.load_model("medium")
llm = OllamaLLM(model = "llama3:8b")

prompt_template = PromptTemplate(
    input_variables=["transcript"],
    template="""
    You are a creative Telugu songs lyric writer. Based on the following transcript 
    which may be in English or Telugu, write creative and meaningful Telugu 
    song lyrics. 
    
    IMPORTANT: Write the lyrics in Telugu language but using English alphabet 
    (transliteration). For example: "idhe kadha nee kadha, marachipovu naa kadha".
    Include verses and a chorus. Keep the emotion and theme of the original transcript.
    
    Transcript: {transcript}
    
    Telugu Song Lyrics (in English alphabet):
    """
)

chain = prompt_template | llm

def update_job_status(db: Session, jobid: str, status: str, error_message: str= None, s3_lyrics_url: str = None):
    job = db.query(Job).filter(Job.jobid == jobid).first()
    if job:
        job.status = status
        if error_message:
            job.error_message = error_message
        if s3_lyrics_url:
            job.s3_lyrics_url = s3_lyrics_url
        db.commit()

def send_email(useremail: str, lyrics: str, download_url: str):
    ses_client.send_email(
        Source = SES_SENDER_EMAIL,
        Destination = {"ToAddresses": [useremail]},
        Message = {
            "Subject": {"Data": "Your Song Lyrics Are Ready!"},
            "Body": {
                "Text": {
                    "Data": f"Your lyrics are ready!\n\nDownload here: {download_url}\n\nLyrics Preview:\n{lyrics[:500]}"
                }
            }
        }
    )

def send_failure_email(useremail: str):
    ses_client.send_email(
        SSource = SES_SENDER_EMAIL,
        Destination = {"ToAddresses": [useremail]},
        Message = {
            "Subject": {"Data": "We couldn't process your song"},
            "Body": {
                "Text": {
                    "Data": "Unfortunately we were unable to process your audio file after multiple attempts. Please try uploading again."
                }
            }
        }
    )

def process_job(message: dict):
    jobid = message["jobid"]
    s3_file_url = message["s3_file_url"]
    useremail = message["useremail"]
    original_filename = message["original_filename"]

    db = SessionLocal()
    temp_path = None
    job = None
    try: 
        #Update job status to processing
        update_job_status(db, jobid, "processing")

        #Download MP3 from S3
        file_bytes = download_file(s3_file_url)
        print(f"Downloaded file bytes: {len(file_bytes) if file_bytes else 'None'}")
        temp_path = save_audio_temp(file_bytes, original_filename)
        print(f"Temp path: {temp_path}")

        #Transcribe with Whisper
        result = whisper_model.transcribe(temp_path, language = None, task = "transcribe")
        print(f"Full result: {result}")
        transcript = result["text"]
        print(f"Transcript: {transcript[:100] if transcript else 'None'}")

        #Generate lyrics with Ollama
        lyrics = chain.invoke({"transcript": transcript})
        print(f"Lyrics: {lyrics[:100] if lyrics else 'None'}")

        #Save lyrics to S3
        lyrics_key = upload_file(lyrics.encode(), "lyrics", f"{jobid}_lyrics.txt")

        #Save song to database
        job = db.query(Job).filter(Job.jobid == jobid).first()
        song = Song(
            vocalprint = job.s3_file_url,
            s3_lyrics_url = lyrics_key
        )

        db.add(song)
        db.commit()
        db.expire_on_commit = False
        #Update cache
        save_vocalprint(job.s3_file_url, lyrics_key)

        #Generate presigned URL
        download_url = generate_presigned_url(lyrics_key)

        #Update job status
        update_job_status(db, jobid, "completed", s3_lyrics_url= lyrics_key)

        #Send email
        send_email(useremail, lyrics, download_url)

    except Exception as e:
        update_job_status(db, jobid, "failed", error_message=str(e))
        raise

    finally:
        if temp_path:
            cleanup_temp(temp_path)
        
        db.close()
        if job:
            release_lock(s3_file_url)

def poll_queue():
    print("Worker started - polling SQS...")
    while True:
        response = sqs_client.receive_message(
            QueueUrl = SQS_QUEUE_URL,
            MaxNumberOfMessages = 1,
            WaitTimeSeconds = 20
        )
        
        messages = response.get("Messages", [])
        if not messages:
            print("No messages - waiting...")
            continue
            
        for message in messages:
            body = json.loads(message["Body"])
            print(f"Processing job: {body['jobid']}")

            try:
                process_job(body)
                #Delete message from queue on success
                sqs_client.delete_message(
                    QueueUrl = SQS_QUEUE_URL,
                    ReceiptHandle = message["ReceiptHandle"]
                )
                print(f"Job completed: {body['jobid']}")
            except Exception as e:
                print(f"Job failed: {body['jobid']}-{str(e)}")


if __name__ == "__main__":
    poll_queue()