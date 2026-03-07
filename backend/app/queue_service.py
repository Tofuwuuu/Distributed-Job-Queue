import json
import uuid
from typing import Any, Optional

import redis
from app.config import settings
from app.models import JobPriority

# Priority order: high first, then normal, then low (worker pops in this order)
QUEUE_KEYS_BY_PRIORITY = [settings.queue_high, settings.queue_normal, settings.queue_low]


def get_redis() -> redis.Redis:
    return redis.from_url(settings.redis_url, decode_responses=True)


def queue_key(priority: str) -> str:
    return {
        JobPriority.HIGH: settings.queue_high,
        JobPriority.NORMAL: settings.queue_normal,
        JobPriority.LOW: settings.queue_low,
    }.get(priority, settings.queue_normal)


def enqueue(job_id: str, job_type: str, payload: dict, priority: str = JobPriority.NORMAL) -> None:
    r = get_redis()
    key = queue_key(priority)
    message = json.dumps({"job_id": job_id, "job_type": job_type, "payload": payload})
    r.lpush(key, message)


def dequeue(block_timeout: int = 0) -> Optional[dict]:
    """Pop one job from queues in priority order. block_timeout in seconds (0 = block forever)."""
    r = get_redis()
    result = r.brpop(QUEUE_KEYS_BY_PRIORITY, timeout=block_timeout)
    if not result:
        return None
    _key, message = result
    return json.loads(message)


def enqueue_dlq(job_id: str, job_type: str, payload: dict, error: str) -> None:
    r = get_redis()
    message = json.dumps({
        "job_id": job_id,
        "job_type": job_type,
        "payload": payload,
        "error": error,
    })
    r.lpush(settings.queue_dlq, message)


def get_queue_lengths() -> dict[str, int]:
    r = get_redis()
    return {
        "high": r.llen(settings.queue_high),
        "normal": r.llen(settings.queue_normal),
        "low": r.llen(settings.queue_low),
        "dlq": r.llen(settings.queue_dlq),
    }
