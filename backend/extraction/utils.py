"""Utility functions for text extraction."""

import re
import logging

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """
    Normalize extracted text: fix encoding issues, collapse whitespace, etc.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Replace multiple newlines with double newline
    text = re.sub(r'\n\n+', '\n\n', text)
    
    # Replace multiple spaces with single space (but preserve newlines)
    lines = text.split('\n')
    lines = [re.sub(r' +', ' ', line.strip()) for line in lines]
    text = '\n'.join(lines)
    
    # Remove common OCR artifacts and control characters
    # Keep: letters, digits, common punctuation, spaces, newlines, accents
    text = ''.join(
        char for char in text 
        if char.isalnum() or char in ' \n\t.,-!?;:()[]{}""\'""—–' or ord(char) > 127
    )
    
    # Clean up multiple spaces again
    text = re.sub(r' +', ' ', text)
    
    return text.strip()


def clean_and_truncate(text: str, max_chars: int) -> str:
    """
    Clean text and truncate to maximum character limit.
    
    Args:
        text: Normalized text
        max_chars: Maximum number of characters to keep
        
    Returns:
        Cleaned and truncated text
    """
    if not text:
        return ""
    
    # If already under limit, return as is
    if len(text) <= max_chars:
        return text
    
    # Truncate to max_chars, trying to cut at a sentence boundary
    truncated = text[:max_chars]
    
    # Find the last period, question mark, or newline before truncation point
    for end_char in ['.', '?', '\n']:
        last_pos = truncated.rfind(end_char)
        if last_pos > max_chars * 0.8:  # At least 80% of allocated space used
            return truncated[:last_pos + 1].strip()
    
    # If no good sentence boundary found, truncate at word boundary
    last_space = truncated.rfind(' ')
    if last_space > max_chars * 0.8:
        return truncated[:last_space].strip()
    
    # Fallback: just truncate
    return truncated.strip()


def infer_material_type(text: str, filename: str = "") -> str:
    """
    Infer material type (LECTURE, ASSIGNMENT, READING, EXAM, LAB, OTHER) 
    from text content and filename.
    
    Args:
        text: Extracted text content
        filename: Original filename (optional)
        
    Returns:
        One of: LECTURE, ASSIGNMENT, READING, EXAM, LAB, OTHER
    """
    text_lower = text.lower()
    filename_lower = filename.lower()
    
    # Check for common keywords
    exam_keywords = ['exam', 'test', 'quiz', 'examination', 'final', 'midterm', 'qa', 'answer key']
    if any(kw in text_lower for kw in exam_keywords) or any(kw in filename_lower for kw in exam_keywords):
        return "EXAM"
    
    assignment_keywords = ['assignment', 'homework', 'problem set', 'exercise', 'task', 'project']
    if any(kw in text_lower for kw in assignment_keywords) or any(kw in filename_lower for kw in assignment_keywords):
        return "ASSIGNMENT"
    
    lab_keywords = ['lab', 'laboratory', 'experiment', 'practical', 'hands-on']
    if any(kw in text_lower for kw in lab_keywords) or any(kw in filename_lower for kw in lab_keywords):
        return "LAB"
    
    lecture_keywords = ['lecture', 'slides', 'presentation', 'notes', 'chapter', 'lesson', 'course material']
    if any(kw in text_lower for kw in lecture_keywords) or any(kw in filename_lower for kw in lecture_keywords):
        return "LECTURE"
    
    reading_keywords = ['reading', 'paper', 'article', 'journal', 'research', 'textbook', 'reference']
    if any(kw in text_lower for kw in reading_keywords) or any(kw in filename_lower for kw in reading_keywords):
        return "READING"
    
    return "OTHER"


def extract_week_number(text: str, filename: str = "") -> int | None:
    """
    Attempt to extract week number from text or filename.
    
    Args:
        text: Extracted text content
        filename: Original filename
        
    Returns:
        Week number (1-16) or None if not found
    """
    import re
    
    search_text = f"{filename} {text}".lower()
    
    # Look for patterns like "Week 1", "week 1", "W1", "w1", "Wk 1"
    patterns = [
        r'week\s*(\d{1,2})',
        r'wk\.\s*(\d{1,2})',
        r'w\.?(?:\s*|\s)(\d{1,2})',
        r'semana\s*(\d{1,2})',  # Spanish/Filipino
    ]
    
    for pattern in patterns:
        match = re.search(pattern, search_text)
        if match:
            week_num = int(match.group(1))
            if 1 <= week_num <= 16:
                return week_num
    
    return None


def is_valid_extracted_text(text: str, min_chars: int = 50) -> bool:
    """
    Check if extracted text is valid (not empty, not just gibberish).
    
    Args:
        text: Extracted text
        min_chars: Minimum character count to be valid
        
    Returns:
        True if text passes validation
    """
    if not text or len(text) < min_chars:
        return False
    
    # Check for reasonable character distribution (not all numbers or symbols)
    letters = sum(1 for c in text if c.isalpha())
    if letters < len(text) * 0.3:  # Less than 30% letters = probably not readable text
        return False
    
    return True
