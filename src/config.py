"""
Centralized Configuration and Environment Settings for StudyVault.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = Path(__file__).resolve().parent

# Application Info
APP_NAME = "StudyVault"
APP_TITLE = "StudyVault API"
APP_DESCRIPTION = "Course Notes Hub and AI-Powered Quiz & Flashcard Study Engine"
APP_VERSION = "1.1.0"

# Database Configuration
DEFAULT_DB_PATH = str(BASE_DIR / "studyvault.db")
DB_PATH = os.getenv("STUDYVAULT_DB_PATH", DEFAULT_DB_PATH)

# Supported Course Badge Colors
COURSE_COLORS = ["indigo", "emerald", "amber", "rose", "purple", "sky", "teal", "orange"]

# Pagination & Defaults
DEFAULT_PAGE_SIZE = 50
MAX_SEARCH_RESULTS = 100
MAX_FLASHCARDS_PER_NOTE = 20
MAX_QUIZ_QUESTIONS = 10
