from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from zoneinfo import ZoneInfo
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from datetime import timezone
from typing import List 
load_dotenv()


from scheduler import get_job_scheduler, send_to_rabbitmq
from database import init_db, get_db, Jobs
from schema import JobResponse, SingleJob, Job


# Initialises the connection to the scheduler db.
scheduler = get_job_scheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):

    # Connect to db and create table if not already created.
    init_db()
    #Starts the background scheduler process, and also loads all the jobs from the jobstore.
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)

app = FastAPI(
    title="Scheduler Microservice",
    lifespan=lifespan,
)


@app.get("/healthcheck", response_model=str)
async def health():
    return "ok"


@app.get("/jobs", response_model=List[JobResponse])
async def get_jobs():
    """
    Lists all scheduled jobs only from the jobstore.
    """
    
    #Only picking jobs from the jobstore.
    jobs = scheduler.get_jobs()
    
    items: List[JobResponse] = []
    
    for j in jobs:
        cron_str = str(j.trigger)
        fields = j.args[2] if (j.args and len(j.args) > 2) else {}
        print(fields, j.args)

        items.append(JobResponse(
            id=j.id,
            name=j.name,
            cron=cron_str,
            job_fields=fields
        ))
    
    return items


@app.get("/jobs/{job_id}", response_model=SingleJob)
async def get_jobs(job_id: str, db: Session = Depends(get_db)):
    """
    Lists single job from the db along with the required  field from jobstore.
    """ 
    
    #Picking the job from the db.
    job = db.query(Jobs).filter(Jobs.job_id == job_id).first()
    # Only need the next-run-time from the jobstore.
    jobstore = scheduler.get_job(job_id, jobstore="default")
    if job and jobstore:
        job_details = SingleJob(
            name=job.name,
            cron=job.cron,
            job_id=job.job_id,
            last_run_at=job.last_run_at,
            next_run_at=jobstore.next_run_time.astimezone(ZoneInfo("Asia/Kolkata")), #Stored as epoch time, converted to local time.
            job_fields=job.job_fields,
        )
        return job_details
    else:
        raise HTTPException(status_code=404, detail="Job not found")


@app.post("/jobs", status_code=201, response_model=JobResponse)
async def create_job(job: Job, db: Session = Depends(get_db)):
    """
    Adds a new cron job into the shared SQLAlchemy jobstore, and saves to a separate table. 
    The scheduler worker process will execute it.
    """
    
    existing = db.execute(select(Jobs.id).where(Jobs.name == job.name)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=400, detail=f"Job name '{job.name}' already exists")
    
    try:
        trigger = CronTrigger.from_crontab(job.cron, timezone=timezone.utc)
        
        # Adds to the APScheduler jobstore.
        new_job = scheduler.add_job(
            func=send_to_rabbitmq,
            trigger=trigger,
            name=job.name,
            args=[None, job.name, job.job_fields],
            jobstore="default",
            replace_existing=False,
        )
        jobstore_id= new_job.id
                
    
        # Adds to our database.
        job_db = Jobs(
            name=job.name,
            cron=job.cron,
            job_fields=job.job_fields,
            job_id=jobstore_id,
        )
                
        
        db.add(job_db)
        db.commit()
        db.refresh(job_db)
        
        
        # Modifies the job in the jobstore with the db id, so that the worker can update the last_run_at time.
        scheduler.modify_job(jobstore_id, jobstore="default",
                     args=[job_db.id, job.name, job.job_fields])
        
        job_details = JobResponse(
            id=jobstore_id,
            name=job.name,
            cron=job.cron,
            job_fields=job.job_fields
        )
        
        return job_details

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


