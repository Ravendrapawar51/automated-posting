from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration and credentials loaded from environment variables."""

    # Server Settings
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 4000
    DEBUG: bool = False

    # Simulation / Mock Mode
    # If True, platforms return simulated responses instead of attempting live external network calls
    MOCK_MODE: bool = False

    # 1. Telegram Platform Configuration
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    # 2. Discord Platform Configuration
    DISCORD_WEBHOOK_URL: Optional[str] = None

    # 3. Slack Platform Configuration
    SLACK_WEBHOOK_URL: Optional[str] = None
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_CHANNEL_ID: Optional[str] = None

    # 4. Mastodon Platform Configuration
    MASTODON_INSTANCE_URL: str = "https://mastodon.social"
    MASTODON_ACCESS_TOKEN: Optional[str] = None

    # 5. GitHub Platform Configuration
    GITHUB_ACCESS_TOKEN: Optional[str] = None
    GITHUB_REPO_OWNER: Optional[str] = None
    GITHUB_REPO_NAME: Optional[str] = None

    # 6. Dev.to Platform Configuration (Bonus)
    DEVTO_API_KEY: Optional[str] = None
    DEVTO_ORGANIZATION_ID: Optional[int] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# Global settings singleton
settings = Settings()
