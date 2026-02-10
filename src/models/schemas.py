"""
Data models and schemas for the book generation system.
Uses Pydantic for validation and serialization.
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class StatusEnum(str, Enum):
    """Status values for feedback gates"""
    YES = "yes"
    NO = "no"
    NO_NOTES_NEEDED = "no_notes_needed"
    PENDING = "pending"
    APPROVED = "approved"
    NEEDS_REVISION = "needs_revision"


class BookOutputStatus(str, Enum):
    """Overall book generation status"""
    PENDING = "pending"
    OUTLINE_GENERATION = "outline_generation"
    OUTLINE_REVIEW = "outline_review"
    CHAPTER_GENERATION = "chapter_generation"
    CHAPTER_REVIEW = "chapter_review"
    FINAL_COMPILATION = "final_compilation"
    COMPLETED = "completed"
    PAUSED = "paused"
    ERROR = "error"


class ChapterStatus(str, Enum):
    """Chapter generation status"""
    PENDING = "pending"
    GENERATING = "generating"
    REVIEW = "review"
    APPROVED = "approved"
    REGENERATING = "regenerating"


class Book(BaseModel):
    """Main book record - matches Supabase books table"""
    id: UUID = Field(default_factory=uuid4)
    title: str
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class Outline(BaseModel):
    """Outline record - matches Supabase outlines table"""
    id: UUID = Field(default_factory=uuid4)
    book_id: UUID
    outline: Optional[str] = None
    notes_before: Optional[str] = None
    notes_after: Optional[str] = None
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class Chapter(BaseModel):
    """Chapter record - matches Supabase chapters table"""
    id: UUID = Field(default_factory=uuid4)
    book_id: UUID
    chapter_number: int
    title: Optional[str] = None
    content: Optional[str] = None
    summary: Optional[str] = None
    notes: Optional[str] = None
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class FinalState(BaseModel):
    """Final state record - matches Supabase final_state table"""
    id: UUID = Field(default_factory=uuid4)
    book_id: UUID
    final_review_status: Optional[str] = None
    output_status: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        use_enum_values = True


class GenerationLog(BaseModel):
    """Audit log for generation actions"""
    id: UUID = Field(default_factory=uuid4)
    book_id: UUID
    stage: str
    action: str
    details: dict
    created_at: datetime = Field(default_factory=datetime.now)




class OutlineInput(BaseModel):
    """Input for outline generation"""
    title: str
    notes_before: str


class ChapterInput(BaseModel):
    """Input for chapter generation"""
    chapter_number: int
    title: str
    outline_text: str
    previous_summaries: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class CompilationInput(BaseModel):
    """Input for final compilation"""
    book_id: UUID
    chapters: List[Chapter]
    final_review_notes: Optional[str] = None

