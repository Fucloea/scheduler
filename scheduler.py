from datetime import timezone as dt_timezone
from typing import Dict 
import logging
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import os
load_dotenv()

from database import SessionLocal, Jobs
from sqlalchemy import update, func

DATABASE_URL = os.environ["DATABASE_URL"]  


scheduler = None

# The APScehdule library initiates its own db and processes.
def get_job_scheduler():
    global scheduler
    
    if scheduler is None:
        jobstores = {"default": SQLAlchemyJobStore(url=DATABASE_URL)}
        executors = {"default": ThreadPoolExecutor(20)}
        job_defaults = {"coalesce": True, "max_instances": 1}

        scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=dt_timezone.utc,
        )
    
    return scheduler



def send_to_rabbitmq(db_id: int, job_name: str, parameters: Dict):
    """
    Placeholder func that is meant to imitate the process of adding to a message queue. 
    I would replace this part with actual RabbitMQ publishing.
    """
    
    logger = logging.getLogger(job_name)
    
    #Since the jobs names are dynamic, we initalise a format for each when the new job is created.
    if not logger.handlers:
        handler = logging.FileHandler(f"{job_name}.log", mode="a")
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    
    db = SessionLocal()
    try:
        logger.info("Job queued with parameters: %s", parameters)
        stmt = update(Jobs).where(Jobs.id == db_id).values(last_run_at=func.now())
        db.execute(stmt)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
