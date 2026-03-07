import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db import Base


class JobStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DLQ = "dlq"  # dead-letter queue


class JobPriority:
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_type = Column(String(64), nullable=False, index=True)
    payload = Column(JSONB, default=dict)
    status = Column(String(32), default=JobStatus.PENDING, index=True)
    priority = Column(String(16), default=JobPriority.NORMAL, index=True)
    retries = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    result = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
