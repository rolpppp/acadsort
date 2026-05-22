"""FastAPI routes for file review queue."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json

from backend.database.engine import get_session
from backend.database.models import FileRecord

router = APIRouter(prefix="/api/queue", tags=["queue"])


@router.get("/pending")
async def get_pending_files(
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
) -> list:
    """Get pending files awaiting user review/confirmation."""
    result = await session.execute(
        select(FileRecord)
        .where(FileRecord.status == "PENDING")
        .order_by(FileRecord.id.desc())
        .limit(limit)
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
            "snippet": f.snippet,
        }
        for f in files
    ]


@router.get("/auto-moved")
async def get_auto_moved_files(
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
) -> list:
    """Get files that were auto-moved."""
    result = await session.execute(
        select(FileRecord)
        .where(FileRecord.status.in_(["AUTO_MOVED", "CONFIRMED"]))
        .order_by(FileRecord.id.desc())
        .limit(limit)
    )
    files = result.scalars().all()
    
    return [
        {
            "id": f.id,
            "name": f.original_name,
            "course": f.detected_course,
            "status": f.status,
        }
        for f in files
    ]


@router.get("/stats")
async def get_queue_stats(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get statistics on file processing."""
    from sqlalchemy import func
    
    # Count by status
    statuses = {}
    for status in ["PENDING", "AUTO_MOVED", "CONFIRMED", "REJECTED"]:
        result = await session.execute(
            select(func.count(FileRecord.id)).where(FileRecord.status == status)
        )
        statuses[status.lower()] = result.scalar()
    
    # Total confidence average for pending
    result = await session.execute(
        select(func.avg(FileRecord.confidence)).where(FileRecord.status == "PENDING")
    )
    avg_confidence = result.scalar() or 0.0
    
    return {
        "total_pending": statuses.get("pending", 0),
        "total_confirmed": statuses.get("confirmed", 0),
        "total_rejected": statuses.get("rejected", 0),
        "avg_confidence": float(avg_confidence),
    }
