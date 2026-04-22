from fastapi import APIRouter

router = APIRouter  (prefix= "/lyrics", tags=["lyrics"])

@router.post("/upload")
async def upload_audio():
    return {"message": "upload endpoint coming soon"}

@router.get("/search")
async def search_lyrics():
    return {"message": "search endpoint coming soon"}

@router.get("/download/{song_id}")
async def download_lyrics(song_id: str):
    return {"message": f"download endpoint for {song_id} coming soon"}