import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    PROJECT_NAME: str = "UGC Video Generator"
    API_V1_STR: str = "/api/v1"
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    ASSETS_DIR: Path = BASE_DIR / "assets"
    TEMP_DIR: Path = Path("/tmp/ugc-video")
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/ugc_generator"
    
    # AI & Extraction
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    JINA_API_KEY: Optional[str] = None

    # Licensed Media APIs
    GIPHY_API_KEY: Optional[str] = None
    PEXELS_API_KEY: Optional[str] = None
    EPIDEMIC_API_KEY: Optional[str] = None
    EPIDEMIC_TIER: str = "PROTOTYPE"  # "PROTOTYPE" or "PRODUCTION"
    EPIDEMIC_PARTNER_USER_ID: str = "ugc-generator-admin"
    
    # Video Generation & Safe Zones (1080x1920)
    VIDEO_DURATION: int = 7
    VIDEO_WIDTH: int = 1080
    VIDEO_HEIGHT: int = 1920
    VIDEO_FPS: int = 30
    SAFE_ZONE_TOP: int = 250
    SAFE_ZONE_BOTTOM: int = 1570
    
    model_config = SettingsConfigDict(
        env_file=(
            str(Path(__file__).resolve().parent.parent.parent.parent / ".env"),
            str(Path(__file__).resolve().parent.parent.parent / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sync_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url


settings = Settings()
