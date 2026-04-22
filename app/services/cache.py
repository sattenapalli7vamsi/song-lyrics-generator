import redis
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
LOCK_TTL = 600

r = redis.from_url(REDIS_URL, decode_responses = True)

def exists_vocalprint(vocalprint: str) -> str | None:
    return r.get(f"vocalprint:{vocalprint}")

def save_vocalprint(vocalprint: str, lyrics_url: str):
    r.set(f"vocalprint:{vocalprint}", lyrics_url)

def set_lock(vocalprint: str) -> bool:
    return r.set(f"lock:vocalprint:{vocalprint}", "processing", nx=True, ex=LOCK_TTL)

def release_lock(vocalprint: str):
    r.delete(f"lock:vocalprint:{vocalprint}")

def check_lock(vocalprint: str) -> bool:
    return r.exists(f"lock:vocalprint:{vocalprint}") > 0