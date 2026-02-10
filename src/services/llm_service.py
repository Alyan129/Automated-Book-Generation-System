"""
Gemini LLM Service for content generation.
Handles all interactions with Google's Gemini API.
"""
import time
import re
from typing import Optional, List
import google.generativeai as genai
from src.core.config import config
from src.utils.logger import logger


class LLMService:
    """Service for interacting with Gemini API"""
    
    def __init__(self):
        """Initialize Gemini API"""
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not configured")
        
        genai.configure(api_key=config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(config.GEMINI_MODEL)
        logger.info(f"Initialized Gemini model: {config.GEMINI_MODEL}")
    
    def _call_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call Gemini API with automatic retry on rate limit errors.
        
        Args:
            prompt: The prompt to send
            max_retries: Maximum number of retry attempts
            
        Returns:
            Generated content
        """
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response.text
            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a rate limit error (429)
                if "429" in error_msg or "quota exceeded" in error_msg.lower():
                    # Extract retry delay from error message
                    retry_match = re.search(r'retry in ([\d.]+)s', error_msg)
                    if retry_match:
                        retry_delay = float(retry_match.group(1))
                    else:
                        # Default exponential backoff
                        retry_delay = (2 ** attempt) * 5  # 5s, 10s, 20s
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit. Retrying in {retry_delay:.1f} seconds... (Attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        continue
                    else:
                        logger.error(f"Rate limit exceeded after {max_retries} attempts")
                        raise Exception(f"API rate limit exceeded. Please wait a few minutes and try again. You're on the free tier (20 requests/minute).")
                else:
                    # Other errors, don't retry
                    logger.error(f"API error: {error_msg}")
                    raise
        
        raise Exception("Failed after maximum retries")
    
    def generate_outline(self, title: str, notes: str, num_chapters: int = 10) -> str:
        """
        Generate book outline based on title and notes.
        
        Args:
            title: Book title
            notes: Editor notes for outline generation
            num_chapters: Exact number of chapters requested
            
        Returns:
            Generated outline as formatted text
        """
        prompt = f"""You are a professional book outline creator. Create a detailed outline for a book with the following specifications:

Title: {title}

Editor's Requirements and Notes:
{notes}

CRITICAL REQUIREMENT: You MUST generate EXACTLY {num_chapters} chapters. Count carefully!

Generate a comprehensive book outline with this EXACT format:

## BOOK OVERVIEW
[Write 2-3 paragraphs overview here]

## CHAPTERS

Chapter 1: [Chapter Title Here]
Description: [2-3 sentence description]
Key Points: [bullet points]

Chapter 2: [Chapter Title Here]
Description: [2-3 sentence description]
Key Points: [bullet points]

[Continue for all {num_chapters} chapters - DO NOT generate more or fewer]

STRICT RULES YOU MUST FOLLOW:
1. Generate EXACTLY {num_chapters} chapters - no more, no fewer
2. Each chapter heading line MUST start with "Chapter [number]: [actual title]"
3. Replace "[Chapter Title Here]" with an actual descriptive title
4. Do NOT use the word "Chapter" in descriptions or key points
5. Number chapters sequentially from 1 to {num_chapters}
6. Each chapter must have a unique, descriptive title
7. Do NOT include placeholder text like "[Chapter Title Here]" in your final output
"""
        
        try:
            logger.info(f"Generating outline for: {title}")
            outline = self._call_with_retry(prompt)
            logger.success(f"Outline generated successfully ({len(outline)} chars)")
            return outline
        except Exception as e:
            logger.error(f"Error generating outline: {e}")
            raise
    
    def regenerate_outline(self, title: str, original_outline: str, feedback_notes: str, num_chapters: int = 10) -> str:
        """
        Regenerate outline based on feedback.
        
        Args:
            title: Book title
            original_outline: Previously generated outline
            feedback_notes: Editor feedback for improvements
            num_chapters: Exact number of chapters requested
            
        Returns:
            Improved outline
        """
        prompt = f"""You are a professional book outline creator. You previously created an outline for a book, and now you need to improve it based on editor feedback.

Title: {title}

Original Outline:
{original_outline}

Editor's Feedback:
{feedback_notes}

CRITICAL REQUIREMENT: You MUST generate EXACTLY {num_chapters} chapters. Count carefully!

Revise the outline with this EXACT format:

## BOOK OVERVIEW
[Write 2-3 paragraphs overview here]

## CHAPTERS

Chapter 1: [Chapter Title Here]
Description: [2-3 sentence description]
Key Points: [bullet points]

Chapter 2: [Chapter Title Here]
Description: [2-3 sentence description]
Key Points: [bullet points]

[Continue for all {num_chapters} chapters - DO NOT generate more or fewer]

STRICT RULES YOU MUST FOLLOW:
1. Generate EXACTLY {num_chapters} chapters - no more, no fewer
2. Each chapter heading line MUST start with "Chapter [number]: [actual title]"
3. Replace "[Chapter Title Here]" with an actual descriptive title
4. Do NOT use the word "Chapter" in descriptions or key points
5. Number chapters sequentially from 1 to {num_chapters}
6. Each chapter must have a unique, descriptive title
7. Do NOT include placeholder text like "[Chapter Title Here]" in your final output
8. Address all the editor's feedback while maintaining exactly {num_chapters} chapters
"""
        
        try:
            logger.info(f"Regenerating outline for: {title}")
            outline = self._call_with_retry(prompt)
            logger.success(f"Outline regenerated successfully ({len(outline)} chars)")
            return outline
        except Exception as e:
            logger.error(f"Error regenerating outline: {e}")
            raise
    
    def generate_chapter(
        self,
        title: str,
        outline: str,
        chapter_number: int,
        chapter_title: str,
        previous_summaries: List[str],
        chapter_notes: Optional[str] = None
    ) -> str:
        """
        Generate chapter content with context from previous chapters.
        
        Args:
            title: Book title
            outline: Full book outline
            chapter_number: Current chapter number
            chapter_title: Title of current chapter
            previous_summaries: Summaries of all previous chapters
            chapter_notes: Optional editor notes for this chapter
            
        Returns:
            Generated chapter content
        """
        context = ""
        if previous_summaries:
            context = "\n\nContext from previous chapters:\n" + "\n".join(
                [f"Chapter {i+1} Summary: {summary}" 
                 for i, summary in enumerate(previous_summaries)]
            )
        
        notes_section = ""
        if chapter_notes:
            notes_section = f"\n\nEditor's Specific Requirements for this Chapter:\n{chapter_notes}"
        
        prompt = f"""You are a professional book author. Write Chapter {chapter_number} of a book based on the following information:

Book Title: {title}

Full Book Outline:
{outline}

Current Chapter: Chapter {chapter_number} - {chapter_title}
{context}
{notes_section}

Write a comprehensive, well-structured chapter that:
1. Follows the outline's guidance for this chapter
2. Maintains continuity with previous chapters (if any)
3. Is engaging and well-written
4. Includes proper transitions and flow
5. Is substantial in length (aim for 2000-3000 words)
6. Addresses all points from the editor's requirements

Begin the chapter with "# Chapter {chapter_number}: {chapter_title}" and then write the full content.
"""
        
        try:
            logger.info(f"Generating Chapter {chapter_number}: {chapter_title}")
            content = self._call_with_retry(prompt)
            logger.success(f"Chapter {chapter_number} generated ({len(content)} chars)")
            return content
        except Exception as e:
            logger.error(f"Error generating chapter {chapter_number}: {e}")
            raise
    
    def generate_chapter_summary(self, chapter_content: str, chapter_number: int, chapter_title: str) -> str:
        """
        Generate a concise summary of a chapter for context chaining.
        
        Args:
            chapter_content: Full chapter content
            chapter_number: Chapter number
            chapter_title: Chapter title
            
        Returns:
            Chapter summary (150-200 words)
        """
        prompt = f"""Summarize the following chapter in 150-200 words. Focus on:
- Main topics covered
- Key points and arguments
- Important information that would be relevant for understanding subsequent chapters

Chapter {chapter_number}: {chapter_title}

{chapter_content}

Provide a clear, concise summary:"""
        
        try:
            logger.info(f"Generating summary for Chapter {chapter_number}")
            summary = self._call_with_retry(prompt)
            logger.success(f"Summary generated for Chapter {chapter_number}")
            return summary
        except Exception as e:
            logger.error(f"Error generating summary for chapter {chapter_number}: {e}")
            raise
