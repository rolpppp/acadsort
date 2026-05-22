"""LLM fallback classifier using Ollama for low-confidence predictions."""

import asyncio
import logging
from typing import Optional

import httpx

from backend.config import settings
from backend.database.models import Course

logger = logging.getLogger(__name__)


class OllamaClassifier:
    """
    Fallback classifier using Ollama local LLM.
    
    Used when embedding-based classifier has low confidence or for validation.
    """
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.model = settings.ollama_model_name
        self.timeout = settings.ollama_timeout_seconds
        self.available = False
    
    async def check_availability(self) -> bool:
        """
        Check if Ollama service is running and accessible.
        
        Returns:
            True if Ollama is available
        """
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                self.available = response.status_code == 200
                if self.available:
                    logger.info("Ollama service is available")
                else:
                    logger.warning(f"Ollama returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"Ollama service not available: {e}")
            self.available = False
        
        return self.available
    
    async def classify_with_retries(
        self,
        text: str,
        available_courses: list[Course],
        max_retries: int = 3,
    ) -> Optional[dict]:
        """
        Classify text using LLM with retry logic.
        
        Args:
            text: Extracted text to classify
            available_courses: List of available courses
            max_retries: Number of retry attempts
            
        Returns:
            Classification result dict or None if failed
        """
        if not self.available:
            await self.check_availability()
        
        if not self.available:
            logger.warning("Skipping LLM classification: Ollama not available")
            return None
        
        # Limit text to reasonable size for LLM
        text_preview = text[:2000]
        
        # Build course list for the prompt
        course_list = "\n".join(
            [f"- {c.course_code}: {c.name}" for c in available_courses[:20]]  # Top 20 courses
        )
        
        prompt = self._build_classification_prompt(text_preview, course_list)
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"LLM classification attempt {attempt + 1}/{max_retries}")
                
                async with httpx.AsyncClient(timeout=self.timeout + 10) as client:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "stream": False,
                            "temperature": 0.1,  # Low temperature for deterministic output
                        },
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    extracted_code = self._parse_course_code(result.get("response", ""))
                    
                    if extracted_code:
                        return {
                            "course_code": extracted_code,
                            "confidence": 0.65,  # LLM fallback gets fixed confidence
                            "source": "ollama",
                            "raw_response": result.get("response", ""),
                        }
                    
                    logger.warning("LLM response didn't contain valid course code")
                else:
                    logger.warning(f"LLM request failed with status {response.status_code}")
            
            except asyncio.TimeoutError:
                logger.warning(f"LLM classification timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Brief backoff
                continue
            except Exception as e:
                logger.error(f"LLM classification error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                continue
        
        logger.warning(f"LLM classification failed after {max_retries} attempts")
        return None
    
    def _build_classification_prompt(self, text: str, course_list: str) -> str:
        """
        Build a prompt for the LLM to classify the text.
        
        Returns:
            Formatted prompt string
        """
        return f"""You are an academic course classifier. Given a document excerpt and a list of UP Tacloban courses, determine which course the document most likely belongs to.

DOCUMENT EXCERPT:
{text}

AVAILABLE COURSES:
{course_list}

Answer with ONLY the course code (e.g., "CMSC 11") that best matches the document. If unsure, choose the most likely course. Do not explain your answer."""
    
    def _parse_course_code(self, response: str) -> Optional[str]:
        """
        Extract course code from LLM response.
        
        Args:
            response: Raw LLM response text
            
        Returns:
            Extracted course code (e.g., "CMSC 11") or None
        """
        import re
        
        response_upper = response.strip().upper()
        
        # Look for course code pattern: 4 letters + space + 1-3 digits
        match = re.search(r'([A-Z]{2,4})\s*(\d{1,3})', response_upper)
        if match:
            return f"{match.group(1)} {match.group(2)}"
        
        # Look for just the code at the start
        parts = response_upper.split()
        if len(parts) >= 2:
            if parts[0].isalpha() and parts[1].isdigit():
                return f"{parts[0]} {parts[1]}"
        
        return None


# Global singleton instance
_ollama_classifier: Optional[OllamaClassifier] = None


def get_ollama_classifier() -> OllamaClassifier:
    """
    Get the global Ollama classifier instance.
    
    Returns:
        OllamaClassifier singleton
    """
    global _ollama_classifier
    if _ollama_classifier is None:
        _ollama_classifier = OllamaClassifier()
    return _ollama_classifier


async def validate_with_llm(
    text: str,
    predicted_course_code: str,
    available_courses: list[Course],
) -> bool:
    """
    Validate a prediction using the LLM.
    
    Uses LLM to double-check if a course prediction makes sense.
    
    Args:
        text: Original extracted text
        predicted_course_code: Course code predicted by embeddings
        available_courses: List of available courses
        
    Returns:
        True if LLM agrees with the prediction
    """
    classifier = get_ollama_classifier()
    
    text_preview = text[:1500]
    courses_list = "\n".join([f"- {c.course_code}: {c.name}" for c in available_courses[:20]])
    
    prompt = f"""You are validating a course classification.

DOCUMENT EXCERPT:
{text_preview}

PREDICTED COURSE: {predicted_course_code}

AVAILABLE COURSES:
{courses_list}

Is {predicted_course_code} a reasonable course for this document? Answer with only "YES" or "NO"."""
    
    try:
        async with httpx.AsyncClient(timeout=classifier.timeout + 10) as client:
            response = await client.post(
                f"{classifier.base_url}/api/generate",
                json={
                    "model": classifier.model,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,
                },
            )
        
        if response.status_code == 200:
            result_text = response.json().get("response", "").strip().upper()
            return "YES" in result_text
    except Exception as e:
        logger.warning(f"LLM validation failed: {e}")
    
    return True  # Assume valid if LLM unavailable
