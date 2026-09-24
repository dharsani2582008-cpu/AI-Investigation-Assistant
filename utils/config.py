"""
Central configuration for the AI Investigation Assistant.

Keep this file as the single source of truth for constants so later
phases (upload validation, NLP, AI assistant, etc.) can import from
here instead of hardcoding values in multiple places.
"""

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
SAMPLE_DIR = os.path.join(DATA_DIR, "sample")

DB_PATH = os.path.join(BASE_DIR, "database", "investigation.db")

# ---------------------------------------------------------------------------
# Upload validation (Feature 1)
# ---------------------------------------------------------------------------
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".json", ".pdf"}

# 50 MB max file size for the MVP. Adjust if demo evidence is larger.
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# ---------------------------------------------------------------------------
# App metadata
# ---------------------------------------------------------------------------
APP_TITLE = "AI Investigation Assistant"
APP_SUBTITLE = "Digital Evidence Analysis Platform (Academic Prototype)"

# This project is an academic prototype only.
DISCLAIMER = (
    "This is an academic prototype for evidence analysis assistance. "
    "It is NOT a certified forensic tool and its output is NOT legally "
    "admissible. All AI-generated findings require investigator "
    "verification."
)

# ---------------------------------------------------------------------------
# Ensure required folders exist at startup
# ---------------------------------------------------------------------------
def ensure_data_dirs():
    for path in (UPLOADS_DIR, PROCESSED_DIR, SAMPLE_DIR):
        os.makedirs(path, exist_ok=True)
