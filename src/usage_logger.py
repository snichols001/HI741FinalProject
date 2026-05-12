"""
HI 741 – Final Project
11 May 2026
Steven Nichols

usage_logger.py

UsageLogger class – appends login and action events to a CSV usage log.
"""

import csv
import os
from datetime import datetime


class UsageLogger:
    """Appends one row per user event to a CSV log file readable without technical tools."""

    _FIELDNAMES = ["timestamp", "username", "role", "action", "success"]

    def __init__(self, log_path: str):
        self.log_path = log_path
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Create the log file with a header row if it does not already exist."""
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
        if not os.path.exists(self.log_path):
            with open(self.log_path, "w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=self._FIELDNAMES).writeheader()

    def log_event(self, username: str, role: str, action: str, success: bool) -> None:
        """Append a single event row with the current timestamp."""
        with open(self.log_path, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=self._FIELDNAMES).writerow({
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "username":  username,
                "role":      role,
                "action":    action,
                "success":   success,
            })
