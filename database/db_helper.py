"""
Study Match AI — Database Helper
=================================
Thread-safe CRUD operations for the local JSON student profile store.

All reads and writes go through this module to ensure data consistency,
automatic ID generation, and duplicate detection.
"""

import json
import os
import threading
from typing import Optional


# ──────────────────────────────────────────────
#  Path resolution
# ──────────────────────────────────────────────

_DB_DIR = os.path.dirname(os.path.abspath(__file__))
_DB_PATH = os.path.join(_DB_DIR, "students_db.json")

# Module-level lock for thread-safe file operations
_file_lock = threading.Lock()


# ──────────────────────────────────────────────
#  Read operations
# ──────────────────────────────────────────────

def load_students() -> list[dict]:
    """
    Load all student profiles from the JSON database.

    Returns:
        A list of student profile dictionaries. Returns an empty list
        if the file doesn't exist or is corrupted.
    """
    with _file_lock:
        if not os.path.exists(_DB_PATH):
            return []
        try:
            with open(_DB_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return []
            return data
        except (json.JSONDecodeError, IOError):
            return []


def find_student_by_id(student_id: str) -> Optional[dict]:
    """
    Find a student profile by their unique student_id.

    Args:
        student_id: The ID to search for (e.g., "STU001").

    Returns:
        The matching student dict, or None if not found.
    """
    students = load_students()
    for student in students:
        if student.get("student_id", "").upper() == student_id.upper():
            return student
    return None


def find_student_by_name(name: str) -> Optional[dict]:
    """
    Find a student profile by name (case-insensitive).

    Used for duplicate detection during registration.

    Args:
        name: The student name to search for.

    Returns:
        The first matching student dict, or None if not found.
    """
    students = load_students()
    name_lower = name.strip().lower()
    for student in students:
        if student.get("name", "").strip().lower() == name_lower:
            return student
    return None


def get_next_student_id() -> str:
    """
    Generate the next sequential student ID.

    Scans existing IDs and returns the next one in the STU00X format.
    Handles gaps in numbering gracefully.

    Returns:
        A string like "STU009", "STU010", etc.
    """
    students = load_students()
    if not students:
        return "STU001"

    max_num = 0
    for student in students:
        sid = student.get("student_id", "")
        if sid.startswith("STU"):
            try:
                num = int(sid[3:])
                max_num = max(max_num, num)
            except ValueError:
                continue

    return f"STU{max_num + 1:03d}"


# ──────────────────────────────────────────────
#  Write operations
# ──────────────────────────────────────────────

def _write_students(students: list[dict]) -> None:
    """
    Atomically write the full student list to disk.

    Writes to a temporary file first, then replaces the original
    to prevent data corruption on crash.
    """
    tmp_path = _DB_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(students, f, indent=4, ensure_ascii=False)
    os.replace(tmp_path, _DB_PATH)


def save_student(profile: dict) -> dict:
    """
    Save a student profile — creates new or updates existing.

    If a profile with the same student_id already exists, it is replaced.
    Otherwise, the new profile is appended.

    Args:
        profile: A complete student profile dict. Must contain 'student_id'.

    Returns:
        The saved profile dict (with any auto-generated fields).

    Raises:
        ValueError: If the profile is missing required fields.
    """
    _validate_profile(profile)

    with _file_lock:
        students = []
        if os.path.exists(_DB_PATH):
            try:
                with open(_DB_PATH, "r", encoding="utf-8") as f:
                    students = json.load(f)
            except (json.JSONDecodeError, IOError):
                students = []

        # Check for existing profile with same ID → update
        updated = False
        for i, existing in enumerate(students):
            if existing.get("student_id") == profile["student_id"]:
                students[i] = profile
                updated = True
                break

        if not updated:
            students.append(profile)

        _write_students(students)

    return profile


def delete_student(student_id: str) -> bool:
    """
    Remove a student profile by ID.

    Args:
        student_id: The student ID to delete.

    Returns:
        True if a profile was deleted, False if not found.
    """
    with _file_lock:
        students = []
        if os.path.exists(_DB_PATH):
            try:
                with open(_DB_PATH, "r", encoding="utf-8") as f:
                    students = json.load(f)
            except (json.JSONDecodeError, IOError):
                return False

        original_count = len(students)
        students = [s for s in students if s.get("student_id") != student_id]

        if len(students) == original_count:
            return False

        _write_students(students)
        return True


# ──────────────────────────────────────────────
#  Validation
# ──────────────────────────────────────────────

_REQUIRED_FIELDS = [
    "student_id",
    "name",
    "year",
    "branch",
    "subjects_needing_help_in",
    "subjects_strong_in",
    "study_style",
    "preferred_study_time",
    "availability_days",
    "goal",
    "communication_preference",
]


def _validate_profile(profile: dict) -> None:
    """
    Validate that a student profile has all required fields.

    Raises:
        ValueError: With details about which fields are missing.
    """
    if not isinstance(profile, dict):
        raise ValueError("Profile must be a dictionary.")

    missing = [field for field in _REQUIRED_FIELDS if field not in profile]
    if missing:
        raise ValueError(
            f"Profile is missing required fields: {', '.join(missing)}"
        )

    # Validate list fields are actually lists
    list_fields = [
        "subjects_needing_help_in",
        "subjects_strong_in",
        "preferred_study_time",
        "availability_days",
    ]
    for field in list_fields:
        if not isinstance(profile.get(field), list):
            raise ValueError(f"Field '{field}' must be a list.")

    # Validate non-empty strings
    string_fields = ["student_id", "name", "year", "branch", "study_style", "goal", "communication_preference"]
    for field in string_fields:
        val = profile.get(field)
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"Field '{field}' must be a non-empty string.")
