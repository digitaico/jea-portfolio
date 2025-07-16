from functools import lru_cache
from typing import Optional
from pydantic import BaseSettings, PostgresDsn, validator


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    
    # PostgreSQL settings
    postgres_server: str = "localhost"
    postgres_user: str = "postgres"
    postgres_password: str = "password"
    postgres_db: str = "running_metrics"
    postgres_port: int = 5432
    
    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    # Database URL
    database_url: Optional[PostgresDsn] = None
    
    @validator("database_url", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("postgres_user"),
            password=values.get("postgres_password"),
            host=values.get("postgres_server"),
            port=str(values.get("postgres_port")),
            path=f"/{values.get('postgres_db') or ''}",
        )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()