from typing import Optional
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    # Application
    PROJECT_NAME: str = "WhatsApp Weekly PDF Report Automation System"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    PUBLIC_BASE_URL: str = "http://localhost:8000"

    # Database
    DATABASE_URL: str = "sqlite:///./whatsapp_reports.db"

    # Persistent Storage
    STORAGE_DIR: str = "storage/reports"

    # Scheduling
    TIMEZONE: str = "Asia/Kolkata"
    SCHEDULE_DAY_OF_WEEK: str = "mon"
    SCHEDULE_HOUR: int = 9
    SCHEDULE_MINUTE: int = 0

    # Meta WhatsApp Cloud API (Official Graph API)
    WHATSAPP_API_URL: str = "https://graph.facebook.com"
    WHATSAPP_API_VERSION: str = "v21.0"
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_BUSINESS_ACCOUNT_ID: str = ""
    META_APP_SECRET: str = ""

    # Webhook Security
    WEBHOOK_VERIFY_TOKEN: str = "whatsapp_report_verify_token_secure"

    # Template Messaging
    WHATSAPP_TEMPLATE_NAME: str = "weekly_report_document"
    WHATSAPP_TEMPLATE_LANG: str = "en_US"

    # Reliability
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_SECONDS: float = 2.0
    API_TIMEOUT: int = 30
    LOG_LEVEL: str = "INFO"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if isinstance(v, str):
            # Render / Railway backward compatibility (postgres:// -> postgresql://)
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql://", 1)
        return v

    @property
    def is_whatsapp_configured(self) -> bool:
        """Check if production Meta credentials have been supplied."""
        placeholder_tokens = {"", "mock_whatsapp_access_token", "your_whatsapp_api_token", "your_meta_system_user_permanent_access_token"}
        placeholder_ids = {"", "mock_phone_number_id", "your_phone_number_id", "your_meta_phone_number_id"}
        return (
            bool(self.WHATSAPP_ACCESS_TOKEN)
            and self.WHATSAPP_ACCESS_TOKEN not in placeholder_tokens
            and bool(self.WHATSAPP_PHONE_NUMBER_ID)
            and self.WHATSAPP_PHONE_NUMBER_ID not in placeholder_ids
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
