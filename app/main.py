from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes import lyrics

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up Song Lyrics Generator...")
    yield
    print("Shutting down...")

app = FastAPI(
    title = "Song Lyrics Generator",
    description= "Upload audio and receive AI generated lyrics",
    version= "1.0.0",
    lifespan= lifespan
)

app.include_router(lyrics.router)

@app.get("/health")
async def health():
    return {"status": "ok"}