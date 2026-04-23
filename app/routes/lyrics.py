from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.storage import upload_file, generate_presigned_url, get_s3_key
from app.services.vocalprint import generate_vocalprint, save_audio_temp, cleanup_temp
from app.services.cache import exists_vocalprint, save_vocalprint, set_lock
from app.services.database import get_db, User, Job, Song
from app.services.queue import push_to_queue
from app.models.schemas import UploadResponse, SongItem
from datetime import datetime, timezone
import uuid
from pydantic import EmailStr

router = APIRouter(prefix= "/lyrics", tags=["lyrics"])

@router.post("/upload")
async def upload_audio(
    file: UploadFile = File(...),
    email: EmailStr = Form(...)
):
    #Validate file type
    if not file.content_type in ["audio/mpeg", "audio/mp3"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload an MP3 file only."
        )
    
    #Read file bytes and save to temp
    file_bytes = await file.read()
    temp_path = save_audio_temp(file_bytes, file.filename)

    try:
        #Generate vocalprint
        vocalprint = generate_vocalprint(temp_path)

        #Check Redis cache
        cached_lyrics_url = exists_vocalprint(vocalprint)
        if cached_lyrics_url:
            return UploadResponse(
                status = "found",
                message = "Your lyrics are ready!",
                songs = [SongItem(
                    title=file.filename,
                    download_url=generate_presigned_url(cached_lyrics_url)
                )]
            )
        
        #Check database
        db = next(get_db())
        song = db.query(Song).filter(Song.vocalprint == vocalprint).first()
        if song:
            save_vocalprint(vocalprint, song.s3_lyrics_url)
            return UploadResponse(
                status="found",
                message="Your lyrics are ready!",
                songs = [SongItem(
                    title = file.filename,
                    download_url = generate_presigned_url(song.s3_lyrics_url)
                )]
            )
        
        #New Song, set lock
        set_lock(vocalprint)

        #Check or create user
        user = db.query(User).filter(User.useremail == email).first()
        if not user:
            user = User(
                userid = str(uuid.uuid4()),
                useremail = email
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        #Upload MP3 to S3
        job_id = str(uuid.uuid4())
        safe_filename = file.filename.replace(" ", "_")
        s3_key = upload_file(file_bytes, "uploads", f"{job_id}_{safe_filename}")

        #Create job in PostgreSQL
        job = Job(
            jobid = job_id,
            userid = user.userid,
            s3_file_url = s3_key,
            status = "pending",
            cache_hit = False,
            original_filename = file.filename
        )
        db.add(job)
        db.commit()

        #Push to SQS
        push_to_queue(
            jobid =  job_id,
            s3_file_url = s3_key,
            useremail = email,
            original_filename = file.filename
        )
        return UploadResponse(
            status = "processing",
            message = f"Lyrics will be emailed to you at {email} once ready"
        )
    
    finally:
        cleanup_temp(temp_path)

async def search_lyrics():
    return {"message": "search endpoint coming soon"}

@router.get("/download/{song_id}")
async def download_lyrics(song_id: str):
    return {"message": f"download endpoint for {song_id} coming soon"}