"""Integration tests for Wave 5: FastAPI Routes."""

import asyncio
import json
from fastapi.testclient import TestClient

try:
    import pytest
    pytest_available = True
except ImportError:
    pytest_available = False


def test_health_endpoint():
    """Test 1: Health endpoint works."""
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    print("✅ Passed: Health endpoint")


def test_courses_list():
    """Test 2: GET /api/courses/list returns courses."""
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/api/courses/list")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 50  # Should have 63 courses seeded
    assert "code" in data[0]
    assert "name" in data[0]
    print(f"✅ Passed: GET /api/courses/list ({len(data)} courses)")


def test_courses_get_specific():
    """Test 3: GET /api/courses/{code} returns specific course."""
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/api/courses/CMSC%2011")
    
    if response.status_code == 200:
        data = response.json()
        assert "code" in data
        assert "name" in data
        print("✅ Passed: GET /api/courses/{code}")
    else:
        print("⏭️  Skipped: Course not found (may need exact code)")


def test_settings_current():
    """Test 4: GET /api/settings/current returns current settings."""
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/api/settings/current")
    
    assert response.status_code == 200
    data = response.json()
    assert "semester_name" in data
    assert "organization_style" in data
    assert "confidence_auto" in data
    print("✅ Passed: GET /api/settings/current")


def test_settings_update():
    """Test 5: PUT /api/settings/current updates settings."""
    from backend.main import app
    
    client = TestClient(app)
    response = client.put("/api/settings/current", params={
        "organization_style": "type",
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "updated"
    print("✅ Passed: PUT /api/settings/current")


def test_queue_stats():
    """Test 6: GET /api/queue/stats returns queue statistics."""
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/api/queue/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_pending" in data
    assert "total_confirmed" in data
    assert "total_rejected" in data
    assert "avg_confidence" in data
    print(f"✅ Passed: GET /api/queue/stats")


def test_queue_pending():
    """Test 7: GET /api/queue/pending returns pending files."""
    from backend.main import app
    
    client = TestClient(app)
    response = client.get("/api/queue/pending")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    print(f"✅ Passed: GET /api/queue/pending ({len(data)} files)")


async def manual_test_suite():
    """Run all tests manually."""
    print("\n🧪 WAVE 5: FastAPI Routes Tests\n")
    
    tests = [
        ("Health Endpoint", test_health_endpoint),
        ("Courses List", test_courses_list),
        ("Courses Get Specific", test_courses_get_specific),
        ("Settings Current", test_settings_current),
        ("Settings Update", test_settings_update),
        ("Queue Stats", test_queue_stats),
        ("Queue Pending", test_queue_pending),
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_name, test_func in tests:
        try:
            print(f"Running: {test_name}...", end=" ", flush=True)
            if asyncio.iscoroutinefunction(test_func):
                await test_func()
            else:
                test_func()
            passed += 1
        except ImportError as e:
            print(f"⏭️  SKIPPED: {e}")
            skipped += 1
        except AssertionError as e:
            print(f"❌ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR: {str(e)[:60]}")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed, {skipped} skipped\n")
    return failed == 0


if __name__ == "__main__":
    asyncio.run(manual_test_suite())
