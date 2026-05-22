"""PDF text extraction using PyMuPDF."""

import logging
from pathlib import Path

import fitz  # PyMuPDF

from backend.config import settings
from backend.extraction.utils import clean_and_truncate, normalize_text

logger = logging.getLogger(__name__)


async def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted and cleaned text, truncated to max chars
        
    Raises:
        ValueError: If file cannot be read or is corrupted
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise ValueError(f"PDF file not found: {file_path}")
        
        if file_path.stat().st_size > settings.max_file_size_mb * 1024 * 1024:
            raise ValueError(
                f"PDF file too large: {file_path.stat().st_size / 1024 / 1024:.1f}MB "
                f"(max: {settings.max_file_size_mb}MB)"
            )
        
        logger.info(f"Extracting text from PDF: {file_path}")
        
        doc = fitz.open(file_path)
        text_parts = []
        
        for page_num, page in enumerate(doc):
            try:
                text = page.get_text("text")
                if text.strip():
                    text_parts.append(text)
            except Exception as e:
                logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                continue
        
        doc.close()
        
        full_text = "\n".join(text_parts)
        
        if not full_text.strip():
            raise ValueError("No text could be extracted from PDF")
        
        # Normalize and truncate
        normalized = normalize_text(full_text)
        cleaned = clean_and_truncate(normalized, settings.extraction_max_chars)
        
        logger.info(
            f"PDF extraction complete: {len(cleaned)} chars from {len(text_parts)} pages"
        )
        
        return cleaned
        
    except Exception as e:
        logger.error(f"PDF extraction failed for {file_path}: {e}")
        raise


async def extract_text_from_pdf_with_metadata(file_path: str) -> dict:
    """
    Extract text and metadata from a PDF file.
    
    Returns dict with keys:
        - text: Extracted text
        - page_count: Number of pages
        - title: PDF title (if available)
        - author: PDF author (if available)
    """
    try:
        file_path = Path(file_path)
        doc = fitz.open(file_path)
        
        # Extract metadata
        metadata = doc.metadata or {}
        
        text_parts = []
        for page in doc:
            text = page.get_text("text")
            if text.strip():
                text_parts.append(text)
        
        doc.close()
        
        full_text = "\n".join(text_parts)
        normalized = normalize_text(full_text)
        cleaned = clean_and_truncate(normalized, settings.extraction_max_chars)
        
        return {
            "text": cleaned,
            "page_count": len(doc),
            "title": metadata.get("title", ""),
            "author": metadata.get("author", ""),
        }
        
    except Exception as e:
        logger.error(f"PDF metadata extraction failed for {file_path}: {e}")
        raise
