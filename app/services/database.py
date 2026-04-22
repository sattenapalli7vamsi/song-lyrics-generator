import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import uuid

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    pkid = Column(Integer, primary_key=True, autoincrement=True)
    userid = Column(String, unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    useremail = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Song(Base):
    __tablename__ = "songs"
    pkid = Column(Integer, primary_key=True, autoincrement=True)
    songid = Column(String, unique=True, nullable=False, default= lambda: str(uuid.uuid4()))
    vocalprint = Column(String(512), unique=True, nullable=False)
    s3_lyrics_url = Column(Text, nullable=False)
    created_at = Column(DateTime, default= lambda: datetime.now(timezone.utc))

class Job(Base):
    __tablename__ = "jobs"
    pkid = Column(Integer, primary_key= True, autoincrement= True)
    jobid = Column(String, unique=True, nullable= False, default= lambda: str(uuid.uuid4()))
    userid = Column(String, nullable= True)
    s3_file_url = Column(Text, nullable=False)
    s3_lyrics_url = Column(Text, nullable= True)
    status = Column(String(50), default= "pending")
    retry_count = Column(Integer, default=0)
    cache_hit = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default= lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default= lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()