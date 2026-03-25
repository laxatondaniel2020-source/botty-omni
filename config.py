"""
config.py — Bot Configuration
==============================
Load sensitive settings from environment variables.
Never hardcode tokens or IDs directly in source code.

Setup:
    Copy .env.example to .env and fill in your values.
"""

import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file


def _require(key: str) -> str:
    """Fetch a required environment variable or raise a clear error."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: {key}\n"
            f"Please set it in your .env file."
        )
    return value


def _parse_admin_ids(raw: str) -> set[int]:
    """Parse a comma-separated string of Telegram user IDs into a set of ints."""
    try:
        return {int(uid.strip()) for uid in raw.split(",") if uid.strip()}
    except ValueError:
        raise EnvironmentError(
            "ADMIN_IDS must be a comma-separated list of integers.\n"
            "Example: ADMIN_IDS=123456789,987654321"
        )


# ── Bot Token from @BotFather ──────────────────────────────────────────────────
BOT_TOKEN: str = _require("BOT_TOKEN")

# ── Admin Telegram User IDs (can control the bot) ─────────────────────────────
ADMIN_IDS: set[int] = _parse_admin_ids(_require("ADMIN_IDS"))

# ── Target Chat ID where broadcasts are sent ──────────────────────────────────
# This can be a user ID, group ID, or channel ID (e.g., -100xxxxxxxxxx)
TARGET_CHAT_ID: int = int(_require("TARGET_CHAT_ID"))
