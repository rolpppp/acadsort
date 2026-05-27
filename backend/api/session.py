"""FastAPI routes for session management."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from uuid import uuid4
import json

from backend.database.engine import get_session
from backend.database.models import Session, UserSettings

router = APIRouter(prefix="/api/session", tags=["session"])

# Session expiry time (24 hours)
SESSION_EXPIRY_HOURS = 24


@router.post("/create")
async def create_session(
    session: AsyncSession = Depends(get_session),
):
    """Create a new user session."""
    session_id = str(uuid4())
    
    new_session = Session(
        id=session_id,
        created_at=datetime.utcnow(),
        last_activity=datetime.utcnow(),
        metadata_json=json.dumps({})
    )
    session.add(new_session)
    await session.commit()
    await session.refresh(new_session)
    
    return {
        "id": session_id,
        "created_at": new_session.created_at.isoformat(),
        "last_activity": new_session.last_activity.isoformat(),
    }


@router.get("/{session_id}")
async def get_current_session(
    session_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Get details of a specific session."""
    result = await session.execute(
        select(Session).where(Session.id == session_id)
    )
    user_session = result.scalars().first()
    
    if not user_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Check if session is still valid
    expiry_time = user_session.created_at + timedelta(hours=SESSION_EXPIRY_HOURS)
    is_valid = datetime.utcnow() < expiry_time
    
    return {
        "id": user_session.id,
        "valid": is_valid,
        "created_at": user_session.created_at.isoformat(),
        "last_activity": user_session.last_activity.isoformat(),
        "semester_id": user_session.semester_id,
        "metadata": json.loads(user_session.metadata_json),
    }


@router.post("/{session_id}/verify")
async def verify_session(
    session_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Verify if a session is still valid."""
    result = await session.execute(
        select(Session).where(Session.id == session_id)
    )
    user_session = result.scalars().first()
    
    if not user_session:
        return {"valid": False, "message": "Session not found"}
    
    # Check if session is still valid
    expiry_time = user_session.created_at + timedelta(hours=SESSION_EXPIRY_HOURS)
    is_valid = datetime.utcnow() < expiry_time
    
    # Update last activity
    if is_valid:
        user_session.last_activity = datetime.utcnow()
        session.add(user_session)
        await session.commit()
    
    return {
        "valid": is_valid,
        "last_activity": user_session.last_activity.isoformat(),
        "expires_in_hours": max(0, (expiry_time - datetime.utcnow()).total_seconds() / 3600),
    }


@router.post("/{session_id}/metadata")
async def update_session_metadata(
    session_id: str,
    data: dict,
    session: AsyncSession = Depends(get_session),
):
    """Update session metadata."""
    result = await session.execute(
        select(Session).where(Session.id == session_id)
    )
    user_session = result.scalars().first()
    
    if not user_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Merge new metadata with existing
    existing_metadata = json.loads(user_session.metadata_json)
    existing_metadata.update(data)
    user_session.metadata_json = json.dumps(existing_metadata)
    user_session.last_activity = datetime.utcnow()
    
    session.add(user_session)
    await session.commit()
    await session.refresh(user_session)
    
    return {
        "updated": True,
        "metadata": json.loads(user_session.metadata_json),
    }


@router.post("/{session_id}/set-semester")
async def set_session_semester(
    session_id: str,
    semester_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Associate a session with a semester."""
    result = await session.execute(
        select(Session).where(Session.id == session_id)
    )
    user_session = result.scalars().first()
    
    if not user_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Verify semester exists
    result = await session.execute(
        select(UserSettings).where(UserSettings.id == semester_id)
    )
    semester = result.scalars().first()
    
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    
    user_session.semester_id = semester_id
    user_session.last_activity = datetime.utcnow()
    session.add(user_session)
    await session.commit()
    
    return {"updated": True, "semester_id": semester_id}


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete/invalidate a session."""
    result = await session.execute(
        select(Session).where(Session.id == session_id)
    )
    user_session = result.scalars().first()
    
    if not user_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await session.delete(user_session)
    await session.commit()
    
    return {"success": True, "message": "Session deleted"}
