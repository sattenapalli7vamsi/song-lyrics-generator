from pydantic import BaseModel, EmailStr
from typing import Optional, List

class SongItem(BaseModel):
    title: str
    downloadUrl: str

class UploadResponse(BaseModel):
    status: str
    message: str
    songs: Optional[List[SongItem]] = None

class SearchResponse(BaseModel):
    status: str
    message: Optional[str] = None
    songs: Optional[List[SongItem]] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    lyrics_url: Optional[str] = None
    cache_hit: bool = False
    submitted_at: str
    completed_at: Optional[str] = None

class UploadRequest(BaseModel):
    email: EmailStr