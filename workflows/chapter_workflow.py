"""
Chapter Workflow.
Handles chapter generation with context chaining and feedback loops.
"""
from uuid import UUID
from typing import List, Optional
from src.models.schemas import Book, Chapter, ChapterStatus, GenerationLog, BookOutputStatus
from src.services.database_service import DatabaseService
from src.services.llm_service import LLMService
from src.services.notification_service import NotificationService
from src.core.state_machine import StateMachine
from src.core.context_manager import ContextManager
from src.utils.logger import logger


class ChapterWorkflow:
    """Workflow for chapter generation"""
    
    def __init__(
        self,
        db_service: DatabaseService,
        llm_service: LLMService,
        notification_service: NotificationService,
        state_machine: StateMachine,
        context_manager: ContextManager
    ):
        """Initialize chapter workflow"""
        self.db = db_service
        self.llm = llm_service
        self.notifier = notification_service
        self.state_machine = state_machine
        self.context = context_manager
    
    def parse_outline_chapters(self, outline: str) -> List[tuple[int, str]]:
        """
        Parse outline to extract chapter numbers and titles.
        
        Args:
            outline: Outline text
            
        Returns:
            List of (chapter_number, chapter_title) tuples
        """
        chapters = []
        lines = outline.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for patterns like "Chapter 1:", "1.", "Chapter 1 -", etc.
            if 'chapter' in line.lower():
                # Try to extract chapter number and title
                parts = line.split(':', 1)
                if len(parts) == 2:
                    # Extract number
                    try:
                        num_str = ''.join(filter(str.isdigit, parts[0]))
                        if num_str:
                            chapter_num = int(num_str)
                            chapter_title = parts[1].strip()
                            chapters.append((chapter_num, chapter_title))
                    except ValueError:
                        continue
        
        # If no chapters found with above pattern, create default structure
        if not chapters:
            logger.warning("Could not parse chapters from outline, using default 10 chapters")
            chapters = [(i, f"Chapter {i}") for i in range(1, 11)]
        
        return chapters
    
    def initialize_chapters(self, book_id: UUID) -> tuple[bool, str]:
        """
        Initialize chapter records from outline.
        
        Args:
            book_id: Book ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            book = self.db.get_book(book_id)
            if not book or not book.outline:
                return False, "Book or outline not found"
            
            # Check if chapters already exist
            existing_chapters = self.db.get_chapters_by_book(book_id)
            if existing_chapters:
                logger.info(f"Chapters already initialized for book {book_id}")
                return True, f"{len(existing_chapters)} chapters already exist"
            
            # Parse outline to get chapters
            chapter_list = self.parse_outline_chapters(book.outline)
            
            # Create chapter records
            for chapter_num, chapter_title in chapter_list:
                chapter = Chapter(
                    book_id=book_id,
                    chapter_number=chapter_num,
                    chapter_title=chapter_title,
                    status=ChapterStatus.PENDING
                )
                self.db.create_chapter(chapter)
            
            logger.success(f"Initialized {len(chapter_list)} chapters for book {book_id}")
            return True, f"Initialized {len(chapter_list)} chapters"
            
        except Exception as e:
            logger.error(f"Error initializing chapters: {e}")
            return False, f"Error: {e}"
    
    def generate_chapter(self, book_id: UUID, chapter_number: int) -> tuple[bool, str]:
        """
        Generate content for a specific chapter.
        
        Args:
            book_id: Book ID
            chapter_number: Chapter number to generate
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get book
            book = self.db.get_book(book_id)
            if not book:
                return False, "Book not found"
            
            # Check if chapter can be generated
            can_proceed, reason = self.state_machine.can_generate_chapter(book, chapter_number)
            if not can_proceed:
                logger.warning(f"Cannot generate chapter {chapter_number}: {reason}")
                return False, reason
            
            # Get chapter record
            chapters = self.db.get_chapters_by_book(book_id)
            chapter = next(
                (c for c in chapters if c.chapter_number == chapter_number),
                None
            )
            
            if not chapter:
                return False, f"Chapter {chapter_number} not found"
            
            # Update status
            self.db.update_chapter_status(chapter.id, ChapterStatus.GENERATING)
            self.state_machine.update_book_stage(book_id, BookOutputStatus.CHAPTER_GENERATION)
            
            # Log action
            self.db.create_log(GenerationLog(
                book_id=book_id,
                stage="chapter",
                action="generation_started",
                details={
                    "chapter_number": chapter_number,
                    "chapter_title": chapter.chapter_title
                }
            ))
            
            # Get context from previous chapters
            previous_summaries = self.context.get_context_for_chapter(book_id, chapter_number)
            
            # Generate chapter content
            logger.info(f"Generating Chapter {chapter_number}: {chapter.chapter_title}")
            content = self.llm.generate_chapter(
                title=book.title,
                outline=book.outline,
                chapter_number=chapter_number,
                chapter_title=chapter.chapter_title,
                previous_summaries=previous_summaries,
                chapter_notes=chapter.chapter_notes
            )
            
            # Update chapter with content
            self.db.update_chapter(chapter.id, {
                'content': content,
                'status': ChapterStatus.REVIEW.value
            })
            
            # Generate and store summary
            self.context.generate_and_store_summary(
                Chapter(**{**chapter.dict(), 'content': content})
            )
            
            # Log completion
            self.db.create_log(GenerationLog(
                book_id=book_id,
                stage="chapter",
                action="generation_completed",
                details={
                    "chapter_number": chapter_number,
                    "content_length": len(content)
                }
            ))
            
            logger.success(f"Chapter {chapter_number} generated successfully")
            return True, f"Chapter {chapter_number} generated"
            
        except Exception as e:
            logger.error(f"Error generating chapter {chapter_number}: {e}")
            self.db.update_book_status(book_id, BookOutputStatus.ERROR)
            return False, f"Error: {e}"
    
    def generate_all_chapters(self, book_id: UUID) -> tuple[bool, str]:
        """
        Generate all chapters for a book sequentially.
        
        Args:
            book_id: Book ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Initialize chapters if needed
            self.initialize_chapters(book_id)
            
            # Get all chapters
            chapters = self.db.get_chapters_by_book(book_id)
            
            if not chapters:
                return False, "No chapters to generate"
            
            success_count = 0
            failed_chapters = []
            
            for chapter in chapters:
                # Skip if already has content
                if chapter.content:
                    logger.info(f"Chapter {chapter.chapter_number} already generated, skipping")
                    success_count += 1
                    continue
                
                # Check if we should wait for notes
                book = self.db.get_book(book_id)
                should_wait, reason = self.state_machine.should_wait_for_chapter_notes(
                    book, chapter.chapter_number
                )
                
                if should_wait:
                    logger.info(f"Waiting for notes on chapter {chapter.chapter_number}: {reason}")
                    self.notifier.notify_waiting_for_chapter_notes(
                        book.title,
                        chapter.chapter_number
                    )
                    break
                
                # Generate chapter
                success, message = self.generate_chapter(book_id, chapter.chapter_number)
                
                if success:
                    success_count += 1
                else:
                    failed_chapters.append(chapter.chapter_number)
                    logger.error(f"Failed to generate chapter {chapter.chapter_number}: {message}")
                    break  # Stop on first failure
            
            if failed_chapters:
                return False, f"Failed chapters: {failed_chapters}"
            
            # Check if all chapters are done
            all_chapters = self.db.get_chapters_by_book(book_id)
            all_done = all(c.content for c in all_chapters)
            
            if all_done:
                self.state_machine.update_book_stage(book_id, BookOutputStatus.FINAL_COMPILATION)
                return True, f"All {success_count} chapters generated successfully"
            
            return True, f"{success_count} chapters generated, more pending"
            
        except Exception as e:
            logger.error(f"Error generating chapters: {e}")
            return False, f"Error: {e}"
    
    def regenerate_chapter(self, book_id: UUID, chapter_number: int, notes: str) -> tuple[bool, str]:
        """
        Regenerate a chapter based on feedback notes.
        
        Args:
            book_id: Book ID
            chapter_number: Chapter number
            notes: Feedback notes
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get chapter
            chapters = self.db.get_chapters_by_book(book_id)
            chapter = next(
                (c for c in chapters if c.chapter_number == chapter_number),
                None
            )
            
            if not chapter:
                return False, f"Chapter {chapter_number} not found"
            
            # Update chapter with notes
            self.db.update_chapter(chapter.id, {
                'chapter_notes': notes,
                'status': ChapterStatus.REGENERATING.value
            })
            
            # Log action
            self.db.create_log(GenerationLog(
                book_id=book_id,
                stage="chapter",
                action="regeneration_started",
                details={
                    "chapter_number": chapter_number,
                    "notes": notes
                }
            ))
            
            # Regenerate
            success, message = self.generate_chapter(book_id, chapter_number)
            
            if success:
                self.db.update_chapter_status(chapter.id, ChapterStatus.APPROVED)
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error regenerating chapter: {e}")
            return False, f"Error: {e}"
