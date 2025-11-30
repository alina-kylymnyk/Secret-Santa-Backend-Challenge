"""Configuration settings for Secret Santa Bot"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
DATA_DIR = PROJECT_ROOT / "data"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be configured via .env file or environment variables.
    """
    
    # Bot settings
    bot_token: str = Field(
        ...,
        description="Telegram Bot API token from @BotFather"
    )
    
    # Database settings
    database_url: str = Field(
        default=f"sqlite+aiosqlite:///{DATA_DIR / 'bot.db'}",
        description="Database connection URL"
    )
    
    # Auto-purge settings
    enable_auto_purge: bool = Field(
        default=True,
        description="Enable automatic purging of expired games"
    )
    
    auto_purge_days: int = Field(
        default=30,
        description="Days until automatic game purge"
    )
    
    # Logging settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode (verbose logging)"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # Application settings
    app_name: str = Field(
        default="Secret Santa Bot",
        description="Application name"
    )
    
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    # Admin settings (optional)
    admin_ids: list[int] = Field(
        default_factory=list,
        description="List of admin user IDs (comma-separated in env)"
    )
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, v: str) -> str:
        """Validate that bot token is not empty"""
        if not v or v == "your_bot_token_here":
            raise ValueError(
                "BOT_TOKEN must be set. Get it from @BotFather on Telegram"
            )
        return v
    
    @field_validator("auto_purge_days")
    @classmethod
    def validate_auto_purge_days(cls, v: int) -> int:
        """Validate auto-purge days is positive"""
        if v < 1:
            raise ValueError("AUTO_PURGE_DAYS must be at least 1")
        if v > 365:
            raise ValueError("AUTO_PURGE_DAYS must be at most 365")
        return v
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {', '.join(valid_levels)}")
        return v_upper
    
    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, v) -> list[int]:
        """Parse admin IDs from string or list"""
        if isinstance(v, str):
            if not v:
                return []
            # Split by comma and convert to integers
            return [int(id.strip()) for id in v.split(",") if id.strip()]
        return v or []
    
    def is_admin(self, user_id: int) -> bool:
        """
        Check if user ID is in admin list.
        
        Args:
            user_id: Telegram user ID to check
        
        Returns:
            True if user is admin, False otherwise
        """
        return user_id in self.admin_ids
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.debug
    
    @property
    def database_type(self) -> str:
        """Get database type from URL"""
        if "sqlite" in self.database_url:
            return "sqlite"
        elif "postgresql" in self.database_url:
            return "postgresql"
        else:
            return "unknown"


# Create global settings instance
try:
    settings = Settings()
except Exception as e:
    print(f"Error loading settings: {e}")
    print("\nPlease ensure you have a .env file with BOT_TOKEN set.")
    print("Example .env file:")
    print("BOT_TOKEN=your_token_here")
    print("DATABASE_URL=sqlite+aiosqlite:///./data/bot.db")
    raise


def print_settings_info():
    """Print current settings (for debugging)"""
    print("=" * 60)
    print("Secret Santa Bot - Configuration")
    print("=" * 60)
    print(f"App Name: {settings.app_name}")
    print(f"Version: {settings.app_version}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Log Level: {settings.log_level}")
    print(f"Database: {settings.database_type}")
    print(f"Auto-purge: {'Enabled' if settings.enable_auto_purge else 'Disabled'}")
    print(f"Auto-purge days: {settings.auto_purge_days}")
    print(f"Admin users: {len(settings.admin_ids)}")
    print("=" * 60)


if __name__ == "__main__":
    # Test settings loading
    print_settings_info()