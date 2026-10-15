from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_db_url: str = ""
    supabase_url: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_URL"),
    )
    supabase_publishable_key: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_PUBLISHABLE_KEY", "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY"),
    )
    supabase_secret_key: str = ""
    frontend_origin: str = ""
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080"
    max_upload_bytes: int = 5_000_000
    forecast_async: bool = True
    tabpfn_enabled: bool = True
    tabpfn_model_version: str = "v2"
    tabpfn_api_key: str = ""
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    llm_model: str = "gemma-4-26b-a4b-it"
    llm_api_key: str = ""
    llm_timeout: float = 240
    llm_max_rpm: int = 10
    llm_max_wait: float = 45
    llm_thinking_level: str = "minimal"
    llm_max_per_day: int = 300
    submit_limit: int = 8
    sample_csv: str = str(ROOT / "samples" / "kirana_billing.csv")

    @property
    def database_url(self) -> str:
        raw = self.supabase_db_url.strip()
        if not raw:
            return "sqlite:///./data/dukaandost.db"
        if raw.startswith("postgres://"):
            return "postgresql+psycopg://" + raw[len("postgres://") :]
        if raw.startswith("postgresql://") and not raw.startswith("postgresql+"):
            return "postgresql+psycopg://" + raw[len("postgresql://") :]
        return raw

    @property
    def data_api_key(self) -> str:
        secret = self.supabase_secret_key.strip()
        if secret:
            return secret
        return self.supabase_publishable_key.strip()

    @property
    def uses_data_api(self) -> bool:
        if self.supabase_db_url.strip().startswith(("postgres://", "postgresql://", "postgresql+")):
            return False
        return bool(self.supabase_url.strip() and self.data_api_key)

    @property
    def database_label(self) -> str:
        if self.uses_data_api or self.database_url.startswith("postgresql"):
            return "supabase"
        return "sqlite"

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [item.strip() for item in self.cors_origins.split(",") if item.strip()]
        extra = self.frontend_origin.strip().rstrip("/")
        if extra and extra not in origins:
            origins.append(extra)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
