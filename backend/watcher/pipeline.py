"""End-to-end file processing pipeline."""

import asyncio
import logging
from pathlib import Path
from typing import Optional, Callable

from backend.config import settings
from backend.extraction.pdf import extract_text_from_pdf
from backend.extraction.docx import extract_text_from_docx
from backend.extraction.pptx import extract_text_from_pptx
from backend.extraction.utils import (
    is_valid_extracted_text,
    infer_material_type,
    extract_week_number,
)
from backend.classifier.engine import classify_text_to_courses, should_auto_move, should_suggest
from backend.organizer.mover import get_organizer

logger = logging.getLogger(__name__)


class ProcessingPipeline:
    """Orchestrates extraction, classification, and organization."""
    
    # File extension to extractor mapping
    EXTRACTORS = {
        ".pdf": extract_text_from_pdf,
        ".docx": extract_text_from_docx,
        ".doc": extract_text_from_docx,  # Older format
        ".pptx": extract_text_from_pptx,
        ".ppt": extract_text_from_pptx,  # Older format
    }
    
    def __init__(
        self,
        on_auto_move: Optional[Callable] = None,
        on_suggest: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
    ):
        """
        Initialize pipeline.
        
        Args:
            on_auto_move: Callback when file auto-moves
            on_suggest: Callback when file needs user review
            on_error: Callback when error occurs
        """
        self.on_auto_move = on_auto_move
        self.on_suggest = on_suggest
        self.on_error = on_error
        self.organizer = get_organizer()
    
    async def process_file(
        self,
        file_path: str,
        available_courses: list,
        user_settings=None,
    ) -> dict:
        """
        Process a single file: extract → classify → organize.
        
        Args:
            file_path: Path to file
            available_courses: List of Course objects to classify against
            user_settings: User preference settings
            
        Returns:
            Processing result dict with status and details
        """
        try:
            file_path = Path(file_path)
            logger.info(f"Processing file: {file_path.name}")
            
            # Step 1: Validate file
            if not file_path.exists():
                return self._error_result(f"File not found: {file_path}")
            
            file_size_mb = file_path.stat().st_size / 1024 / 1024
            if file_size_mb > settings.max_file_size_mb:
                return self._error_result(
                    f"File too large: {file_size_mb:.1f}MB (max: {settings.max_file_size_mb}MB)"
                )
            
            # Step 2: Extract text
            text = await self._extract_text(file_path)
            if not text:
                return self._error_result("No text extracted from file")
            
            if not is_valid_extracted_text(text):
                return self._error_result("Extracted text not readable")
            
            logger.debug(f"Extracted {len(text)} chars from {file_path.name}")
            
            # Step 3: Classify
            classification_results = await self._classify(text, available_courses)
            if not classification_results:
                return self._error_result("Classification failed")
            
            top_match = classification_results[0]
            confidence = top_match["confidence"]
            
            logger.info(
                f"Classification: {top_match['course_code']} "
                f"(confidence: {confidence:.2f})"
            )
            
            # Step 4: Infer metadata
            material_type = infer_material_type(text, file_path.name)
            week_number = extract_week_number(text, file_path.name)
            
            # Step 5: Decide action based on confidence
            if await should_auto_move(confidence):
                logger.info("Auto-moving file (confidence >= 0.90)")
                
                destination = await self.organizer.organize_file(
                    file_path,
                    top_match["course_code"],
                    material_type,
                    week_number,
                )
                
                if destination:
                    if self.on_auto_move:
                        await self.on_auto_move({
                            "filename": file_path.name,
                            "course": top_match["course_code"],
                            "destination": str(destination),
                        })
                    
                    return {
                        "status": "auto_moved",
                        "filename": file_path.name,
                        "course_code": top_match["course_code"],
                        "confidence": confidence,
                        "destination": str(destination),
                        "material_type": material_type,
                        "week_number": week_number,
                    }
                else:
                    return self._error_result("Failed to move file")
            
            elif await should_suggest(confidence):
                logger.info("Suggesting file for user review (0.70 <= confidence < 0.90)")
                
                if self.on_suggest:
                    await self.on_suggest({
                        "filename": file_path.name,
                        "course": top_match["course_code"],
                        "confidence": confidence,
                        "alternatives": classification_results[1:3],
                    })
                
                return {
                    "status": "suggest_to_user",
                    "filename": file_path.name,
                    "course_code": top_match["course_code"],
                    "confidence": confidence,
                    "alternatives": classification_results[1:3],
                    "material_type": material_type,
                    "week_number": week_number,
                }
            
            else:
                logger.info("Moving to review queue (confidence < 0.70)")
                
                return {
                    "status": "review_queue",
                    "filename": file_path.name,
                    "course_code": top_match["course_code"],
                    "confidence": confidence,
                    "alternatives": classification_results[1:3],
                    "material_type": material_type,
                    "week_number": week_number,
                    "reason": f"Low confidence: {confidence:.2f}",
                }
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}", exc_info=True)
            if self.on_error:
                await self.on_error({"filename": file_path.name, "error": str(e)})
            return self._error_result(str(e))
    
    async def _extract_text(self, file_path: Path) -> Optional[str]:
        """Extract text from file based on extension."""
        try:
            ext = file_path.suffix.lower()
            
            if ext not in self.EXTRACTORS:
                logger.warning(f"Unsupported file type: {ext}")
                return None
            
            extractor = self.EXTRACTORS[ext]
            text = await extractor(str(file_path))
            
            return text
            
        except Exception as e:
            logger.error(f"Extraction error for {file_path}: {e}")
            return None
    
    async def _classify(self, text: str, available_courses: list) -> Optional[list]:
        """Classify text against courses."""
        try:
            results = await classify_text_to_courses(text, available_courses)
            return results
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return None
    
    def _error_result(self, message: str) -> dict:
        """Create error result dict."""
        logger.error(f"Processing error: {message}")
        return {
            "status": "error",
            "error": message,
        }
    
    async def batch_process(
        self,
        file_paths: list[str],
        available_courses: list,
        max_concurrent: int = 3,
    ) -> list[dict]:
        """
        Process multiple files concurrently.
        
        Args:
            file_paths: List of file paths
            available_courses: List of courses
            max_concurrent: Max concurrent processes
            
        Returns:
            List of processing results
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(path):
            async with semaphore:
                return await self.process_file(path, available_courses)
        
        tasks = [process_with_semaphore(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r if isinstance(r, dict) else {"status": "error", "error": str(r)} for r in results]


# Global singleton
_pipeline: Optional[ProcessingPipeline] = None


def get_pipeline() -> ProcessingPipeline:
    """Get global pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = ProcessingPipeline()
    return _pipeline
