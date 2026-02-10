"""
Enhanced backend with interactive user approval workflow
Matches the improved user experience requirements
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import sys
from pathlib import Path
from uuid import UUID
import asyncio

sys.path.append(str(Path(__file__).parent.parent))

from src.services.database_service import DatabaseService
from src.services.llm_service import LLMService
from src.services.export_service import ExportService
from src.models.schemas import Book, Outline, Chapter, FinalState
from src.utils.logger import logger

app = FastAPI(title="Book Generation API - Interactive", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = DatabaseService()
llm = LLMService()
export = ExportService()

# Store workflow state
workflow_states = {}


class CreateBookRequest(BaseModel):
    title: str
    requirements: str
    num_chapters: Optional[int] = 10  # Default to 10 chapters


class ApprovalRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None
    rating: Optional[int] = None  # 0-10 rating


class OutlineResponse(BaseModel):
    book_id: str
    outline: str
    chapters: List[dict]  # [{"number": 1, "title": "..."}]
    status: str


class ChapterResponse(BaseModel):
    chapter_number: int
    title: str
    content: str
    status: str


@app.get("/")
async def root():
    return {"status": "healthy", "message": "Interactive Book Generation API"}


@app.post("/books")
async def create_book(request: CreateBookRequest):
    """Create a new book and initialize workflow"""
    try:
        book = db.create_book(request.title)
        
        outline = Outline(
            book_id=book.id,
            notes_before=request.requirements,
            status="pending"
        )
        db.create_outline(outline)
        
        final_state = FinalState(
            book_id=book.id,
            output_status="pending"
        )
        db.create_final_state(final_state)
        
        # Initialize workflow state
        workflow_states[str(book.id)] = {
            "step": "outline_pending",
            "current_chapter": 0,
            "total_chapters": 0,
            "num_chapters_requested": request.num_chapters,
            "ratings": []
        }
        
        return {
            "id": str(book.id),
            "title": book.title,
            "status": "created",
            "message": "Book created! Ready to generate outline."
        }
    except Exception as e:
        logger.error(f"Error creating book: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/books/{book_id}/generate-outline")
async def generate_outline(book_id: str):
    """Generate book outline for user approval"""
    try:
        book_uuid = UUID(book_id)
        outline_record = db.get_outline_by_book(book_uuid)
        book = db.get_book(book_uuid)
        
        if not outline_record:
            raise HTTPException(status_code=404, detail="Outline record not found")
        
        # Get requested chapter count
        num_chapters = workflow_states.get(book_id, {}).get("num_chapters_requested", 10)
        
        # Generate outline
        logger.info(f"Generating outline for: {book.title} ({num_chapters} chapters)")
        outline_text = llm.generate_outline(
            title=book.title,
            notes=outline_record.notes_before or "",
            num_chapters=num_chapters
        )
        
        # Parse outline to extract chapters
        chapters = parse_outline_chapters(outline_text, num_chapters)
        
        # Update outline record with generated outline
        db.update_outline(outline_record.id, {
            'outline': outline_text
        })
        
        # Update workflow state (preserve existing fields)
        if book_id not in workflow_states:
            workflow_states[book_id] = {}
        
        workflow_states[book_id].update({
            "step": "outline_review",
            "current_chapter": 0,
            "total_chapters": len(chapters)
        })
        
        # Keep num_chapters_requested if it exists
        if "num_chapters_requested" not in workflow_states[book_id]:
            workflow_states[book_id]["num_chapters_requested"] = num_chapters
        
        # Initialize ratings list if not exists
        if "ratings" not in workflow_states[book_id]:
            workflow_states[book_id]["ratings"] = []
        
        return OutlineResponse(
            book_id=book_id,
            outline=outline_text,
            chapters=chapters,
            status="pending_approval"
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating outline: {error_msg}")
        
        # Provide user-friendly error messages
        if "rate limit" in error_msg.lower() or "quota exceeded" in error_msg.lower():
            raise HTTPException(
                status_code=429, 
                detail="API rate limit exceeded. The system is automatically retrying. Please wait a moment and try again, or wait a few minutes if this persists. (Free tier: 20 requests/minute)"
            )
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@app.post("/books/{book_id}/approve-outline")
async def approve_outline(book_id: str, approval: ApprovalRequest):
    """User approves or requests changes to outline"""
    try:
        book_uuid = UUID(book_id)
        outline_record = db.get_outline_by_book(book_uuid)
        
        # Store rating if provided
        if approval.rating is not None:
            if book_id in workflow_states:
                workflow_states[book_id]["ratings"].append({
                    "step": "outline",
                    "rating": approval.rating
                })
        
        if approval.approved:
            # User approved - workflow continues
            # (Don't update user_rating in database until schema updated)
            
            # Update workflow state - ensure it exists first
            if book_id not in workflow_states:
                workflow_states[book_id] = {
                    "num_chapters_requested": 10,
                    "total_chapters": 10,
                    "current_chapter": 0,
                    "ratings": []
                }
            
            workflow_states[book_id]["step"] = "chapter_generation"
            
            logger.info(f"Outline approved for book {book_id}. Workflow state: {workflow_states[book_id]}")
            
            return {
                "message": "Outline approved! Ready to generate chapters.",
                "status": "approved",
                "next_step": "generate_chapter_1"
            }
        else:
            # User wants changes
            if not approval.feedback:
                raise HTTPException(status_code=400, detail="Feedback required for changes")
            
            # Store feedback
            db.update_outline(outline_record.id, {
                'notes_after': approval.feedback
            })
            
            return {
                "message": "Feedback received. Regenerating outline...",
                "status": "needs_revision",
                "next_step": "regenerate_outline"
            }
            
    except Exception as e:
        logger.error(f"Error approving outline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/books/{book_id}/regenerate-outline")
async def regenerate_outline(book_id: str):
    """Regenerate outline based on user feedback"""
    try:
        book_uuid = UUID(book_id)
        outline_record = db.get_outline_by_book(book_uuid)
        book = db.get_book(book_uuid)
        
        # Get requested chapter count
        num_chapters = workflow_states.get(book_id, {}).get("num_chapters_requested", 10)
        
        # Combine original notes with feedback
        combined_notes = f"{outline_record.notes_before}\n\nUser Feedback:\n{outline_record.notes_after}"
        
        # Regenerate outline
        outline_text = llm.regenerate_outline(
            title=book.title,
            original_outline=outline_record.outline,
            feedback_notes=outline_record.notes_after,
            num_chapters=num_chapters
        )
        
        chapters = parse_outline_chapters(outline_text, num_chapters)
        
        db.update_outline(outline_record.id, {
            'outline': outline_text
        })
        
        return OutlineResponse(
            book_id=book_id,
            outline=outline_text,
            chapters=chapters,
            status="pending_approval"
        )
        
    except Exception as e:
        logger.error(f"Error regenerating outline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/books/{book_id}/generate-chapter/{chapter_num}")
async def generate_chapter(book_id: str, chapter_num: int):
    """Generate a specific chapter"""
    try:
        book_uuid = UUID(book_id)
        book = db.get_book(book_uuid)
        outline_record = db.get_outline_by_book(book_uuid)
        
        # Check approval status from workflow state (not database)
        workflow_step = workflow_states.get(book_id, {}).get("step", "")
        logger.info(f"Generate chapter {chapter_num} - Current workflow step: {workflow_step}")
        logger.info(f"Workflow states for book {book_id}: {workflow_states.get(book_id, {})}")
        
        if workflow_step not in ["chapter_generation", "chapter_review"]:
            raise HTTPException(status_code=400, detail=f"Outline must be approved first. Current step: {workflow_step}")
        
        # Get previous chapter summaries for context
        prev_summaries = db.get_previous_chapter_summaries(book_uuid, chapter_num)
        
        # Get requested chapter count
        num_chapters = workflow_states.get(book_id, {}).get("num_chapters_requested", 10)
        
        # Get chapter title from outline
        chapters = parse_outline_chapters(outline_record.outline, num_chapters)
        chapter_title = next((c["title"] for c in chapters if c["number"] == chapter_num), f"Chapter {chapter_num}")
        
        # Generate chapter
        logger.info(f"Generating chapter {chapter_num}: {chapter_title}")
        content = llm.generate_chapter(
            title=book.title,
            outline=outline_record.outline,
            chapter_number=chapter_num,
            chapter_title=chapter_title,
            previous_summaries=prev_summaries
        )
        
        # Create chapter record
        chapter = Chapter(
            book_id=book_uuid,
            chapter_number=chapter_num,
            title=chapter_title,
            content=content
        )
        saved_chapter = db.create_chapter(chapter)
        
        # Update workflow state
        if book_id in workflow_states:
            workflow_states[book_id]["current_chapter"] = chapter_num
        
        return ChapterResponse(
            chapter_number=chapter_num,
            title=chapter_title,
            content=content,
            status="pending_approval"
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating chapter: {error_msg}")
        
        # Provide user-friendly error messages
        if "rate limit" in error_msg.lower() or "quota exceeded" in error_msg.lower():
            raise HTTPException(
                status_code=429, 
                detail="API rate limit exceeded. The system is automatically retrying. Please wait a moment and try again, or wait a few minutes if this persists. (Free tier: 20 requests/minute)"
            )
        else:
            raise HTTPException(status_code=500, detail=error_msg)


@app.post("/books/{book_id}/approve-chapter/{chapter_num}")
async def approve_chapter(book_id: str, chapter_num: int, approval: ApprovalRequest):
    """User approves or requests changes to a chapter"""
    try:
        book_uuid = UUID(book_id)
        
        # Store rating if provided
        if approval.rating is not None:
            if book_id in workflow_states:
                workflow_states[book_id]["ratings"].append({
                    "step": f"chapter_{chapter_num}",
                    "rating": approval.rating
                })
        
        # Get chapter
        chapters = db.get_chapters_by_book(book_uuid)
        chapter = next((c for c in chapters if c.chapter_number == chapter_num), None)
        
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        
        if approval.approved:
            # Try to generate summary for context in next chapters (non-blocking)
            summary = None
            try:
                summary = llm.generate_chapter_summary(
                    chapter_content=chapter.content,
                    chapter_number=chapter_num,
                    chapter_title=chapter.title
                )
                logger.success(f"Summary generated for chapter {chapter_num}")
            except Exception as summary_error:
                # Don't fail approval if summary generation fails
                logger.warning(f"Could not generate summary for chapter {chapter_num}: {summary_error}")
                logger.info("Continuing without summary - chapter can still be approved")
            
            # Update chapter with summary if generated
            if summary:
                try:
                    update_data = {'summary': summary}
                    db.update_chapter(chapter.id, update_data)
                except Exception as update_error:
                    logger.warning(f"Could not save summary: {update_error}")
            
            # Check if this was the last chapter
            total_chapters = workflow_states.get(book_id, {}).get("total_chapters", 10)
            
            if chapter_num < total_chapters:
                return {
                    "message": f"Chapter {chapter_num} approved!",
                    "status": "approved",
                    "next_step": f"generate_chapter_{chapter_num + 1}"
                }
            else:
                return {
                    "message": "All chapters completed!",
                    "status": "all_approved",
                    "next_step": "final_review"
                }
        else:
            # User wants changes
            if not approval.feedback:
                raise HTTPException(status_code=400, detail="Feedback required for changes")
            
            # Store feedback in workflow state (database columns may not exist yet)
            if book_id in workflow_states:
                if "chapter_feedback" not in workflow_states[book_id]:
                    workflow_states[book_id]["chapter_feedback"] = {}
                workflow_states[book_id]["chapter_feedback"][chapter_num] = approval.feedback
            
            return {
                "message": "Feedback received. Regenerating chapter...",
                "status": "needs_revision",
                "feedback": approval.feedback
            }
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error approving chapter: {error_msg}")
        
        # Provide user-friendly error messages
        if "rate limit" in error_msg.lower() or "quota exceeded" in error_msg.lower():
            raise HTTPException(
                status_code=429, 
                detail="API rate limit exceeded. Please wait a moment and try again. (Free tier: 20 requests/minute)"
            )
        elif "not found" in error_msg.lower():
            raise HTTPException(status_code=404, detail="Chapter not found in database")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to process chapter approval: {error_msg}")


@app.post("/books/{book_id}/regenerate-chapter/{chapter_num}")
async def regenerate_chapter(book_id: str, chapter_num: int, feedback: str):
    """Regenerate chapter with user feedback"""
    try:
        book_uuid = UUID(book_id)
        book = db.get_book(book_uuid)
        outline_record = db.get_outline_by_book(book_uuid)
        
        chapters = db.get_chapters_by_book(book_uuid)
        chapter = next((c for c in chapters if c.chapter_number == chapter_num), None)
        
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        
        prev_summaries = db.get_previous_chapter_summaries(book_uuid, chapter_num)
        
        # Regenerate with feedback
        enhanced_prompt = f"User feedback: {feedback}\n\nOriginal chapter title: {chapter.title}"
        
        content = llm.generate_chapter(
            title=book.title,
            outline=outline_record.outline,
            chapter_number=chapter_num,
            chapter_title=f"{chapter.title} (Revised)",
            previous_summaries=prev_summaries
        )
        
        db.update_chapter(chapter.id, {
            'content': content
        })
        
        return ChapterResponse(
            chapter_number=chapter_num,
            title=chapter.title,
            content=content,
            status="pending_approval"
        )
    except Exception as e:
        logger.error(f"Error regenerating chapter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/books/{book_id}/compile")
async def compile_book(book_id: str):
    """Compile final book to PDF/DOCX/TXT"""
    try:
        book_uuid = UUID(book_id)
        book = db.get_book(book_uuid)
        chapters = db.get_chapters_by_book(book_uuid)
        
        # Check we have chapters to compile
        if not chapters:
            raise HTTPException(
                status_code=400,
                detail="No chapters found to compile"
            )
        
        # Get expected chapter count
        expected_chapters = workflow_states.get(book_id, {}).get("total_chapters", len(chapters))
        
        # Verify we have all chapters
        if len(chapters) < expected_chapters:
            raise HTTPException(
                status_code=400,
                detail=f"Only {len(chapters)} of {expected_chapters} chapters have been generated"
            )
        
        logger.info(f"Compiling book '{book.title}' with {len(chapters)} chapters")
        
        # Export to all formats
        docx_path = export.export_to_docx(book, chapters)
        pdf_path = export.export_to_pdf(book, chapters)
        txt_path = export.export_to_txt(book, chapters)
        
        db.update_or_create_final_state(book_uuid, {
            'output_status': 'completed'
        })
        
        return {
            "message": "Book compiled successfully!",
            "files": {
                "docx": str(docx_path),
                "pdf": str(pdf_path),
                "txt": str(txt_path)
            },
            "ratings": workflow_states.get(book_id, {}).get("ratings", [])
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error compiling book: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Failed to compile book: {error_msg}")


@app.get("/books/{book_id}/status")
async def get_status(book_id: str):
    """Get current workflow status"""
    try:
        book_uuid = UUID(book_id)
        book = db.get_book(book_uuid)
        outline = db.get_outline_by_book(book_uuid)
        chapters = db.get_chapters_by_book(book_uuid)
        
        workflow_state = workflow_states.get(book_id, {})
        
        # Count chapters that have summaries as "approved" (since we generate summary on approval)
        chapters_approved = len([c for c in chapters if c.summary])
        
        return {
            "book_id": book_id,
            "title": book.title,
            "workflow_step": workflow_state.get("step", "created"),
            "outline_status": "approved" if workflow_state.get("step") in ["chapter_generation", "chapter_review", "final", "completed"] else "pending",
            "chapters_total": workflow_state.get("total_chapters", 0),
            "chapters_approved": chapters_approved,
            "current_chapter": workflow_state.get("current_chapter", 0),
            "ratings": workflow_state.get("ratings", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def parse_outline_chapters(outline_text: str, expected_count: int = 10) -> List[dict]:
    """Parse outline text to extract chapter titles - ONLY chapter headings, not descriptions"""
    import re
    chapters = []
    seen_numbers = set()
    lines = outline_text.split('\n')
    
    for line in lines:
        line = line.strip()
        # ONLY match lines that START with "Chapter [number]:"
        # This excludes descriptions that mention "chapter" in them
        match = re.match(r'^Chapter\s+(\d+)\s*:\s*(.+)$', line, re.IGNORECASE)
        if match:
            chapter_num = int(match.group(1))
            chapter_title = match.group(2).strip()
            
            # Skip if we've already seen this chapter number (avoid duplicates)
            if chapter_num in seen_numbers:
                logger.warning(f"Skipping duplicate chapter number: {chapter_num}")
                continue
            
            # Skip placeholder titles
            if "[chapter title here]" in chapter_title.lower() or chapter_title == "":
                logger.warning(f"Skipping placeholder chapter: {chapter_title}")
                continue
            
            # Remove any trailing "Description:" or similar
            chapter_title = re.sub(r'\s*Description:.*$', '', chapter_title, flags=re.IGNORECASE)
            
            seen_numbers.add(chapter_num)
            chapters.append({
                "number": chapter_num,
                "title": chapter_title
            })
            
            # Stop once we have enough chapters
            if len(chapters) >= expected_count:
                break
    
    # Sort by chapter number and take only the expected count
    chapters.sort(key=lambda x: x["number"])
    chapters = chapters[:expected_count]
    
    # Renumber chapters sequentially (1, 2, 3...)
    for idx, chapter in enumerate(chapters, start=1):
        chapter["number"] = idx
    
    # Validate we got the right count
    if len(chapters) != expected_count:
        logger.warning(f"Expected {expected_count} chapters but only parsed {len(chapters)} valid chapters")
    
    # If no chapters found, generate defaults
    if not chapters:
        logger.error(f"No valid chapters found in outline. Generating {expected_count} defaults.")
        chapters = [{"number": i, "title": f"Chapter {i}"} for i in range(1, expected_count + 1)]
    
    return chapters


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
