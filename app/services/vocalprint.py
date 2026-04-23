import acoustid
import os
from dotenv import load_dotenv

load_dotenv()

ACCOUSTID_API_KEY = os.getenv("ACCOUSTID_API_KEY", "local")

def generate_vocalprint(file_path: str) -> str:
    duration, vocalprint = acoustid.fingerprint_file(file_path)
    if isinstance(vocalprint, bytes):
        return vocalprint.decode('utf-8')
    return vocalprint

def save_audio_temp(file_bytes: bytes, filename: str) ->str:
    temp_path = f"/tmp/{filename}"
    with open(temp_path, "wb") as f:
        f.write(file_bytes)
    return temp_path

def cleanup_temp(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)