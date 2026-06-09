"""
Study Match AI — Configuration
================================
Central configuration module. Loads environment variables and defines
all constants used across the application.

All validation enums, algorithm weights, and system-level settings
are defined here to ensure a single source of truth.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# ──────────────────────────────────────────────
#  Environment
# ──────────────────────────────────────────────

# Load .env from the project root (one level up from backend/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = "llama-3.3-70b-versatile"
GROQ_MAX_TOKENS: int = 1024
GROQ_TEMPERATURE: float = 0.7


# ──────────────────────────────────────────────
#  Database paths
# ──────────────────────────────────────────────

DATABASE_DIR: Path = _PROJECT_ROOT / "database"
STUDENTS_DB_PATH: Path = DATABASE_DIR / "students_db.json"


# ──────────────────────────────────────────────
#  Valid profile enumerations (from TRD)
# ──────────────────────────────────────────────

VALID_STUDY_STYLES: list[str] = [
    "visual",
    "reading",
    "discussion",
    "practice-problems",
]

VALID_GOALS: list[str] = [
    "exam prep",
    "concept clarity",
    "project work",
    "competitive exam",
]

VALID_STUDY_TIMES: list[str] = [
    "morning",
    "afternoon",
    "evening",
    "night",
]

VALID_DAYS: list[str] = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

VALID_COMMUNICATION_PREFS: list[str] = [
    "online",
    "in-person",
    "both",
]

VALID_YEARS: list[str] = [
    "1st Year",
    "2nd Year",
    "3rd Year",
    "4th Year",
]


# ──────────────────────────────────────────────
#  Matching algorithm weights (from TRD)
# ──────────────────────────────────────────────

WEIGHTS: dict[str, float] = {
    "complementary_strengths": 0.40,
    "time_day_overlap":        0.30,
    "study_style":             0.15,
    "goal_match":              0.15,
}

# Study style compatibility matrix
# 1.0 = perfect match, 0.5 = partially compatible, 0.0 = incompatible
STYLE_COMPATIBILITY: dict[tuple[str, str], float] = {
    # Perfect matches (same style)
    ("visual", "visual"):                       1.0,
    ("reading", "reading"):                     1.0,
    ("discussion", "discussion"):               1.0,
    ("practice-problems", "practice-problems"): 1.0,
    # Partial compatibility
    ("discussion", "visual"):                   0.5,
    ("visual", "discussion"):                   0.5,
    ("discussion", "practice-problems"):        0.5,
    ("practice-problems", "discussion"):        0.5,
    ("reading", "visual"):                      0.5,
    ("visual", "reading"):                      0.5,
    # Low compatibility
    ("reading", "practice-problems"):           0.25,
    ("practice-problems", "reading"):           0.25,
    ("reading", "discussion"):                  0.25,
    ("discussion", "reading"):                  0.25,
    ("visual", "practice-problems"):            0.25,
    ("practice-problems", "visual"):            0.25,
}


# ──────────────────────────────────────────────
#  Registration flow — field collection order
# ──────────────────────────────────────────────

REGISTRATION_FIELDS: list[dict] = [
    {
        "key": "name",
        "prompt": "What's your name?",
        "type": "text",
        "validation": None,
    },
    {
        "key": "year",
        "prompt": "What year are you in?",
        "type": "choice",
        "validation": VALID_YEARS,
    },
    {
        "key": "branch",
        "prompt": "What's your branch/department?",
        "type": "text",
        "validation": None,
    },
    {
        "key": "subjects_strong_in",
        "prompt": "Which subjects are you strong in? (You can list multiple, separated by commas)",
        "type": "list",
        "validation": None,
    },
    {
        "key": "subjects_needing_help_in",
        "prompt": "Which subjects do you need help with?",
        "type": "list",
        "validation": None,
    },
    {
        "key": "study_style",
        "prompt": "What's your preferred study style?",
        "type": "choice",
        "validation": VALID_STUDY_STYLES,
    },
    {
        "key": "preferred_study_time",
        "prompt": "When do you prefer to study?",
        "type": "multi-choice",
        "validation": VALID_STUDY_TIMES,
    },
    {
        "key": "availability_days",
        "prompt": "Which days are you available?",
        "type": "multi-choice",
        "validation": VALID_DAYS,
    },
    {
        "key": "goal",
        "prompt": "What's your current study goal?",
        "type": "choice",
        "validation": VALID_GOALS,
    },
    {
        "key": "communication_preference",
        "prompt": "Do you prefer online, in-person, or both?",
        "type": "choice",
        "validation": VALID_COMMUNICATION_PREFS,
    },
]
