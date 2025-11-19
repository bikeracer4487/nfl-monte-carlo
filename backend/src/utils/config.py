"""
Configuration management for the NFL Monte Carlo simulation application.

Loads and manages application configuration from environment variables.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .logger import get_log_level


class Config:
    """Application configuration manager."""

    def __init__(self):
        """Initialize configuration with default values."""
        # API Configuration
        self.ODDS_API_KEY: str = ""
        self.ODDS_API_BASE_URL: str = "https://api.the-odds-api.com/v4"
        self.ESPN_API_BASE_URL: str = "https://site.api.espn.com/apis/site/v2"
        self.ESPN_CORE_API_BASE_URL: str = "https://sports.core.api.espn.com/v2"

        # Cache Configuration
        self.CACHE_DIRECTORY: Path = Path("data")
        self.CACHE_MAX_AGE_SCHEDULE: int = 86400  # 24 hours
        self.CACHE_MAX_AGE_RESULTS: int = 3600  # 1 hour
        self.CACHE_MAX_AGE_ODDS: int = 3600  # 1 hour

        # Logging
        self.LOG_LEVEL: str = "INFO"
        self.LOG_FILE: str = "nfl_monte_carlo.log"

        # Development
        self.DEVELOPMENT_MODE: bool = False
        self.MOCK_API_CALLS: bool = False

    @classmethod
    def load(cls, env_file: Optional[str] = None) -> "Config":
        """
        Load configuration from environment variables.

        Args:
            env_file: Optional path to .env file (default: .env in current directory)

        Returns:
            Config instance with loaded values
        """
        # Load .env file if it exists
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()  # Loads .env from current directory if exists

        config = cls()

        # API Configuration
        config.ODDS_API_KEY = os.getenv("ODDS_API_KEY", config.ODDS_API_KEY)
        config.ODDS_API_BASE_URL = os.getenv(
            "ODDS_API_BASE_URL", config.ODDS_API_BASE_URL
        )
        config.ESPN_API_BASE_URL = os.getenv(
            "ESPN_API_BASE_URL", config.ESPN_API_BASE_URL
        )
        config.ESPN_CORE_API_BASE_URL = os.getenv(
            "ESPN_CORE_API_BASE_URL", config.ESPN_CORE_API_BASE_URL
        )

        # Cache Configuration
        cache_dir = os.getenv("CACHE_DIRECTORY", str(config.CACHE_DIRECTORY))
        config.CACHE_DIRECTORY = Path(cache_dir)

        config.CACHE_MAX_AGE_SCHEDULE = int(
            os.getenv("CACHE_MAX_AGE_SCHEDULE", config.CACHE_MAX_AGE_SCHEDULE)
        )
        config.CACHE_MAX_AGE_RESULTS = int(
            os.getenv("CACHE_MAX_AGE_RESULTS", config.CACHE_MAX_AGE_RESULTS)
        )
        config.CACHE_MAX_AGE_ODDS = int(
            os.getenv("CACHE_MAX_AGE_ODDS", config.CACHE_MAX_AGE_ODDS)
        )

        # Logging
        config.LOG_LEVEL = os.getenv("LOG_LEVEL", config.LOG_LEVEL)
        config.LOG_FILE = os.getenv("LOG_FILE", config.LOG_FILE)

        # Development
        config.DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        config.MOCK_API_CALLS = os.getenv("MOCK_API_CALLS", "false").lower() in (
            "true",
            "1",
            "yes",
        )

        return config

    def get_log_level_int(self) -> int:
        """
        Get logging level as integer.

        Returns:
            Logging level constant (e.g., logging.INFO)
        """
        return get_log_level(self.LOG_LEVEL)

    def validate(self) -> list[str]:
        """
        Validate configuration values.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate cache directory is writable
        try:
            self.CACHE_DIRECTORY.mkdir(parents=True, exist_ok=True)
            test_file = self.CACHE_DIRECTORY / ".test_write"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            errors.append(f"Cache directory not writable: {e}")

        # Validate cache max age values
        if self.CACHE_MAX_AGE_SCHEDULE <= 0:
            errors.append("CACHE_MAX_AGE_SCHEDULE must be positive")
        if self.CACHE_MAX_AGE_RESULTS <= 0:
            errors.append("CACHE_MAX_AGE_RESULTS must be positive")
        if self.CACHE_MAX_AGE_ODDS <= 0:
            errors.append("CACHE_MAX_AGE_ODDS must be positive")

        # Validate log level
        try:
            get_log_level(self.LOG_LEVEL)
        except ValueError as e:
            errors.append(str(e))

        return errors

    def __repr__(self) -> str:
        """Return string representation of configuration."""
        return (
            f"Config("
            f"ODDS_API_KEY={'***' if self.ODDS_API_KEY else 'Not Set'}, "
            f"CACHE_DIRECTORY={self.CACHE_DIRECTORY}, "
            f"LOG_LEVEL={self.LOG_LEVEL}, "
            f"DEVELOPMENT_MODE={self.DEVELOPMENT_MODE}"
            f")"
        )
