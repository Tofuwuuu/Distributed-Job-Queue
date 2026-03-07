from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_async_db
from app.models import Job, JobStatus
from app.schemas import JobCreate, JobResponse, JobListResponse, DashboardStats, QueueStatsResponse
from app.queue_service import enqueue, get_queue_lengths

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobResponse)
async def submit_job(
    body: JobCreate,
    db: AsyncSession = Depends(get_async_db),
):
    job = Job(
        job_type=body.job_type,
        payload=body.payload,
        priority=str(body.priority),
        max_retries=3,
    )
    db.add(job)
    await db.flush()
    enqueue(str(job.id), job.job_type, job.payload, job.priority)
    await db.refresh(job)
    return job


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: str | None = Query(None, description="Filter by status"),
    job_type: str | None = Query(None, description="Filter by job type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_async_db),
):
    q = select(Job).order_by(Job.created_at.desc())
    count_q = select(func.count(Job.id))
    if status:
        q = q.where(Job.status == status)
        count_q = count_q.where(Job.status == status)
    if job_type:
        q = q.where(Job.job_type == job_type)
        count_q = count_q.where(Job.job_type == job_type)
    total = (await db.execute(count_q)).scalar_one()
    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    jobs = result.scalars().all()
    return JobListResponse(jobs=jobs, total=total)


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_async_db)):
    from sqlalchemy import select, func
    from app.models import Job, JobStatus

    # Count by status
    q = select(Job.status, func.count(Job.id)).group_by(Job.status)
    rows = (await db.execute(q)).all()
    by_status = {row[0]: row[1] for row in rows}
    pending = by_status.get(JobStatus.PENDING, 0)
    processing = by_status.get(JobStatus.PROCESSING, 0)
    completed = by_status.get(JobStatus.COMPLETED, 0)
    failed = by_status.get(JobStatus.FAILED, 0)
    dlq = by_status.get(JobStatus.DLQ, 0)

    queue_lengths = get_queue_lengths()
    return DashboardStats(
        pending=pending,
        processing=processing,
        completed=completed,
        failed=failed,
        dlq=dlq,
        queue_lengths=QueueStatsResponse(**queue_lengths),
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(select(Job).where(Job.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
