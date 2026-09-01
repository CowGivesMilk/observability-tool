from pydantic_settings import BaseSettings
class Settings(BaseSettings):
    db_url: str = "postgresql://obs:obs@localhost:5432/observability"
    redis_host: str = "localhost"
    redis_port: int = 6379

    class Config:
        env_file = ".env"

settings = Settings()