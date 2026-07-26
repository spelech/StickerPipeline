import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

class Settings(BaseSettings):
    sticker_storage_dir: str = os.getenv("STICKER_STORAGE_DIR", "./storage")
    upstream_llm_url: str = os.getenv("UPSTREAM_LLM_URL", "http://litellm:4000/v1")
    border_offset_px: int = int(os.getenv("BORDER_OFFSET_PX", "20"))
    target_dpi: int = int(os.getenv("TARGET_DPI", "300"))
    port: int = int(os.getenv("PORT", "8460"))
    auto_sheet_build_threshold: int = int(os.getenv("AUTO_SHEET_BUILD_THRESHOLD", "6"))

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
