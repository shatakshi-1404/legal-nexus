from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://legalnexus:legalnexus@localhost:5432/legalnexus"
    checkpoint_dsn: str = "postgresql://legalnexus:legalnexus@localhost:5432/legalnexus"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    access_token_minutes: int = 720
    admin_emails: list[str] = []
    cors_origins: list[str] = ["http://localhost:5173"]
    auto_create_tables: bool = True  # dev convenience; use Alembic in production

    # LLM provider abstraction: "groq" or "openai_compatible"
    llm_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    openai_base_url: str = ""
    openai_api_key: str = ""
    openai_model: str = ""

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    min_rerank_score: float = -3.0  # evidence sufficiency threshold; tune with evaluation/

    storage_dir: str = "./storage"
    max_upload_mb: int = 20
    celery_eager: bool = False  # True = run tasks inline (no Redis/worker needed)
    require_approval: bool = False  # human approval before the report is finalized
    max_clauses_per_analysis: int = 40

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
