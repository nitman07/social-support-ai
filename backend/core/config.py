from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, field_validator
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Social Support AI"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_log_level: str = "DEBUG"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_cors_origins: str = "http://localhost:8501,http://localhost:8000"

    # JWT
    jwt_secret_key: str = "change-this-to-a-secure-random-key-in-production"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"

    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "social_support"
    postgres_user: str = "app_user"
    postgres_password: str = "app_password"
    postgres_pool_size: int = 10
    postgres_max_overflow: int = 20

    @property
    def postgres_dsn(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    @property
    def postgres_sync_dsn(self) -> str:
        return str(
            PostgresDsn.build(
                scheme="postgresql",
                username=self.postgres_user,
                password=self.postgres_password,
                host=self.postgres_host,
                port=self.postgres_port,
                path=self.postgres_db,
            )
        )

    # MongoDB
    mongodb_host: str = "localhost"
    mongodb_port: int = 27017
    mongodb_db: str = "social_support"
    mongodb_user: str = "app_user"
    mongodb_password: str = "app_password"

    @property
    def mongodb_dsn(self) -> str:
        return (
            f"mongodb://{self.mongodb_user}:{self.mongodb_password}"
            f"@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_db}"
            f"?authSource=admin"
        )

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_prefer_grpc: bool = False

    @property
    def qdrant_url(self) -> str:
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    # Neo4j
    neo4j_host: str = "localhost"
    neo4j_port: int = 7687
    neo4j_user: str = "neo4j"
    neo4j_password: str = "app_password"
    neo4j_database: str = "neo4j"

    @property
    def neo4j_dsn(self) -> str:
        return f"bolt://{self.neo4j_host}:{self.neo4j_port}"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    @property
    def redis_dsn(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_llm_model: str = "mistral:7b"
    ollama_embedding_model: str = "nomic-embed-text"
    ollama_vision_model: str = "qwen2.5-vl:7b"
    ollama_timeout: int = 120

    # Langfuse
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    # ML
    ml_model_path: str = "data/models/eligibility_rf.pkl"
    ml_feature_config_path: str = "configs/features.yaml"
    ml_confidence_threshold: float = 0.7
    ml_auto_approve_threshold: float = 0.85
    ml_auto_decline_threshold: float = 0.3

    # Workflow
    workflow_max_retries: int = 3
    workflow_ocr_confidence_min: float = 0.6
    workflow_hitl_inconsistency_threshold: int = 3

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.api_cors_origins.split(",")]

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        app_env = info.data.get("app_env")
        if v == "change-this-to-a-secure-random-key-in-production" and app_env == "production":
            raise ValueError("JWT_SECRET_KEY must be changed in production")
        return v


settings = Settings()
