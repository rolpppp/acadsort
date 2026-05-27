"""FastAPI routes for watch folder management."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from pathlib import Path

from backend.database.engine import get_session
from backend.database.models import WatchFolder, UserSettings

router = APIRouter(prefix="/api/watch-folders", tags=["watch_folders"])


@router.post("/add")
async def add_watch_folder(
    path: str,
    semester_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
):
    """Add a new watch folder for automatic file monitoring."""
    # Validate path exists
    folder_path = Path(path).expanduser()
    if not folder_path.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Folder does not exist: {path}"
        )
    
    if not folder_path.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"Path is not a directory: {path}"
        )
    
    # Get active semester if not specified
    if semester_id is None:
        result = await session.execute(
            select(UserSettings).where(UserSettings.is_active == True)
        )
        settings = result.scalars().first()
        if not settings:
            raise HTTPException(
                status_code=400,
                detail="No active semester. Create one first."
            )
        semester_id = settings.id
    
    # Check if folder already being watched
    result = await session.execute(
        select(WatchFolder).where(
            WatchFolder.path == path,
            WatchFolder.semester_id == semester_id
        )
    )
    existing = result.scalars().first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail="This folder is already being watched"
        )
    
    # Create new watch folder
    watch_folder = WatchFolder(
        path=path,
        semester_id=semester_id,
        enabled=True
    )
    session.add(watch_folder)
    await session.commit()
    await session.refresh(watch_folder)
    
    return {
        "id": watch_folder.id,
        "path": watch_folder.path,
        "semester_id": watch_folder.semester_id,
        "enabled": watch_folder.enabled,
        "created_at": watch_folder.created_at.isoformat(),
        "updated_at": watch_folder.updated_at.isoformat(),
    }


@router.get("/list")
async def list_watch_folders(
    semester_id: Optional[int] = None,
    session: AsyncSession = Depends(get_session),
) -> list:
    """List all watch folders for a semester."""
    # Get active semester if not specified
    if semester_id is None:
        result = await session.execute(
            select(UserSettings).where(UserSettings.is_active == True)
        )
        settings = result.scalars().first()
        if not settings:
            return []  # No active semester, return empty list
        semester_id = settings.id
    
    result = await session.execute(
        select(WatchFolder).where(WatchFolder.semester_id == semester_id)
    )
    folders = result.scalars().all()
    
    return [
        {
            "id": f.id,
            "path": f.path,
            "semester_id": f.semester_id,
            "enabled": f.enabled,
            "created_at": f.created_at.isoformat(),
            "updated_at": f.updated_at.isoformat(),
        }
        for f in folders
    ]


@router.put("/{folder_id}")
async def update_watch_folder(
    folder_id: int,
    path: Optional[str] = None,
    enabled: Optional[bool] = None,
    session: AsyncSession = Depends(get_session),
):
    """Update a watch folder's settings."""
    result = await session.execute(
        select(WatchFolder).where(WatchFolder.id == folder_id)
    )
    folder = result.scalars().first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Watch folder not found")
    
    # Validate new path if provided
    if path is not None:
        folder_path = Path(path).expanduser()
        if not folder_path.exists() or not folder_path.is_dir():
            raise HTTPException(
                status_code=400,
                detail=f"Invalid path: {path}"
            )
        folder.path = path
    
    if enabled is not None:
        folder.enabled = enabled
    
    folder.updated_at = datetime.utcnow()
    session.add(folder)
    await session.commit()
    await session.refresh(folder)
    
    return {
        "id": folder.id,
        "path": folder.path,
        "semester_id": folder.semester_id,
        "enabled": folder.enabled,
        "created_at": folder.created_at.isoformat(),
        "updated_at": folder.updated_at.isoformat(),
    }


@router.delete("/{folder_id}")
async def delete_watch_folder(
    folder_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Remove a watch folder from monitoring."""
    result = await session.execute(
        select(WatchFolder).where(WatchFolder.id == folder_id)
    )
    folder = result.scalars().first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Watch folder not found")
    
    await session.delete(folder)
    await session.commit()
    
    return {"success": True, "message": "Watch folder removed"}


@router.get("/{folder_id}/status")
async def check_folder_status(
    folder_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Check the status of a watch folder."""
    result = await session.execute(
        select(WatchFolder).where(WatchFolder.id == folder_id)
    )
    folder = result.scalars().first()
    
    if not folder:
        raise HTTPException(status_code=404, detail="Watch folder not found")
    
    folder_path = Path(folder.path).expanduser()
    
    # Check if folder still exists and is accessible
    accessible = folder_path.exists() and folder_path.is_dir()
    
    # Count files in folder
    file_count = 0
    if accessible:
        try:
            file_count = len(list(folder_path.glob("*")))
        except (OSError, PermissionError):
            accessible = False
    
    return {
        "id": folder.id,
        "path": folder.path,
        "accessible": accessible,
        "enabled": folder.enabled,
        "file_count": file_count,
        "last_checked": datetime.utcnow().isoformat(),
    }
