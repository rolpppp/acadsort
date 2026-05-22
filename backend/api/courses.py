"""FastAPI routes for course management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json

from backend.database.engine import get_session
from backend.database.models import Course, UserSettings

router = APIRouter(prefix="/api/courses", tags=["courses"])


@router.get("/list")
async def list_courses(
    session: AsyncSession = Depends(get_session),
) -> list:
    """List all available courses for current semester."""
    result = await session.execute(select(Course))
    courses = result.scalars().all()
    
    return [
        {
            "id": c.id,
            "code": c.course_code,
            "name": c.course_name,
            "keywords": json.loads(c.keywords_json),
        }
        for c in courses
    ]


@router.get("/{course_code}")
async def get_course(
    course_code: str,
    session: AsyncSession = Depends(get_session),
):
    """Get details for a specific course."""
    result = await session.execute(
        select(Course).where(Course.course_code == course_code)
    )
    course = result.scalars().first()
    
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    return {
        "id": course.id,
        "code": course.course_code,
        "name": course.course_name,
        "instructor": course.instructor,
        "keywords": json.loads(course.keywords_json),
        "syllabus": course.syllabus_text,
    }


@router.post("/add")
async def add_course(
    code: str,
    name: str,
    keywords: Optional[List[str]] = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Add a new course."""
    try:
        # Get active semester
        result = await session.execute(
            select(UserSettings).where(UserSettings.is_active == True)
        )
        settings = result.scalars().first()
        
        if not settings:
            raise HTTPException(status_code=400, detail="No active semester")
        
        # Create course
        course = Course(
            course_code=code,
            course_name=name,
            keywords_json=json.dumps(keywords or []),
            semester_id=settings.id,
        )
        session.add(course)
        await session.commit()
        
        return {"status": "created", "course_id": course.id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{course_id}")
async def update_course(
    course_id: int,
    name: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Update course details."""
    try:
        result = await session.execute(select(Course).where(Course.id == course_id))
        course = result.scalars().first()
        
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        if name:
            course.course_name = name
        if keywords is not None:
            course.keywords_json = json.dumps(keywords)
        
        session.add(course)
        await session.commit()
        
        return {"status": "updated", "course_id": course_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{course_id}")
async def delete_course(
    course_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Delete a course."""
    try:
        result = await session.execute(select(Course).where(Course.id == course_id))
        course = result.scalars().first()
        
        if not course:
            raise HTTPException(status_code=404, detail="Course not found")
        
        await session.delete(course)
        await session.commit()
        
        return {"status": "deleted", "course_id": course_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
