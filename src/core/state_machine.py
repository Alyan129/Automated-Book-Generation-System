"""
State Machine for workflow management.
Manages the state transitions and gating logic for book generation.
"""
from enum import Enum
from typing import Optional, Tuple
from uuid import UUID
from src.models.schemas import Book, BookOutputStatus, StatusEnum
from src.services.database_service import DatabaseService
from src.utils.logger import logger
from src.utils.validators import should_proceed_with_outline, should_wait_for_notes


class WorkflowStage(str, Enum):
    """Workflow stages"""
    INPUT = "input"
    OUTLINE_GENERATION = "outline_generation"
    OUTLINE_REVIEW = "outline_review"
    CHAPTER_GENERATION = "chapter_generation"
    CHAPTER_REVIEW = "chapter_review"
    FINAL_COMPILATION = "final_compilation"
    COMPLETED = "completed"


class StateMachine:
    """State machine for managing workflow stages"""
    
    def __init__(self, db_service: DatabaseService):
        """
        Initialize state machine.
        
        Args:
            db_service: Database service instance
        """
        self.db = db_service
    
    def can_generate_outline(self, book: Book) -> Tuple[bool, str]:
        """
        Check if outline can be generated.
        
        Args:
            book: Book record
            
        Returns:
            Tuple of (can_proceed, reason)
        """
        if not book.notes_on_outline_before:
            return False, "notes_on_outline_before is required"
        
        if book.outline:
            return False, "Outline already exists"
        
        return True, "OK"
    
    def can_regenerate_outline(self, book: Book) -> Tuple[bool, str]:
        """
        Check if outline can be regenerated based on feedback.
        
        Args:
            book: Book record
            
        Returns:
            Tuple of (can_proceed, reason)
        """
        if not book.outline:
            return False, "No existing outline to regenerate"
        
        if not book.notes_on_outline_after:
            return False, "notes_on_outline_after is required for regeneration"
        
        return True, "OK"
    
    def should_proceed_after_outline(self, book: Book) -> Tuple[bool, str]:
        """
        Check if workflow should proceed after outline generation.
        
        Args:
            book: Book record
            
        Returns:
            Tuple of (should_proceed, reason)
        """
        if not book.status_outline_notes:
            return False, "status_outline_notes is not set"
        
        status = book.status_outline_notes
        
        if status == StatusEnum.YES:
            if not book.notes_on_outline_after:
                return False, "Waiting for notes_on_outline_after"
            # If notes are provided, regenerate outline
            return False, "Notes provided, regeneration needed"
        
        elif status == StatusEnum.NO_NOTES_NEEDED:
            return True, "Proceeding to chapter generation"
        
        elif status == StatusEnum.NO:
            return False, "Workflow paused by editor (status=no)"
        
        return False, "Invalid status"
    
    def can_generate_chapter(self, book: Book, chapter_number: int) -> Tuple[bool, str]:
        """
        Check if a specific chapter can be generated.
        
        Args:
            book: Book record
            chapter_number: Chapter number to generate
            
        Returns:
            Tuple of (can_proceed, reason)
        """
        if not book.outline:
            return False, "Outline must exist before generating chapters"
        
        # Check if previous chapter is completed (if not first chapter)
        if chapter_number > 1:
            chapters = self.db.get_chapters_by_book(book.id)
            prev_chapter = next(
                (c for c in chapters if c.chapter_number == chapter_number - 1),
                None
            )
            
            if not prev_chapter or not prev_chapter.content:
                return False, f"Previous chapter ({chapter_number - 1}) must be completed first"
        
        return True, "OK"
    
    def should_wait_for_chapter_notes(self, book: Book, chapter_number: int) -> Tuple[bool, str]:
        """
        Check if workflow should wait for chapter notes.
        
        Args:
            book: Book record
            chapter_number: Current chapter number
            
        Returns:
            Tuple of (should_wait, reason)
        """
        if not book.chapter_notes_status:
            return True, "chapter_notes_status not set"
        
        status = book.chapter_notes_status
        
        if status == StatusEnum.YES:
            # Check if chapter has notes
            chapters = self.db.get_chapters_by_book(book.id)
            chapter = next(
                (c for c in chapters if c.chapter_number == chapter_number),
                None
            )
            
            if chapter and not chapter.chapter_notes:
                return True, "Waiting for chapter notes"
            return False, "Chapter notes provided"
        
        elif status == StatusEnum.NO_NOTES_NEEDED:
            return False, "No notes needed, proceeding"
        
        elif status == StatusEnum.NO:
            return True, "Workflow paused (status=no)"
        
        return True, "Invalid status"
    
    def can_compile_final_draft(self, book: Book) -> Tuple[bool, str]:
        """
        Check if final draft can be compiled.
        
        Args:
            book: Book record
            
        Returns:
            Tuple of (can_proceed, reason)
        """
        # Check if all chapters exist
        chapters = self.db.get_chapters_by_book(book.id)
        
        if not chapters:
            return False, "No chapters exist"
        
        # Check if all chapters have content
        incomplete = [c.chapter_number for c in chapters if not c.content]
        if incomplete:
            return False, f"Chapters incomplete: {incomplete}"
        
        # Check final review status
        if not book.final_review_notes_status:
            return False, "final_review_notes_status not set"
        
        status = book.final_review_notes_status
        
        if status == StatusEnum.YES:
            return False, "Waiting for final review notes"
        
        elif status in [StatusEnum.NO_NOTES_NEEDED, StatusEnum.NO]:
            return True, "Ready for compilation"
        
        return False, "Invalid status"
    
    def update_book_stage(self, book_id: UUID, stage: BookOutputStatus):
        """
        Update book workflow stage.
        
        Args:
            book_id: Book ID
            stage: New workflow stage
        """
        self.db.update_book_status(book_id, stage)
        logger.info(f"Book {book_id} moved to stage: {stage.value}")
