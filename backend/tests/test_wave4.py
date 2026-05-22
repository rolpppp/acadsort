"""Integration tests for Wave 4: Database & Data Models."""

import asyncio
import json
from pathlib import Path

try:
    import pytest
    pytest_available = True
except ImportError:
    pytest_available = False


@pytest.mark.asyncio
async def test_database_initialization():
    """Test 1: Database initializes and creates tables."""
    from backend.database.engine import init_db, AsyncSessionLocal
    from backend.database.models import Course
    from sqlalchemy import select
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        # Should be able to query
        result = await session.execute(select(Course))
        courses = result.scalars().all()
        
        # Should be a list (possibly empty)
        assert isinstance(courses, list)
    
    print("✅ Passed: Database initialization")


@pytest.mark.asyncio
async def test_course_crud():
    """Test 2: CRUD operations on courses."""
    from backend.database.engine import init_db, AsyncSessionLocal
    from backend.database.models import Course, UserSettings
    from sqlalchemy import select
    
    await init_db()
    
    # First create user settings (courses need this FK)
    settings_id = None
    async with AsyncSessionLocal() as session:
        settings = UserSettings(
            semester_name="Test Semester",
            organization_style="week",
            confidence_auto=0.90,
            confidence_suggest=0.70,
            is_active=True,
        )
        session.add(settings)
        await session.commit()
        settings_id = settings.id
    
    # Create
    async with AsyncSessionLocal() as session:
        course = Course(
            course_code="TEST 99",
            course_name="Test Course",
            keywords_json=json.dumps(["test", "keyword"]),
            semester_id=settings_id,
        )
        session.add(course)
        await session.commit()
    
    # Read
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Course).where(Course.course_code == "TEST 99")
        )
        found = result.scalars().first()
        
        assert found is not None
        assert found.course_name == "Test Course"
    
    # Update
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Course).where(Course.course_code == "TEST 99")
        )
        found = result.scalars().first()
        found.course_name = "Updated Test Course"
        await session.commit()
    
    # Verify update
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Course).where(Course.course_code == "TEST 99")
        )
        found = result.scalars().first()
        assert found.course_name == "Updated Test Course"
    
    # Delete
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Course).where(Course.course_code == "TEST 99")
        )
        found = result.scalars().first()
        await session.delete(found)
        await session.commit()
    
    # Verify delete
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Course).where(Course.course_code == "TEST 99")
        )
        found = result.scalars().first()
        assert found is None
    
    print("✅ Passed: Course CRUD operations")


@pytest.mark.asyncio
async def test_database_seed():
    """Test 3: Database seeding with UP Tacloban courses."""
    from backend.database.engine import init_db, AsyncSessionLocal
    from backend.database.models import Course
    from backend.database.seed import seed_database
    from sqlalchemy import select, func
    
    await seed_database()
    
    # Check courses were loaded
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count(Course.id)))
        count = result.scalar()
        
        assert count > 50, f"Expected >50 courses, got {count}"
        
        # Check for specific CMSC courses
        result = await session.execute(
            select(Course).where(Course.course_code.like("CMSC%"))
        )
        cmsc_courses = result.scalars().all()
        assert len(cmsc_courses) > 0
    
    print(f"✅ Passed: Database seeding ({count} courses)")


@pytest.mark.asyncio
async def test_foreign_key_relationships():
    """Test 4: Foreign key relationships work."""
    from backend.database.engine import init_db, AsyncSessionLocal
    from backend.database.models import Course, FileRecord, UserSettings
    from sqlalchemy import select
    
    await init_db()
    
    # Create user settings
    async with AsyncSessionLocal() as session:
        settings = UserSettings(
            semester_name="Test Semester",
            organization_style="week",
            confidence_auto=0.90,
            confidence_suggest=0.70,
            is_active=True,
        )
        session.add(settings)
        await session.commit()
        settings_id = settings.id
    
    # Create course
    async with AsyncSessionLocal() as session:
        course = Course(
            course_code="FK TEST",
            course_name="Foreign Key Test",
            semester_id=settings_id,
        )
        session.add(course)
        await session.commit()
        course_id = course.id
    
    # Create file record with foreign key (unique name avoids stale rows in shared DB)
    test_filename = "fk_test_relationship.pdf"
    async with AsyncSessionLocal() as session:
        file_record = FileRecord(
            original_name=test_filename,
            detected_course="FK TEST",
            material_type="LECTURE",
            week_number=1,
            confidence=0.95,
            status="CONFIRMED",
            semester_id=settings_id,
        )
        session.add(file_record)
        await session.commit()
        file_id = file_record.id
    
    # Verify relationships
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(FileRecord).where(FileRecord.id == file_id)
        )
        file_rec = result.scalars().one()
        assert file_rec.semester_id == settings_id
        assert file_rec.detected_course == "FK TEST"
    
    print("✅ Passed: Foreign key relationships")


@pytest.mark.asyncio
async def test_user_settings_crud():
    """Test 5: UserSettings CRUD operations."""
    from backend.database.engine import init_db, AsyncSessionLocal
    from backend.database.models import UserSettings
    from sqlalchemy import select
    
    await init_db()
    
    # Create
    async with AsyncSessionLocal() as session:
        settings = UserSettings(
            semester_name="Test Semester",
            organization_style="type",
            confidence_auto=0.85,
            confidence_suggest=0.65,
            is_active=True,
        )
        session.add(settings)
        await session.commit()
        settings_id = settings.id
    
    # Read
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserSettings).where(UserSettings.id == settings_id))
        found = result.scalars().first()
        assert found is not None
        assert found.organization_style == "type"
    
    print("✅ Passed: UserSettings CRUD operations")


async def manual_test_suite():
    """Run all tests manually."""
    print("\n🧪 WAVE 4: Database & Data Models Tests\n")
    
    tests = [
        ("Database Initialization", test_database_initialization),
        ("Course CRUD Operations", test_course_crud),
        ("Database Seeding", test_database_seed),
        ("Foreign Key Relationships", test_foreign_key_relationships),
        ("UserSettings CRUD", test_user_settings_crud),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"Running: {test_name}...", end=" ", flush=True)
            await test_func()
            passed += 1
        except ImportError as e:
            print(f"⏭️  SKIPPED: {e}")
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed\n")
    return failed == 0


if __name__ == "__main__":
    asyncio.run(manual_test_suite())
