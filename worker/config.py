from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/jobqueue"
    max_retries: int = 3
    queue_high: str = "queue:high"
    queue_normal: str = "queue:normal"
    queue_low: str = "queue:low"
    queue_dlq: str = "queue:dlq"

    class Config:
        env_file = ".env"
        env_prefix = "JOBQUEUE_"


settings = Settings()
