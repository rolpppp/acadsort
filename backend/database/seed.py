"""Database seeding with UP Tacloban courses."""

import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import select

from backend.config import settings
from backend.database.engine import AsyncSessionLocal, init_db
from backend.database.models import Course, UserSettings

logger = logging.getLogger(__name__)


async def load_courses_from_json(json_path: Path) -> list[dict]:
    """
    Load courses from UP Tacloban seed data JSON.
    
    Args:
        json_path: Path to courses JSON file
        
    Returns:
        List of course dicts with course_code, name, keywords
    """
    with open(json_path) as f:
        data = json.load(f)
    
    courses = []
    
    for dept_name, dept_structure in data.get("departments", {}).items():
        for subdept_name, subdept_data in dept_structure.items():
            if isinstance(subdept_data, dict) and "courses" in subdept_data:
                for course in subdept_data["courses"]:
                    course["keywords_json"] = json.dumps(course.get("keywords", []))
                    courses.append(course)
    
    logger.info(f"Loaded {len(courses)} courses from JSON")
    return courses


async def seed_database():
    """
    Initialize and seed database with UP Tacloban courses.
    
    Call on app startup.
    """
    try:
        # Initialize database (create tables)
        await init_db()
        logger.info("Database tables initialized")
        
        # Create default user settings first (courses depend on this)
        settings_id = None
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserSettings))
            settings_obj = result.scalars().first()
            
            if not settings_obj:
                settings_obj = UserSettings(
                    semester_name="Current Semester",
                    organization_style="week",
                    confidence_auto=0.90,
                    confidence_suggest=0.70,
                    is_active=True,
                )
                session.add(settings_obj)
                await session.commit()
                logger.info("Created default user settings")
                settings_id = settings_obj.id
            else:
                settings_id = settings_obj.id
        
        # Check if already seeded
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Course))
            existing = result.scalars().all()
            
            if existing:
                logger.info(f"Database already seeded ({len(existing)} courses)")
                return
        
        # Load courses from JSON
        courses_path = settings.data_dir / "up_tacloban_courses.json"
        course_dicts = await load_courses_from_json(courses_path)
        
        # Seed courses with semester_id
        async with AsyncSessionLocal() as session:
            for course_dict in course_dicts:
                course = Course(
                    course_code=course_dict.get("code", ""),
                    course_name=course_dict.get("name", ""),
                    keywords_json=course_dict.get("keywords_json", "[]"),
                    semester_id=settings_id,
                )
                session.add(course)
            
            await session.commit()
            logger.info(f"Seeded {len(course_dicts)} courses")
        
    except Exception as e:
        logger.error(f"Failed to seed database: {e}")
        raise


async def reset_database():
    """
    Drop all tables and reseed.
    
    Use with caution!
    """
    try:
        from backend.database.engine import sync_engine
        from backend.database.models import SQLModel
        
        # Drop all tables
        SQLModel.metadata.drop_all(sync_engine)
        logger.info("Dropped all database tables")
        
        # Reseed
        await seed_database()
        logger.info("Database reset and reseeded")
        
    except Exception as e:
        logger.error(f"Failed to reset database: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(seed_database())
