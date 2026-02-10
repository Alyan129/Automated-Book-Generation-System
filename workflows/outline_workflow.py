"""
Outline Workflow.
Handles outline generation and regeneration with feedback loops.
"""
from uuid import UUID
from src.models.schemas import Book, GenerationLog, BookOutputStatus
from src.services.database_service import DatabaseService
from src.services.llm_service import LLMService
from src.services.notification_service import NotificationService
from src.core.state_machine import StateMachine
from src.utils.logger import logger


class OutlineWorkflow:
    """Workflow for outline generation"""
    
    def __init__(
        self,
        db_service: DatabaseService,
        llm_service: LLMService,
        notification_service: NotificationService,
        state_machine: StateMachine
    ):
        """Initialize outline workflow"""
        self.db = db_service
        self.llm = llm_service
        self.notifier = notification_service
        self.state_machine = state_machine
    
    def generate_outline(self, book_id: UUID) -> tuple[bool, str]:
        """
        Generate outline for a book.
        
        Args:
            book_id: Book ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get book
            book = self.db.get_book(book_id)
            if not book:
                return False, "Book not found"
            
            # Check if outline can be generated
            can_proceed, reason = self.state_machine.can_generate_outline(book)
            if not can_proceed:
                logger.warning(f"Cannot generate outline: {reason}")
                return False, reason
            
            # Update status
            self.state_machine.update_book_stage(book_id, BookOutputStatus.OUTLINE_GENERATION)
            
            # Log action
            self.db.create_log(GenerationLog(
                book_id=book_id,
                stage="outline",
                action="generation_started",
                details={"title": book.title}
            ))
            
            # Generate outline
            logger.info(f"Generating outline for: {book.title}")
            outline = self.llm.generate_outline(book.title, book.notes_on_outline_before)
            
            # Update book with outline
            self.db.update_book(book_id, {
                'outline': outline,
                'book_output_status': BookOutputStatus.OUTLINE_REVIEW.value
            })
            
            # Log completion
            self.db.create_log(GenerationLog(
                book_id=book_id,
                stage="outline",
                action="generation_completed",
                details={"outline_length": len(outline)}
            ))
            
            # Send notification
            self.notifier.notify_outline_ready(book.title, str(book_id))
            
            logger.success(f"Outline generated for: {book.title}")
            return True, "Outline generated successfully"
            
        except Exception as e:
            logger.error(f"Error generating outline: {e}")
            self.db.update_book_status(book_id, BookOutputStatus.ERROR)
            self.notifier.notify_error(book.title if book else "Unknown", str(e))
            return False, f"Error: {e}"
    
    def regenerate_outline(self, book_id: UUID) -> tuple[bool, str]:
        """
        Regenerate outline based on feedback.
        
        Args:
            book_id: Book ID
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get book
            book = self.db.get_book(book_id)
            if not book:
                return False, "Book not found"
            
            # Check if regeneration is allowed
            can_proceed, reason = self.state_machine.can_regenerate_outline(book)
            if not can_proceed:
                logger.warning(f"Cannot regenerate outline: {reason}")
                return False, reason
            
            # Update status
            self.state_machine.update_book_stage(book_id, BookOutputStatus.OUTLINE_GENERATION)
            
            # Log action
            self.db.create_log(GenerationLog(
                book_id=book_id,
                stage="outline",
                action="regeneration_started",
                details={"feedback": book.notes_on_outline_after}
            ))
            
            # Regenerate outline
            logger.info(f"Regenerating outline for: {book.title}")
            new_outline = self.llm.regenerate_outline(
                book.title,
                book.outline,
                book.notes_on_outline_after
            )
            
            # Update book
            self.db.update_book(book_id, {
                'outline': new_outline,
                'book_output_status': BookOutputStatus.OUTLINE_REVIEW.value,
                'notes_on_outline_after': None  # Clear feedback after processing
            })
            
            # Log completion
            self.db.create_log(GenerationLog(
                book_id=book_id,
                stage="outline",
                action="regeneration_completed",
                details={"outline_length": len(new_outline)}
            ))
            
            # Send notification
            self.notifier.notify_outline_ready(book.title, str(book_id))
            
            logger.success(f"Outline regenerated for: {book.title}")
            return True, "Outline regenerated successfully"
            
        except Exception as e:
            logger.error(f"Error regenerating outline: {e}")
            self.db.update_book_status(book_id, BookOutputStatus.ERROR)
            return False, f"Error: {e}"
    
    def check_and_proceed(self, book_id: UUID) -> tuple[bool, str]:
        """
        Check if workflow can proceed after outline stage.
        
        Args:
            book_id: Book ID
            
        Returns:
            Tuple of (can_proceed, reason)
        """
        try:
            book = self.db.get_book(book_id)
            if not book:
                return False, "Book not found"
            
            should_proceed, reason = self.state_machine.should_proceed_after_outline(book)
            
            if should_proceed:
                # Move to chapter generation stage
                self.state_machine.update_book_stage(book_id, BookOutputStatus.CHAPTER_GENERATION)
                logger.info(f"Book {book_id} ready for chapter generation")
                return True, "Ready for chapter generation"
            else:
                # Check if regeneration is needed
                if "regeneration needed" in reason:
                    return self.regenerate_outline(book_id)
                
                # Otherwise, pause
                self.state_machine.update_book_stage(book_id, BookOutputStatus.PAUSED)
                self.notifier.notify_paused(book.title, reason)
                return False, reason
                
        except Exception as e:
            logger.error(f"Error checking outline status: {e}")
            return False, f"Error: {e}"
