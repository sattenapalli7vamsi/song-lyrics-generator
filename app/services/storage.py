import os
from dotenv import load_dotenv
import boto3

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

s3_client = boto3.client(
    "s3",
    region_name = AWS_REGION,
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY
)

def get_s3_key(folder: str, filename: str) -> str:
    return f"{folder}/{filename}"

def upload_file(file_bytes: bytes, folder: str, filename: str) -> str:
    s3_key = get_s3_key(folder, filename)
    s3_client.put_object(
        Bucket = S3_BUCKET_NAME,
        Key = s3_key,
        Body = file_bytes
    )
    return s3_key

def download_file(s3_key: str) -> bytes:
    response = s3_client.get_object(
        Bucket = S3_BUCKET_NAME,
        Key = s3_key
    )
    return response["Body"].read()

def generate_presigned_url(s3_key: str, expiry: int = 86400) -> str:
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET_NAME, "Key": s3_key},
        ExpiresIn = expiry
    )
    return url