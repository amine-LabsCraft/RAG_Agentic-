from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import json


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # LangSmith
    langsmith_api_key: str = ""
    langsmith_project: str = "rag-masterclass"

    # Encryption
    settings_encryption_key: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        # Accept JSON list '["http://..."]' or comma-separated string
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return ["http://localhost:5173"]
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(o).strip() for o in parsed if str(o).strip()]
            except (json.JSONDecodeError, ValueError):
                pass
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"
        protected_namespaces = ("model_",)


@lru_cache
def get_settings() -> Settings:
    return Settings()
