"""
Supabase Database Service.
Handles all database operations for books, outlines, chapters, and final state.
Updated to match your Supabase schema.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from supabase import create_client, Client
from src.core.config import config
from src.models.schemas import Book, Outline, Chapter, FinalState
from src.utils.logger import logger


class DatabaseService:
    """Service for Supabase database operations"""
    
    def __init__(self):
        """Initialize Supabase client"""
        if not config.SUPABASE_URL or not config.SUPABASE_KEY:
            raise ValueError("Supabase configuration missing")
        
        self.client: Client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        logger.info("Connected to Supabase")
    
    # ==================== Book Operations ====================
    
    def create_book(self, title: str) -> Book:
        """Create a new book record"""
        try:
            book = Book(title=title)
            data = {'id': str(book.id), 'title': title}
            
            result = self.client.table('books').insert(data).execute()
            logger.info(f"Created book: {title} (ID: {book.id})")
            return book
        except Exception as e:
            logger.error(f"Error creating book: {e}")
            raise
    
    def get_book(self, book_id: UUID) -> Optional[Book]:
        """Get book by ID"""
        try:
            result = self.client.table('books').select('*').eq('id', str(book_id)).execute()
            if result.data:
                return Book(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching book {book_id}: {e}")
            raise
    
    def get_all_books(self) -> List[Book]:
        """Get all books"""
        try:
            result = self.client.table('books').select('*').order('created_at', desc=True).execute()
            return [Book(**book) for book in result.data]
        except Exception as e:
            logger.error(f"Error fetching books: {e}")
            raise
    
    # ==================== Outline Operations ====================
    
    def create_outline(self, outline: Outline) -> Outline:
        """Create a new outline record"""
        try:
            data = outline.model_dump(mode='json')
            data['id'] = str(data['id'])
            data['book_id'] = str(data['book_id'])
            
            result = self.client.table('outlines').insert(data).execute()
            logger.info(f"Created outline for book {outline.book_id}")
            return outline
        except Exception as e:
            logger.error(f"Error creating outline: {e}")
            raise
    
    def get_outline_by_book(self, book_id: UUID) -> Optional[Outline]:
        """Get outline for a book (returns most recent if multiple)"""
        try:
            result = (
                self.client.table('outlines')
                .select('*')
                .eq('book_id', str(book_id))
                .order('created_at', desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                return Outline(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching outline for book {book_id}: {e}")
            raise
    
    def update_outline(self, outline_id: UUID, updates: Dict[str, Any]) -> Outline:
        """Update outline record"""
        try:
            result = self.client.table('outlines').update(updates).eq('id', str(outline_id)).execute()
            logger.info(f"Updated outline {outline_id}")
            return Outline(**result.data[0])
        except Exception as e:
            logger.error(f"Error updating outline {outline_id}: {e}")
            raise
    
    # ==================== Chapter Operations ====================
    
    def create_chapter(self, chapter: Chapter) -> Chapter:
        """Create a new chapter record"""
        try:
            data = {
                'book_id': str(chapter.book_id),
                'chapter_number': chapter.chapter_number,
                'title': chapter.title,
                'content': chapter.content,
                'summary': chapter.summary
            }
            # Don't include 'status' or 'notes' - Supabase table uses defaults
            
            result = self.client.table('chapters').insert(data).execute()
            logger.info(f"Created chapter {chapter.chapter_number} for book {chapter.book_id}")
            return Chapter(**result.data[0])
        except Exception as e:
            logger.error(f"Error creating chapter: {e}")
            raise
    
    def get_chapter(self, chapter_id: UUID) -> Optional[Chapter]:
        """Get chapter by ID"""
        try:
            result = self.client.table('chapters').select('*').eq('id', str(chapter_id)).execute()
            if result.data:
                return Chapter(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching chapter {chapter_id}: {e}")
            raise
    
    def get_chapters_by_book(self, book_id: UUID) -> List[Chapter]:
        """Get all chapters for a book, ordered by chapter number"""
        try:
            result = (
                self.client.table('chapters')
                .select('*')
                .eq('book_id', str(book_id))
                .order('chapter_number')
                .execute()
            )
            return [Chapter(**chapter) for chapter in result.data]
        except Exception as e:
            logger.error(f"Error fetching chapters for book {book_id}: {e}")
            raise
    
    def update_chapter(self, chapter_id: UUID, updates: Dict[str, Any]) -> Chapter:
        """Update chapter record"""
        try:
            result = self.client.table('chapters').update(updates).eq('id', str(chapter_id)).execute()
            logger.info(f"Updated chapter {chapter_id}")
            return Chapter(**result.data[0])
        except Exception as e:
            logger.error(f"Error updating chapter {chapter_id}: {e}")
            raise
    
    def get_previous_chapter_summaries(self, book_id: UUID, before_chapter: int) -> List[str]:
        """Get summaries of all chapters before a given chapter number"""
        try:
            result = (
                self.client.table('chapters')
                .select('summary')
                .eq('book_id', str(book_id))
                .lt('chapter_number', before_chapter)
                .order('chapter_number')
                .execute()
            )
            return [chapter['summary'] for chapter in result.data if chapter.get('summary')]
        except Exception as e:
            logger.error(f"Error fetching previous summaries: {e}")
            raise
    
    # ==================== Final State Operations ====================
    
    def create_final_state(self, final_state: FinalState) -> FinalState:
        """Create or update final state record"""
        try:
            data = final_state.model_dump(mode='json')
            data['id'] = str(data['id'])
            data['book_id'] = str(data['book_id'])
            
            result = self.client.table('final_state').insert(data).execute()
            logger.info(f"Created final state for book {final_state.book_id}")
            return final_state
        except Exception as e:
            logger.error(f"Error creating final state: {e}")
            raise
    
    def get_final_state_by_book(self, book_id: UUID) -> Optional[FinalState]:
        """Get final state for a book"""
        try:
            result = (
                self.client.table('final_state')
                .select('*')
                .eq('book_id', str(book_id))
                .order('created_at', desc=True)
                .limit(1)
                .execute()
            )
            if result.data:
                return FinalState(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error fetching final state for book {book_id}: {e}")
            raise
    
    def update_final_state(self, final_state_id: UUID, updates: Dict[str, Any]) -> FinalState:
        """Update final state record"""
        try:
            result = self.client.table('final_state').update(updates).eq('id', str(final_state_id)).execute()
            logger.info(f"Updated final state {final_state_id}")
            return FinalState(**result.data[0])
        except Exception as e:
            logger.error(f"Error updating final state {final_state_id}: {e}")
            raise
    
    def update_or_create_final_state(self, book_id: UUID, updates: Dict[str, Any]) -> FinalState:
        """Update final state if exists, create if not"""
        try:
            existing = self.get_final_state_by_book(book_id)
            if existing:
                return self.update_final_state(existing.id, updates)
            else:
                final_state = FinalState(book_id=book_id, **updates)
                return self.create_final_state(final_state)
        except Exception as e:
            logger.error(f"Error updating/creating final state: {e}")
            raise
