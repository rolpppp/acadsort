"""FastAPI routes for user settings."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import get_session
from backend.database.models import UserSettings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/current")
async def get_current_settings(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get current active semester settings."""
    result = await session.execute(
        select(UserSettings).where(UserSettings.is_active == True)
    )
    settings = result.scalars().first()
    
    if not settings:
        raise HTTPException(status_code=404, detail="No active semester configured")
    
    return {
        "id": settings.id,
        "semester_name": settings.semester_name,
        "organization_style": settings.organization_style,
        "downloads_path": settings.downloads_path,
        "confidence_auto": settings.confidence_auto,
        "confidence_suggest": settings.confidence_suggest,
    }


@router.put("/current")
async def update_current_settings(
    semester_name: Optional[str] = None,
    organization_style: Optional[str] = None,
    confidence_auto: Optional[float] = None,
    confidence_suggest: Optional[float] = None,
    session: Session = Depends(get_session),
) -> dict:
    """Update current active semester settings."""
    try:
        result = await session.execute(
            select(UserSettings).where(UserSettings.is_active == True)
        )
        settings = result.scalars().first()
        
        if not settings:
            raise HTTPException(status_code=404, detail="No active semester")
        
        if semester_name:
            settings.semester_name = semester_name
        if organization_style:
            settings.organization_style = organization_style
        if confidence_auto is not None:
            settings.confidence_auto = confidence_auto
        if confidence_suggest is not None:
            settings.confidence_suggest = confidence_suggest
        
        session.add(settings)
        await session.commit()
        
        return {"status": "updated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create-semester")
async def create_semester(
    semester_name: str,
    organization_style: str = "week",
    confidence_auto: float = 0.90,
    confidence_suggest: float = 0.70,
    session: Session = Depends(get_session),
) -> dict:
    """Create new semester (deactivates previous ones)."""
    try:
        # Deactivate all current settings
        result = await session.execute(select(UserSettings))
        all_settings = result.scalars().all()
        for s in all_settings:
            s.is_active = False
            session.add(s)
        
        # Create new semester
        new_settings = UserSettings(
            semester_name=semester_name,
            organization_style=organization_style,
            confidence_auto=confidence_auto,
            confidence_suggest=confidence_suggest,
            is_active=True,
        )
        session.add(new_settings)
        await session.commit()
        
        return {"status": "created", "semester_id": new_settings.id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list-semesters")
async def list_semesters(
    session: Session = Depends(get_session),
) -> list:
    """List all configured semesters."""
    result = await session.execute(select(UserSettings).order_by(UserSettings.id.desc()))
    semesters = result.scalars().all()
    
    return [
        {
            "id": s.id,
            "semester_name": s.semester_name,
            "is_active": s.is_active,
            "organization_style": s.organization_style,
        }
        for s in semesters
    ]
