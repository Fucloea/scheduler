from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional
from datetime import datetime
from croniter import croniter


#Defines the schemas for the request and responses.

class Job(BaseModel):
    name: str = Field(..., example="every-5-minutes-job")
    cron: str = Field(..., example="*/5 * * * *")
    job_fields: Dict = Field(
        ..., example={"report_type": "monthly", "user_id": 123}
    )

    # Validate cron string
    @field_validator("cron")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        if not croniter.is_valid(v):
            raise ValueError(f"Invalid cron expression: {v}")
        return v
    
class JobResponse(BaseModel):
    id: Optional[str] = "46c1e327d3"
    name: str = Field(..., example="per-minute-job")
    cron: str = Field(..., example="*/1 * * * *")
    job_fields: Dict = Field(
        ..., example={"message": "hello", "user_id": 123}
    )
    
class SingleJob(BaseModel):
    job_id: Optional[str] = "46c1e327d3"
    name: str = Field(..., example="per-minute-job")
    cron: str = Field(..., example="*/1 * * * *")
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    job_fields: Dict = Field(
        ..., example={"message": "hello", "user_id": 123}
    )