from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="PDF_PARSER_", env_file=".env", extra="ignore")

    app_name: str = "Bank Statement PDF Parser"
    debug: bool = False
    parse_debug_logging: bool = False
    upload_dir: Path = Path("data/uploads")
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB
    allowed_content_types: tuple[str, ...] = ("application/pdf", "application/x-pdf")


settings = Settings()
