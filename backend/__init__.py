"""
Study Match AI — Backend Package
================================
Core logic layer: configuration, matching engine, and LLM orchestration.
"""

from backend.config import (
    VALID_STUDY_STYLES,
    VALID_GOALS,
    VALID_STUDY_TIMES,
    VALID_DAYS,
    VALID_COMMUNICATION_PREFS,
    WEIGHTS,
    GROQ_MODEL,
)
from backend.matching_engine import calculate_compatibility, find_matches, find_study_groups
from backend.llm_orchestrator import LLMOrchestrator

__all__ = [
    "VALID_STUDY_STYLES",
    "VALID_GOALS",
    "VALID_STUDY_TIMES",
    "VALID_DAYS",
    "VALID_COMMUNICATION_PREFS",
    "WEIGHTS",
    "GROQ_MODEL",
    "calculate_compatibility",
    "find_matches",
    "find_study_groups",
    "LLMOrchestrator",
]
