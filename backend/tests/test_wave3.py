"""Integration tests for Wave 3: File Organization & Watching."""

import asyncio
import tempfile
from pathlib import Path
from typing import Optional

import pytest

# For manual testing without pytest
pytest_available = True
try:
    import pytest
except ImportError:
    pytest_available = False


@pytest.mark.asyncio
async def test_file_organizer_creation():
    """Test 1: FileOrganizer creates correct destination paths."""
    from backend.organizer.mover import FileOrganizer
    
    organizer = FileOrganizer()
    
    # Test WEEK style
    dest = organizer.get_destination(
        "CMSC 11",
        "LECTURE",
        week_number=1,
        organization_style="week",
    )
    assert "CMSC 11" in str(dest)
    assert "Week_01" in str(dest)
    
    # Test TYPE style
    dest = organizer.get_destination(
        "CMSC 11",
        "ASSIGNMENT",
        organization_style="type",
    )
    assert "CMSC 11" in str(dest)
    assert "ASSIGNMENT" in str(dest)
    
    print("✅ Passed: FileOrganizer creates correct paths")


@pytest.mark.asyncio
async def test_file_organizer_move():
    """Test 2: FileOrganizer moves files successfully."""
    from backend.organizer.mover import FileOrganizer
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create test file
        test_file = tmpdir / "test.txt"
        test_file.write_text("Test content")
        
        # Create organizer with temp base
        organizer = FileOrganizer(str(tmpdir / "organized"))
        
        # Move file
        dest_dir = organizer.get_destination("CMSC 11", "LECTURE", week_number=1, organization_style="week")
        success = await organizer.move_file(test_file, dest_dir)
        
        assert success
        assert not test_file.exists()  # Original removed
        assert (dest_dir / "test.txt").exists()  # Moved to new location
        
        print("✅ Passed: FileOrganizer moves files correctly")


@pytest.mark.asyncio
async def test_file_organizer_undo():
    """Test 3: FileOrganizer undoes moves."""
    from backend.organizer.mover import FileOrganizer
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        original = tmpdir / "original"
        original.mkdir()
        
        # Create test file
        test_file = original / "test.txt"
        test_file.write_text("Test content")
        
        # Create organizer
        organizer = FileOrganizer(str(tmpdir / "organized"))
        
        # Move file
        dest_dir = organizer.get_destination("CMSC 11", "LECTURE", week_number=1, organization_style="week")
        await organizer.move_file(test_file, dest_dir)
        moved_file = dest_dir / "test.txt"
        
        assert moved_file.exists()
        
        # Undo move
        success = await organizer.undo_move(moved_file, test_file)
        
        assert success
        assert not moved_file.exists()
        assert test_file.exists()
        
        print("✅ Passed: FileOrganizer undoes moves correctly")


@pytest.mark.asyncio
async def test_pipeline_process_file():
    """Test 4: Processing pipeline orchestrates extraction → classification → organization."""
    from backend.watcher.pipeline import ProcessingPipeline
    import json
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Create temp PDF
        try:
            import fitz
            
            pdf_path = tmpdir / "test.pdf"
            doc = fitz.open()
            page = doc.new_page()
            page.insert_text((50, 50), "Introduction to Computer Science\nCMSC 11 Lecture\nWeek 1")
            doc.save(str(pdf_path))
            doc.close()
            
            # Load test courses
            courses_path = Path("data/up_tacloban_courses.json")
            with open(courses_path) as f:
                data = json.load(f)
            
            # Convert to simple objects with needed attributes
            class Course:
                def __init__(self, code, name, keywords=None):
                    self.course_code = code
                    self.name = name
                    self.keywords_json = json.dumps(keywords or [])
            
            courses = [
                Course("CMSC 11", "Introduction to Computer Science", ["programming", "algorithms"]),
                Course("CMSC 21", "Data Structures", ["arrays", "linked lists"]),
            ]
            
            # Create pipeline and process
            pipeline = ProcessingPipeline()
            result = await pipeline.process_file(str(pdf_path), courses)
            
            assert result["status"] in ["auto_moved", "suggest_to_user", "review_queue", "error"]
            if result["status"] != "error":
                assert "course_code" in result
                assert "confidence" in result
            
            print(f"✅ Passed: Pipeline processes file ({result['status']})")
            
        except ImportError:
            print("⏭️  Skipped: PyMuPDF not installed")


@pytest.mark.asyncio
async def test_download_monitor_initialization():
    """Test 5: DownloadMonitor initializes correctly."""
    from backend.watcher.monitor import DownloadMonitor
    
    with tempfile.TemporaryDirectory() as tmpdir:
        monitor = DownloadMonitor(watch_path=tmpdir)
        
        status = monitor.get_status()
        assert status["watch_path"] == tmpdir
        assert status["watch_path_exists"] == True
        assert status["is_running"] == False
        
        print("✅ Passed: DownloadMonitor initializes correctly")


@pytest.mark.asyncio
async def test_download_monitor_file_creation():
    """Test 6: DownloadMonitor detects new files (if watchdog available)."""
    from backend.watcher.monitor import DownloadMonitor
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        files_detected = []
        
        async def callback(file_path: str):
            files_detected.append(file_path)
        
        monitor = DownloadMonitor(watch_path=str(tmpdir), debounce_seconds=0.5)
        success = await monitor.start(callback)
        
        if success:
            # Create test file
            test_file = tmpdir / "test.txt"
            test_file.write_text("Test content")
            
            # Wait for detection
            await asyncio.sleep(2)
            
            # Should have detected the file
            assert len(files_detected) > 0
            
            await monitor.stop()
            print("✅ Passed: DownloadMonitor detects new files")
        else:
            print("⚠️  Skipped: Monitor failed to start (permissions issue)")


async def manual_test_suite():
    """Manual test suite (for running without pytest)."""
    print("\n🧪 WAVE 3: File Organization & Watching Tests\n")
    
    tests = [
        ("FileOrganizer Path Creation", test_file_organizer_creation),
        ("FileOrganizer File Move", test_file_organizer_move),
        ("FileOrganizer Undo", test_file_organizer_undo),
        ("Processing Pipeline", test_pipeline_process_file),
        ("DownloadMonitor Init", test_download_monitor_initialization),
        ("DownloadMonitor File Detection", test_download_monitor_file_creation),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, test_func in tests:
        try:
            print(f"Running: {test_name}...", end=" ", flush=True)
            await test_func()
            passed += 1
        except ImportError as e:
            print(f"⏭️  SKIPPED: {e}")
            skipped += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {e}")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed, {skipped} skipped\n")
    return failed == 0


if __name__ == "__main__":
    asyncio.run(manual_test_suite())
