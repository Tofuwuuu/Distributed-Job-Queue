"""
Registry of job type -> handler. Add your task logic here.
Each handler receives (payload: dict) and returns result dict or raises.
"""
from datetime import datetime
import random
import time

JOB_HANDLERS = {}


def register(job_type: str):
    def decorator(fn):
        JOB_HANDLERS[job_type] = fn
        return fn
    return decorator


@register("echo")
def handle_echo(payload: dict) -> dict:
    return {"echo": payload.get("message", ""), "at": datetime.utcnow().isoformat()}


@register("sleep")
def handle_sleep(payload: dict) -> dict:
    secs = min(float(payload.get("seconds", 1)), 10)
    time.sleep(secs)
    return {"slept": secs}


@register("random_fail")
def handle_random_fail(payload: dict) -> dict:
    """Example job that fails sometimes (for testing retry/DLQ)."""
    if random.random() < 0.6:
        raise RuntimeError("Simulated random failure")
    return {"ok": True}


def run_job(job_type: str, payload: dict) -> dict:
    handler = JOB_HANDLERS.get(job_type)
    if not handler:
        raise ValueError(f"Unknown job type: {job_type}")
    return handler(payload)
