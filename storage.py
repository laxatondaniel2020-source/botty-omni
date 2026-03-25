"""
storage.py — Persistent Settings Storage
==========================================
Saves and loads bot configuration (message + schedule) to a local
JSON file so settings survive bot restarts.

For production use, this can be swapped for SQLite, Redis, or any
other database by implementing the same load() / save() interface.
"""

import json
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Default path for the settings file (created automatically if missing)
DEFAULT_PATH = os.path.join(os.path.dirname(__file__), "data", "settings.json")

# Schema of default settings
DEFAULT_SETTINGS: dict[str, Any] = {
    "message": None,           # The broadcast message text
    "schedule_type": None,     # "interval" or "daily"
    "interval_seconds": None,  # For interval schedules
    "daily_time": None,        # "HH:MM" for daily schedules
    "schedule_label": None,    # Human-readable description
    "active": False,           # Whether a schedule is currently active
}


class Storage:
    """
    Simple JSON-backed key-value store for bot settings.

    Usage:
        storage = Storage()
        settings = storage.load()
        settings["message"] = "Hello!"
        storage.save(settings)
    """

    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        self._ensure_file()

    def _ensure_file(self):
        """Create the data directory and settings file if they don't exist."""
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self._write(DEFAULT_SETTINGS.copy())
            logger.info(f"Created new settings file at: {self.path}")

    def _write(self, data: dict):
        """Write data dict to the JSON file atomically."""
        tmp_path = self.path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self.path)  # Atomic rename

    def load(self) -> dict[str, Any]:
        """
        Load settings from disk.
        Returns default settings merged with any saved values.
        """
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # Merge with defaults to handle new keys added in updates
            return {**DEFAULT_SETTINGS, **saved}
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Failed to load settings: {e}. Using defaults.")
            return DEFAULT_SETTINGS.copy()

    def save(self, data: dict[str, Any]) -> None:
        """
        Persist settings to disk.
        Only known keys are saved to avoid bloating the file.
        """
        clean = {k: data.get(k) for k in DEFAULT_SETTINGS}
        try:
            self._write(clean)
            logger.debug("Settings saved successfully.")
        except OSError as e:
            logger.error(f"Failed to save settings: {e}")

    def reset(self) -> None:
        """Reset all settings to defaults (useful for testing)."""
        self._write(DEFAULT_SETTINGS.copy())
        logger.info("Settings reset to defaults.")
