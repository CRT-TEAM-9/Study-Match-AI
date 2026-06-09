"""
Study Match AI — Database Package
===================================
Local JSON-based data layer with CRUD operations for student profiles.
"""

from database.db_helper import (
    load_students,
    save_student,
    find_student_by_name,
    find_student_by_id,
    get_next_student_id,
    delete_student,
)

__all__ = [
    "load_students",
    "save_student",
    "find_student_by_name",
    "find_student_by_id",
    "get_next_student_id",
    "delete_student",
]
