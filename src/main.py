"""
HI 741 – Final Project
11 May 2026
Steven Nichols

main.py

Entry point: loads all clinical data, initializes the usage logger, and launches the UI.

Run with:
    python src/main.py
"""

import os

from data_store import DataStore
from usage_logger import UsageLogger
from app import App

# Resolve paths relative to this file so the program works from any working directory
_SRC_DIR   = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR  = os.path.dirname(_SRC_DIR)
DATA_DIR   = os.path.join(_ROOT_DIR, "data")
OUTPUT_DIR = os.path.join(_ROOT_DIR, "output")


def main() -> None:
    """Load data, initialize the logger, and launch the UI."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    data_store = DataStore(DATA_DIR)
    data_store.load()

    logger = UsageLogger(os.path.join(OUTPUT_DIR, "usage_log.csv"))

    app = App(data_store, logger, DATA_DIR, OUTPUT_DIR)
    app.mainloop()


if __name__ == "__main__":
    main()
