"""
Context Manager for chapter generation.
Handles context chaining by maintaining chapter summaries.
"""
from typing import List
from uuid import UUID
from src.models.schemas import Chapter
from src.services.database_service import DatabaseService
from src.services.llm_service import LLMService
from src.utils.logger import logger


class ContextManager:
    """Manages context for chapter generation"""
    
    def __init__(self, db_service: DatabaseService, llm_service: LLMService):
        """
        Initialize context manager.
        
        Args:
            db_service: Database service instance
            llm_service: LLM service instance
        """
        self.db = db_service
        self.llm = llm_service
    
    def get_context_for_chapter(self, book_id: UUID, chapter_number: int) -> List[str]:
        """
        Get all previous chapter summaries for context.
        
        Args:
            book_id: Book ID
            chapter_number: Current chapter number
            
        Returns:
            List of summaries from previous chapters
        """
        try:
            summaries = self.db.get_previous_chapter_summaries(book_id, chapter_number)
            logger.info(f"Retrieved {len(summaries)} summaries for context (chapter {chapter_number})")
            return summaries
        except Exception as e:
            logger.error(f"Error getting context: {e}")
            return []
    
    def generate_and_store_summary(self, chapter: Chapter) -> str:
        """
        Generate summary for a chapter and update the database.
        
        Args:
            chapter: Chapter object
            
        Returns:
            Generated summary
        """
        try:
            if not chapter.content:
                logger.warning(f"No content for chapter {chapter.chapter_number}, skipping summary")
                return ""
            
            summary = self.llm.generate_chapter_summary(
                chapter.content,
                chapter.chapter_number,
                chapter.chapter_title or f"Chapter {chapter.chapter_number}"
            )
            
            # Update chapter with summary
            self.db.update_chapter(chapter.id, {'summary': summary})
            
            logger.success(f"Generated and stored summary for chapter {chapter.chapter_number}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise
    
    def rebuild_context_chain(self, book_id: UUID) -> int:
        """
        Regenerate all chapter summaries for a book.
        Useful if summaries need to be updated.
        
        Args:
            book_id: Book ID
            
        Returns:
            Number of summaries regenerated
        """
        try:
            chapters = self.db.get_chapters_by_book(book_id)
            count = 0
            
            for chapter in chapters:
                if chapter.content and not chapter.summary:
                    self.generate_and_store_summary(chapter)
                    count += 1
            
            logger.info(f"Rebuilt context chain: {count} summaries generated")
            return count
            
        except Exception as e:
            logger.error(f"Error rebuilding context chain: {e}")
            raise
