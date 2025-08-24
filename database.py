from sqlalchemy import (
    create_engine, Column, String, Text, Boolean, DateTime, func, JSON, Integer
)
from typing import Any
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic import BaseModel
from dotenv import load_dotenv
import os
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

Base = declarative_base()


# Would ideally store all table cleasses in a separate file; something like "models.py"
class Jobs(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)  
    name = Column(String, nullable=False, unique=True)
    cron = Column(Text, nullable=True)
    job_fields = Column(JSON, nullable=True)
    job_id = Column(String, nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
