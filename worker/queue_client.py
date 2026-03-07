import json
from typing import Optional

import redis
from config import settings

QUEUE_KEYS = [settings.queue_high, settings.queue_normal, settings.queue_low]


def get_redis():
    return redis.from_url(settings.redis_url, decode_responses=True)


def dequeue(block_timeout: int = 0) -> Optional[dict]:
    r = get_redis()
    result = r.brpop(QUEUE_KEYS, timeout=block_timeout)
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
