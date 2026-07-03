"""
database.py
------------
SQLAlchemy models and session management for the Personalized Networking
Assistant. Uses SQLite by default (zero-config, file based). Swap the
DATABASE_URL env var to point at PostgreSQL in production without changing
any other code.
"""

import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/networking_assistant.db")

# check_same_thread is only needed for SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=True)
    bio = Column(Text, nullable=True)
    interests = Column(Text, nullable=True)  # comma-separated
    created_at = Column(DateTime, default=datetime.utcnow)


class InteractionLog(Base):
    __tablename__ = "interaction_logs"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, nullable=True)
    event_description = Column(Text, nullable=False)
    interests = Column(Text, nullable=True)
    extracted_themes = Column(Text, nullable=True)  # comma-separated
    generated_starters = Column(Text, nullable=False)  # JSON-encoded list
    fact_check_query = Column(Text, nullable=True)
    fact_check_result = Column(Text, nullable=True)
    feedback = Column(Boolean, nullable=True)  # True = thumbs up, False = thumbs down, None = no feedback
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
