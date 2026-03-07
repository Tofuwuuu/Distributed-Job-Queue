from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field

PriorityLiteral = Literal["high", "normal", "low"]


class JobCreate(BaseModel):
    job_type: str = Field(..., min_length=1, max_length=64)
    payload: dict = Field(default_factory=dict)
    priority: PriorityLiteral = "normal"


class JobResponse(BaseModel):
    id: UUID
    job_type: str
    payload: dict
    status: str
    priority: str
    retries: int
    max_retries: int
    result: dict | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int


class QueueStatsResponse(BaseModel):
    high: int
    normal: int
    low: int
    dlq: int


class DashboardStats(BaseModel):
    pending: int
    processing: int
    completed: int
    failed: int
    dlq: int
    queue_lengths: QueueStatsResponse
