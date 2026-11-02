from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GitAuto AI"
    app_env: str = "development"
    app_secret_key: str = Field(default="", repr=False)
    database_url: str = "sqlite:///./gitauto.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_task_always_eager: bool = False
    github_client_id: str = Field(default="", repr=False)
    github_client_secret: str = Field(default="", repr=False)
    github_redirect_uri: str = "http://localhost:8000/api/v1/auth/github/callback"
    session_cookie_name: str = "gitauto_session"
    oauth_state_cookie_name: str = "gitauto_oauth_state"
    session_ttl_seconds: int = 60 * 60 * 24 * 7
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"
    log_level: str = "INFO"
    openai_api_key: str = Field(default="", repr=False)
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: float = 30.0
    openai_max_output_tokens: int = 8_000
    openai_max_input_chars: int = 100_000
    analysis_max_files: int = 200
    analysis_max_file_size_bytes: int = 200_000
    analysis_max_context_chars: int = 120_000
    workspace_root: str = ".gitauto-workspaces"
    workspace_max_files: int = 500
    workspace_max_size_bytes: int = 10_000_000
    generation_max_duration_seconds: int = 120
    sandbox_image: str = "gitauto-ai-sandbox:local"
    sandbox_timeout_seconds: int = 120
    sandbox_memory_limit: str = "512m"
    sandbox_cpu_limit: float = 1.0
    sandbox_pids_limit: int = 128
    sandbox_output_limit_bytes: int = 100_000
    sandbox_max_concurrent_runs: int = 2
    release_lease_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        origins = {
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        }
        for origin in self.frontend_url.split(","):
            if origin.strip():
                origins.add(origin.strip())
        return list(origins)

    @property
    def github_configured(self) -> bool:
        return bool(self.github_client_id and self.github_client_secret)

    @property
    def secure_cookies(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
