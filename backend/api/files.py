"""FastAPI routes for file management."""

import asyncio
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.database.engine import get_session
from backend.database.models import FileRecord, Course
from backend.watcher.pipeline import get_pipeline, ProcessingPipeline
from backend.extraction.utils import is_valid_extracted_text

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Upload and classify a file.
    
    Returns:
        - auto_moved: File auto-moved to course folder
        - suggest: File classified, awaiting user confirmation
        - review_queue: File needs manual review
    """
    import tempfile
    from pathlib import Path
    
    try:
        # Save upload to temp
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Load courses for classification
        result = await session.execute(select(Course))
        courses = result.scalars().all()
        
        if not courses:
            raise HTTPException(status_code=400, detail="No courses configured")
        
        # Process file through pipeline
        pipeline = get_pipeline()
        result = await pipeline.process_file(tmp_path, courses)
        
        # Create file record
        file_record = FileRecord(
            original_name=file.filename,
            detected_course=result.get("course_code"),
            material_type=result.get("material_type", "OTHER"),
            week_number=result.get("week_number"),
            confidence=result.get("confidence", 0.0),
            status="PENDING",
        )
        session.add(file_record)
        await session.commit()
        
        return {
            "status": result["status"],
            "file_id": file_record.id,
            "course": result.get("course_code"),
            "confidence": result.get("confidence", 0.0),
            "message": result.get("message", "File processed"),
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list")
async def list_files(
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
) -> list:
    """List recent file records."""
    result = await session.execute(
        select(FileRecord).order_by(FileRecord.id.desc()).limit(limit)
    )
    files = result.scalars().all()
    
    return [
        {
            "id": f.id,
            "name": f.original_name,
            "course": f.detected_course,
            "material_type": f.material_type,
            "week": f.week_number,
            "confidence": f.confidence,
            "status": f.status,
        }
        for f in files
    ]


@router.post("/confirm")
async def confirm_file(
    file_id: int,
    course_code: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Confirm classification and move file."""
    try:
        # Get file record
        result = await session.execute(select(FileRecord).where(FileRecord.id == file_id))
        file_record = result.scalars().first()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Update record
        file_record.detected_course = course_code
        file_record.status = "CONFIRMED"
        session.add(file_record)
        await session.commit()
        
        return {"status": "confirmed", "file_id": file_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reject")
async def reject_file(
    file_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Reject file classification."""
    try:
        result = await session.execute(select(FileRecord).where(FileRecord.id == file_id))
        file_record = result.scalars().first()
        
        if not file_record:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_record.status = "REJECTED"
        session.add(file_record)
        await session.commit()
        
        return {"status": "rejected", "file_id": file_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
