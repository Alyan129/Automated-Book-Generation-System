"""
Compilation Workflow.
Handles final book compilation and export.
"""
from uuid import UUID
from pathlib import Path
from typing import Dict
from src.models.schemas import Book, BookOutputStatus, GenerationLog
from src.services.database_service import DatabaseService
from src.services.export_service import ExportService
from src.services.notification_service import NotificationService
from src.core.state_machine import StateMachine
from src.utils.logger import logger


class CompilationWorkflow:
    """Workflow for final compilation"""
    
    def __init__(
        self,
        db_service: DatabaseService,
        export_service: ExportService,
        notification_service: NotificationService,
        state_machine: StateMachine
    ):
        """Initialize compilation workflow"""
        self.db = db_service
        self.export = export_service
        self.notifier = notification_service
        self.state_machine = state_machine
    
    def compile_book(self, book_id: UUID, formats: list[str] = None) -> tuple[bool, Dict[str, Path]]:
        """
        Compile book to final output formats.
        
        Args:
            book_id: Book ID
            formats: List of formats to export ('docx', 'pdf', 'txt'). None = all formats
            
        Returns:
            Tuple of (success, dict of format -> file path)
        """
        try:
            # Get book
            book = self.db.get_book(book_id)
            if not book:
                return False, {}
            
            # Check if compilation can proceed
            can_proceed, reason = self.state_machine.can_compile_final_draft(book)
            if not can_proceed:
                logger.warning(f"Cannot compile book: {reason}")
                return False, {}
            
            # Update status
            self.state_machine.update_book_stage(book_id, BookOutputStatus.FINAL_COMPILATION)
            
            # Log action
            self.db.create_log(GenerationLog(
                book_id=book_id,
                stage="compilation",
                action="compilation_started",
                details={"formats": formats or "all"}
            ))
            
            # Get all chapters
            chapters = self.db.get_chapters_by_book(book_id)
            
            if not chapters:
                return False, {}
            
            logger.info(f"Compiling book: {book.title} ({len(chapters)} chapters)")
            
            # Export to requested formats
            results = {}
            
            if formats is None or 'all' in formats:
                # Export all formats
                results = self.export.export_all_formats(book, chapters)
            else:
                # Export specific formats
                if 'docx' in formats:
                    try:
                        results['docx'] = self.export.export_to_docx(book, chapters)
                    except Exception as e:
                        logger.error(f"DOCX export failed: {e}")
                
                if 'pdf' in formats:
                    try:
                        results['pdf'] = self.export.export_to_pdf(book, chapters)
                    except Exception as e:
                        logger.error(f"PDF export failed: {e}")
                
                if 'txt' in formats:
                    try:
                        results['txt'] = self.export.export_to_txt(book, chapters)
                    except Exception as e:
                        logger.error(f"TXT export failed: {e}")
            
            if not results:
                return False, {}
            
            # Update status to completed
            self.state_machine.update_book_stage(book_id, BookOutputStatus.COMPLETED)
            
            # Log completion
            self.db.create_log(GenerationLog(
                book_id=book_id,
                stage="compilation",
                action="compilation_completed",
                details={
                    "formats": list(results.keys()),
                    "files": {k: str(v) for k, v in results.items()}
                }
            ))
            
            # Send notification
            output_paths = ", ".join([str(p) for p in results.values()])
            self.notifier.notify_final_draft_ready(book.title, str(book_id), output_paths)
            
            logger.success(f"Book compiled successfully: {book.title}")
            return True, results
            
        except Exception as e:
            logger.error(f"Error compiling book: {e}")
            self.db.update_book_status(book_id, BookOutputStatus.ERROR)
            book = self.db.get_book(book_id)
            if book:
                self.notifier.notify_error(book.title, str(e))
            return False, {}
    
    def get_compilation_status(self, book_id: UUID) -> Dict:
        """
        Get compilation status and readiness.
        
        Args:
            book_id: Book ID
            
        Returns:
            Status dictionary
        """
        try:
            book = self.db.get_book(book_id)
            if not book:
                return {"error": "Book not found"}
            
            chapters = self.db.get_chapters_by_book(book_id)
            
            total_chapters = len(chapters)
            completed_chapters = len([c for c in chapters if c.content])
            
            can_compile, reason = self.state_machine.can_compile_final_draft(book)
            
            return {
                "book_id": str(book_id),
                "title": book.title,
                "status": book.book_output_status,
                "total_chapters": total_chapters,
                "completed_chapters": completed_chapters,
                "can_compile": can_compile,
                "reason": reason if not can_compile else "Ready for compilation"
            }
            
        except Exception as e:
            logger.error(f"Error getting compilation status: {e}")
            return {"error": str(e)}
