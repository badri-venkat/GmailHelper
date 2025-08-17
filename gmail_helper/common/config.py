import os
from pathlib import Path


class Config:
    """Centralized configuration (override via env)."""

    # Paths
    _COMMON_DIR = Path(__file__).resolve().parent        # .../gmail_helper/common
    PROJECT_ROOT = _COMMON_DIR.parent.parent             # repo root (one level above gmail_helper)

    # Database
    DB_PATH = os.getenv("DB_PATH", str(PROJECT_ROOT / "emails.db"))

    # OAuth files at repo root by default
    CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS", str(PROJECT_ROOT / ".credentials.json"))
    TOKEN_FILE = os.getenv("GMAIL_TOKEN", str(PROJECT_ROOT / ".token.json"))

    # Gmail scopes
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    # Rules
    RULES_FILE = os.getenv("RULES_FILE", str(PROJECT_ROOT / "rules.json"))

    # API
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))

    # Worker
    FETCH_BATCH_SIZE = int(os.getenv("FETCH_BATCH_SIZE", "25"))
    DEFAULT_LABELS = ["INBOX"]


# Global instance
config = Config()
