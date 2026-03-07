"""
Worker: consumes jobs from Redis (priority queues), updates PostgreSQL, retries or DLQ.
"""
import json
import sys
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from db import get_session
from models import Job
from queue_client import dequeue, enqueue_dlq
from handlers import run_job
import redis

# Re-enqueue for retry: push back to Redis (same priority key from message if we store it)
def re_enqueue(session: Session, job_id: str, job_type: str, payload: dict, priority: str):
    r = redis.from_url(settings.redis_url, decode_responses=True)
    key = {"high": settings.queue_high, "normal": settings.queue_normal, "low": settings.queue_low}.get(priority, settings.queue_normal)
    message = json.dumps({"job_id": job_id, "job_type": job_type, "payload": payload})
    r.lpush(key, message)


def process_one(session: Session) -> bool:
    message = dequeue(block_timeout=5)
    if not message:
        return False
    job_id = message["job_id"]
    job_type = message["job_type"]
    payload = message.get("payload") or {}

    row = session.execute(select(Job).where(Job.id == UUID(job_id))).scalar_one_or_none()
    if not row:
        return True  # job deleted, skip
    job = row

    job.status = "processing"
    job.started_at = datetime.utcnow()
    session.commit()

    try:
        result = run_job(job_type, payload)
        job.status = "completed"
        job.result = result
        job.completed_at = datetime.utcnow()
        job.error_message = None
        session.commit()
        return True
    except Exception as e:
        job.retries = (job.retries or 0) + 1
        err_msg = str(e)
        job.error_message = err_msg
        if job.retries >= (job.max_retries or settings.max_retries):
            job.status = "dlq"
            session.commit()
            enqueue_dlq(job_id, job_type, payload, err_msg)
        else:
            job.status = "pending"
            session.commit()
            re_enqueue(session, job_id, job_type, payload, job.priority or "normal")
        return True


def main():
    print("Worker started. Consuming from Redis (high -> normal -> low)...", flush=True)
    while True:
        session = get_session()
        try:
            process_one(session)
        except KeyboardInterrupt:
            session.close()
            sys.exit(0)
        except Exception as e:
            print(f"Worker error: {e}", flush=True)
        finally:
            session.close()


if __name__ == "__main__":
    main()
