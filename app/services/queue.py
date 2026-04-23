import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL")
AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

sqs_client = boto3.client(
    "sqs",
    region_name = AWS_REGION,
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY
)

def push_to_queue(jobid: str, s3_file_url: str, useremail: str, original_filename: str):
    message = {
        "jobid": jobid,
        "s3_file_url": s3_file_url,
        "useremail": useremail,
        "original_filename": original_filename
    }

    sqs_client.send_message(
        QueueUrl = SQS_QUEUE_URL,
        MessageBody = json.dumps(message)
    )