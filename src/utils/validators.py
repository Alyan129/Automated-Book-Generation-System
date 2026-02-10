"""
Input validation utilities.
"""
from typing import Any, Dict
from src.models.schemas import StatusEnum


def validate_status(status: str) -> bool:
    """Validate status field"""
    try:
        StatusEnum(status)
        return True
    except ValueError:
        return False


def validate_book_input(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate book input data"""
    if not data.get('title'):
        return False, "Title is required"
    
    if not data.get('notes_on_outline_before'):
        return False, "notes_on_outline_before is required before outline generation"
    
    return True, "Valid"


def should_proceed_with_outline(status_outline_notes: str) -> bool:
    """Check if outline generation should proceed"""
    return status_outline_notes in ['no_notes_needed', 'no']


def should_wait_for_notes(status: str) -> bool:
    """Check if system should wait for notes"""
    return status == 'yes'


def should_proceed_with_chapter(chapter_notes_status: str) -> bool:
    """Check if chapter generation should proceed"""
    return chapter_notes_status in ['no_notes_needed', 'no']
