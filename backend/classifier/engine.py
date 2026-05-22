"""Classifier engine using embeddings and keyword matching."""

import logging
from typing import Optional
import numpy as np

from backend.config import settings
from backend.classifier.embeddings import embed, cosine_similarity
from backend.database.models import Course

logger = logging.getLogger(__name__)


async def classify_text_to_courses(
    text: str,
    available_courses: list[Course],
    use_keyword_boost: bool = True,
) -> list[dict]:
    """
    Classify extracted text to available courses using embeddings and keyword matching.
    
    Returns a list of courses ranked by confidence scores:
    [
        {
            "course_code": "CMSC 11",
            "course_name": "Introduction to Computer Science",
            "confidence": 0.87,
            "score_embedding": 0.85,
            "score_keyword": 0.95,
            "matched_keywords": ["programming", "introduction"],
        },
        ...
    ]
    
    Args:
        text: Extracted and normalized text from the file
        available_courses: List of Course objects to match against
        use_keyword_boost: Whether to boost scores based on keyword matches
        
    Returns:
        List of courses ranked by confidence, sorted descending
    """
    if not text or not available_courses:
        logger.warning("No text or courses to classify")
        return []
    
    try:
        # Get embedding for the input text
        text_embedding = embed([text])[0]  # Returns (384,) normalized vector
        
        results = []
        
        for course in available_courses:
            # Get embeddings for course name and keywords
            course_texts = [course.name]
            if course.keywords_json:
                try:
                    import json
                    keywords = json.loads(course.keywords_json)
                    if isinstance(keywords, list):
                        course_texts.extend(keywords)
                except Exception as e:
                    logger.debug(f"Failed to parse keywords for {course.course_code}: {e}")
            
            course_embeddings = embed(course_texts)
            
            # Calculate similarity scores
            scores = [cosine_similarity(text_embedding, emb) for emb in course_embeddings]
            
            # Use max similarity (best match among course name and keywords)
            max_embedding_score = max(scores) if scores else 0.0
            
            # Keyword boosting: check if any course keywords appear in text
            keyword_score = 0.0
            matched_keywords = []
            
            if course.keywords_json and use_keyword_boost:
                try:
                    import json
                    keywords = json.loads(course.keywords_json)
                    if isinstance(keywords, list):
                        text_lower = text.lower()
                        for keyword in keywords:
                            if keyword.lower() in text_lower:
                                matched_keywords.append(keyword)
                        
                        if matched_keywords:
                            # Boost score based on number of matched keywords
                            keyword_score = min(1.0, len(matched_keywords) / max(3, len(keywords)))
                except Exception as e:
                    logger.debug(f"Failed to process keywords for {course.course_code}: {e}")
            
            # Combine embedding and keyword scores
            # Embedding: 70%, Keywords: 30% (keywords are signals but embeddings are primary)
            combined_score = (max_embedding_score * 0.7) + (keyword_score * 0.3)
            
            results.append({
                "course_code": course.course_code,
                "course_name": course.name,
                "confidence": round(combined_score, 3),
                "score_embedding": round(max_embedding_score, 3),
                "score_keyword": round(keyword_score, 3),
                "matched_keywords": matched_keywords,
            })
        
        # Sort by confidence descending
        results.sort(key=lambda x: x["confidence"], reverse=True)
        
        logger.info(f"Classification complete: top 3 matches for {len(results)} courses")
        if results:
            logger.debug(f"  Top match: {results[0]['course_code']} ({results[0]['confidence']})")
        
        return results
        
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise


async def get_top_matches(
    classification_results: list[dict],
    min_confidence: float = 0.5,
    top_n: int = 3,
) -> list[dict]:
    """
    Filter classification results to return only top matches above confidence threshold.
    
    Args:
        classification_results: Output from classify_text_to_courses()
        min_confidence: Minimum confidence score to include (0.0-1.0)
        top_n: Maximum number of results to return
        
    Returns:
        List of top matching courses
    """
    filtered = [r for r in classification_results if r["confidence"] >= min_confidence]
    return filtered[:top_n]


async def should_auto_move(confidence: float) -> bool:
    """
    Determine if a file should be automatically moved to the predicted course.
    
    Uses the confidence_auto_move threshold from settings.
    
    Args:
        confidence: Classification confidence score (0.0-1.0)
        
    Returns:
        True if confidence >= auto_move threshold
    """
    return confidence >= settings.confidence_auto_move


async def should_suggest(confidence: float) -> bool:
    """
    Determine if a file should be suggested to the user for manual review.
    
    Uses the confidence_suggest threshold from settings.
    
    Args:
        confidence: Classification confidence score (0.0-1.0)
        
    Returns:
        True if confidence >= suggest threshold
    """
    return confidence >= settings.confidence_suggest


async def batch_classify(
    texts_with_metadata: list[dict],
    available_courses: list[Course],
) -> list[dict]:
    """
    Classify multiple texts in batch for efficiency.
    
    Args:
        texts_with_metadata: List of dicts with keys:
            - text: Extracted text
            - filename: Original filename
            - file_id: Optional file identifier
        available_courses: List of available courses
        
    Returns:
        List of classification results with file metadata
    """
    results = []
    
    for item in texts_with_metadata:
        try:
            text = item.get("text", "")
            file_id = item.get("file_id")
            filename = item.get("filename", "")
            
            classification = await classify_text_to_courses(text, available_courses)
            
            top_match = classification[0] if classification else None
            
            results.append({
                "file_id": file_id,
                "filename": filename,
                "status": "success",
                "top_match": top_match,
                "all_matches": classification,
            })
        except Exception as e:
            logger.error(f"Batch classification failed for {item.get('filename')}: {e}")
            results.append({
                "file_id": item.get("file_id"),
                "filename": item.get("filename", ""),
                "status": "error",
                "error": str(e),
            })
    
    return results
