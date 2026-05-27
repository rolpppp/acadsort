# AcadSort Technical Architecture Review
**Assessment Date:** 2026-05-22  
**Status:** ⚠️ **NOT READY FOR FIRST DEPLOYMENT**

---

## Executive Summary

AcadSort has **solid foundational architecture and design** but is **incomplete for deployment**. The codebase has:
- ✅ Well-structured configuration and dependency management
- ✅ Thoughtful data schema design (SQLModel)
- ✅ Correct technology choices (FastAPI, Tauri, embeddings pipeline)
- ✅ Good separation of concerns in design
- ❌ **Missing ~60% of critical implementation** (file extraction, classifier, API routes, frontend)

**Recommendation:** Complete the missing modules before first deployment. The skeleton is sound; execution is incomplete.

---

## 1. STRUCTURAL ISSUES

### 1.1 Directory Layout Mismatch ⚠️

**Problem:** README describes a `frontend/` and `backend/` structure, but code is at root level with forward references to non-existent modules.

**Current State:**
```
acadsort/
├── config.py              ✅ Exists
├── embeddings.py          ✅ Exists  
├── engine.py              ✅ Exists (partial)
├── health.py              ✅ Exists (partial)
├── main.py                ✅ Exists but BROKEN (missing imports)
├── models.py              ✅ Exists
├── requirements.txt       ✅ Exists
├── setup_*.sh             ✅ Exist
├── api/                   ❌ MISSING (referenced in main.py)
├── classifier/            ❌ MISSING (referenced in main.py)
├── database/              ❌ MISSING (referenced in main.py)
└── frontend/              ❌ MISSING (referenced in setup_frontend.sh)
```

**Expected by README:**
```
acadsort/
├── frontend/              Tauri + React + TypeScript
├── backend/               Python FastAPI
│   ├── classifier/        Rule engine, embeddings, LLM fallback
│   ├── extraction/        PDF, DOCX, PPTX text extraction
│   ├── organizer/         File moving, renaming, folder creation
│   ├── watcher/           Filesystem monitor
│   ├── database/          SQLModel schema + engine
│   └── api/               FastAPI route handlers
├── data/
│   └── course_registry/   Seed UP Tacloban course data
├── models/                Downloaded models (gitignored)
└── tests/
```

**Impact:** HIGH  
**Fix:** Reorganize to match documented structure; move Python files to `backend/` subdirectory.

---

### 1.2 Missing Critical Modules

| Module | Status | Impact | Usage |
|--------|--------|--------|-------|
| `api/health.py` | ❌ Referenced but not created | HIGH | Required by `main.py` line 62 |
| `api/files.py` | ❌ Missing | HIGH | File upload/classification endpoints |
| `api/courses.py` | ❌ Missing | HIGH | Course management endpoints |
| `api/settings.py` | ❌ Missing | MEDIUM | User preferences endpoints |
| `api/queue.py` | ❌ Missing | MEDIUM | Processing queue status |
| `classifier/engine.py` | ❌ Missing | CRITICAL | Core classification logic |
| `classifier/llm_fallback.py` | ❌ Missing | MEDIUM | LLM-based fallback classification |
| `extraction/pdf.py` | ❌ Missing | CRITICAL | PyMuPDF text extraction |
| `extraction/docx.py` | ❌ Missing | HIGH | python-docx text extraction |
| `extraction/pptx.py` | ❌ Missing | HIGH | python-pptx text extraction |
| `watcher/monitor.py` | ❌ Missing | CRITICAL | Filesystem watching with debounce |
| `organizer/mover.py` | ❌ Missing | CRITICAL | File organization logic |
| `database/engine.py` | ⚠️ Partial | MEDIUM | Only database URL setup, missing async session handling |
| `database/models.py` | ⚠️ Partial | MEDIUM | Schema defined but not complete for all features |
| `frontend/` | ❌ Missing | HIGH | Entire Tauri + React UI |

**Total Coverage:** ~30% of critical path

---

## 2. APPLICATION FLOW ANALYSIS

### 2.1 Startup Sequence

**Current (Broken):**
```python
# main.py tries to import these but they don't exist
from api.health import router as health_router          # ❌ MISSING
from api.files import router as files_router            # ❌ MISSING
from api.courses import router as courses_router        # ❌ MISSING
from api.settings import router as settings_router      # ❌ MISSING
from api.queue import router as queue_router            # ❌ MISSING
```

**Result:** `python main.py` will fail immediately with `ModuleNotFoundError`

**Expected Flow (Design):**
1. **Startup Phase:**
   - ✅ Load config from `.env` (`config.py`)
   - ✅ Initialize SQLite database (`engine.py` / `models.py`)
   - ✅ Pre-load embedding model (`embeddings.py`)
   - ❌ Initialize Ollama connection (not yet coded)
   - ❌ Start filesystem watcher (`watcher/monitor.py`)
   
2. **Ready Phase:**
   - ✅ `/health` endpoint responds with status
   - Tauri frontend detects backend is healthy
   - UI becomes interactive

3. **Runtime Phase:**
   - Filesystem watcher detects new files in Downloads
   - File extraction pipeline runs
   - Classifier determines course + material type
   - File organized or queued for user confirmation

---

## 3. DEPENDENCY ANALYSIS

### 3.1 Dependencies ✅ Well-Chosen

| Layer | Package | Version | Status |
|-------|---------|---------|--------|
| **API** | FastAPI | 0.115.5 | ✅ Current |
| **Database** | SQLModel | 0.0.22 | ✅ Good choice for typed ORM |
| **Embeddings** | sentence-transformers | 3.3.1 | ✅ Multilingual support |
| **LLM** | ollama | 0.4.4 | ✅ Local LLM via HTTP |
| **PyTorch** | torch | 2.5.1 | ⚠️ CPU-only; GPU override available |
| **File Extraction** | PyMuPDF, python-docx, python-pptx | Latest | ✅ Standard choices |
| **Watcher** | watchdog | 6.0.0 | ✅ Current |
| **Logging** | structlog | 24.4.0 | ✅ Structured logging |
| **Async** | aiosqlite | 0.20.0 | ✅ Async SQLite |

### 3.2 Dependency Health Issues

**None detected.** No obvious conflicting versions or deprecated packages.

### 3.3 Missing Dependencies

**Performance:**
- No caching layer (Redis would help for embedding cache)
- No async task queue (Celery/RQ for heavy processing)

**Monitoring:**
- No APM/monitoring library (for production diagnostics)
- No OpenTelemetry hooks

**Testing:**
- ✅ pytest and pytest-asyncio included
- ❌ No test fixtures or factories

---

## 4. DATA MODEL ANALYSIS

### 4.1 Schema Design ✅ Solid

**Strengths:**
- ✅ `FileRecord` captures complete classification flow (original → moved, confidence, status)
- ✅ `CorrectionHistory` enables model retraining from user corrections
- ✅ `EmbeddingExemplar` allows fine-tuning embeddings over time
- ✅ `Course` supports both seed data and user customization (syllabus, keywords)
- ✅ Proper foreign keys and indexing on hot columns (status, course, filename)
- ✅ JSON fields for flexible keyword storage

**Potential Improvements:**
- ⚠️ No explicit "processing queue" table (files in PENDING status used implicitly)
- ⚠️ No "undo" audit trail beyond CorrectionHistory
- ⚠️ No soft deletes (for audit compliance)

### 4.2 Schema Gaps

Missing tables for planned features:
- No `ProcessingJob` table (for queue visibility)
- No `AuditLog` table (for compliance/debugging)
- No `ModelMetrics` table (for classification accuracy tracking)

---

## 5. CONFIGURATION MANAGEMENT ✅ Well-Designed

**Strengths:**
- ✅ Pydantic BaseSettings with `.env` support
- ✅ Sensible defaults (port 8765 fixed for Tauri sidecar reliability)
- ✅ Tunable thresholds (confidence_auto_move=0.90, confidence_suggest=0.70)
- ✅ Feature flags (ollama_enabled, debug mode)
- ✅ Graceful undo window (30 seconds)
- ✅ Directories created at import time

**Issues:**
- ⚠️ No `.env.example` file found (should be in git)
- ⚠️ No validation that Ollama is running before startup (lazy check only)

---

## 6. SECURITY ASSESSMENT

### 6.1 CORS Configuration ✅ Appropriate

```python
allow_origins=[
    "http://localhost:1420",    # Tauri dev
    "tauri://localhost",        # Tauri prod
    "https://tauri.localhost",
]
```
Only localhost; no public routes. ✅ Safe for offline desktop app.

### 6.2 File Handling ⚠️ Needs Review

**Risks:**
- No file size limits defined (requirements.txt missing)
- No path traversal protection (moving files into subdirectories)
- No malware scanning (not a requirement, but worth noting)

**Needed:**
- Add `MAX_FILE_SIZE` to config (prevent OOM on 5GB PDFs)
- Validate destination paths in organizer module

### 6.3 Database ⚠️ Needs Hardening

- ✅ Using SQLite with async support (aiosqlite)
- ❌ No encryption at rest (optional, but consider for sensitive UP student data)
- ⚠️ Connection pooling not explicitly configured

---

## 7. PERFORMANCE CONSIDERATIONS

### 7.1 Embedding Model Singleton ✅ Good Pattern

```python
def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(...)
    return _model
```
Pre-loads 420MB model once at startup. Subsequent classifications use cached model. ✅

### 7.2 Potential Bottlenecks

| Issue | Risk | Mitigation |
|-------|------|-----------|
| Embedding inference on CPU | MEDIUM | Batch processing + GPU override available |
| LLM fallback (Ollama) timeout | HIGH | 30-second timeout configured ✅; but no retry logic |
| File extraction from large PDFs | MEDIUM | extraction_max_chars=2000 limit ✅ |
| Watchdog filesystem events | MEDIUM | 2-second debounce configured ✅ |
| SQLite concurrent writes | LOW | Single-user desktop app; not an issue |

### 7.3 Caching Strategy

**Missing:**
- No embedding cache (recompute for every file)
- No classification result cache
- No course keyword cache

**Improvement:** Add in-memory LRU cache for embeddings after first week of usage data.

---

## 8. ERROR HANDLING & RESILIENCE

### 8.1 Lifespan Management ✅ Correct Pattern

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
```
Proper resource cleanup on app exit. ✅

### 8.2 Missing Error Handlers

- ❌ No global exception handler (500 errors will leak stack traces in debug mode)
- ❌ No timeout handlers (if Ollama hangs, API request blocks indefinitely)
- ❌ No file access error handlers (if Downloads folder is deleted mid-watch)
- ❌ No database connection error recovery

---

## 9. TESTING READINESS ⚠️ Partial

### 9.1 Test Infrastructure

- ✅ pytest + pytest-asyncio configured
- ✅ Dependencies included in requirements.txt
- ❌ No test directory structure
- ❌ No test fixtures or factories
- ❌ No integration tests
- ❌ No E2E test scenario

### 9.2 Week 1 Validation Gates (from README)

These tests **cannot run yet** because classifier + watcher are not implemented:
- [ ] GET `/health` returns `{"status":"ok"}` — **Only partial endpoint exists**
- [ ] PyMuPDF extracts readable text from UP PDF — **No extraction module**
- [ ] Embeddings produce stable scores for Filipino text — **Module exists, not tested**

---

## 10. DEPLOYMENT READINESS

### 10.1 Prerequisites Validation ✅ Good Scripts

**`setup_backend.sh` checks:**
- ✅ Python 3.11+ version
- ✅ Virtual environment creation
- ✅ Critical imports validation
- ✅ Ollama availability warning

**`setup_frontend.sh` checks:**
- ✅ Node.js 20+ version
- ✅ Rust/Cargo for Tauri
- ✅ Linux system dependencies (Tauri)

### 10.2 Blockers for First Deployment

| Blocker | Severity | Must Fix Before Deploy |
|---------|----------|------------------------|
| main.py imports fail (missing modules) | CRITICAL | YES |
| Classifier logic not implemented | CRITICAL | YES |
| File extraction not implemented | CRITICAL | YES |
| Filesystem watcher not implemented | CRITICAL | YES |
| API routes not implemented | CRITICAL | YES |
| Frontend (Tauri + React) not implemented | CRITICAL | YES |
| `.env.example` not present | HIGH | YES |
| Error handling incomplete | MEDIUM | Consider |
| No health check for Ollama connectivity | MEDIUM | Consider |
| File size limits not enforced | MEDIUM | Consider |

---

## 11. DESIGN PATTERNS ASSESSMENT

### 11.1 What's Right ✅

1. **Singleton Pattern (Embeddings)** — Correct for expensive model loading
2. **Dependency Injection (FastAPI)** — Using pydantic BaseSettings correctly
3. **Async/Await Patterns** — Proper use of async SQLite for FastAPI
4. **Configuration via Environment** — 12-factor app compliant
5. **Structured Logging** — Using structlog for debuggability

### 11.2 What's Missing ⚠️

1. **Repository Pattern** — Database access should be abstracted (for testing)
2. **Factory Pattern** — No factories for creating embeddings, classifiers
3. **Circuit Breaker** — For Ollama fallback (if LLM service is slow, should fail fast)
4. **Observer Pattern** — Filesystem watcher should notify subscribers
5. **Command Pattern** — File operations (move, rename) should be undoable via queue

---

## 12. TECH STACK ALIGNMENT

### Tauri + FastAPI Choice

✅ **Excellent for this use case:**
- Tauri gives native desktop app + system tray presence
- FastAPI sidecar on localhost avoids JVM startup overhead vs. Electron
- Rust-based Tauri is lightweight
- No electron bloat (saves 150MB+ in app size)

✅ **Python benefits:**
- Data science ecosystem (embeddings, LLM integration)
- Rapid development
- Cross-platform (macOS, Windows, Linux via setup scripts)

---

## 13. CRITICAL RECOMMENDATIONS

### Phase 1: Fix (Before Deploy)
1. **Reorganize directory structure** to match README (move files to `backend/`)
2. **Implement missing API routers** (health, files, courses, settings, queue)
3. **Implement file extraction** (PDF, DOCX, PPTX pipeline)
4. **Implement classifier** (embedding similarity + LLM fallback with retry logic)
5. **Implement filesystem watcher** with debounce and error recovery
6. **Implement file organizer** with path validation and undo support
7. **Create `.env.example`** for documentation
8. **Write integration tests** for Week 1 validation gates
9. **Add global error handlers** in FastAPI
10. **Implement frontend** (Tauri scaffold already possible)

### Phase 2: Harden (After MVP)
1. Add OpenTelemetry for observability
2. Implement caching layer for embeddings
3. Add model accuracy metrics table
4. Implement soft deletes for audit trail
5. Add file size limits + path traversal protection
6. Implement Ollama health check on startup

### Phase 3: Optimize (Production)
1. Profile embedding inference (consider batching or GPU)
2. Add async task queue for heavy file processing
3. Implement embedding cache expiration strategy
4. Add APM integration for production monitoring

---

## 14. DEPLOYMENT CHECKLIST

- [ ] All modules implemented and import successfully
- [ ] main.py runs without errors
- [ ] `/health` endpoint responds correctly
- [ ] Week 1 validation gates pass (see docs/week1_validation.md)
- [ ] `.env.example` present and documented
- [ ] All API routes tested (manual or automated)
- [ ] Frontend builds and connects to backend
- [ ] File extraction pipeline tested on sample UP PDFs
- [ ] Classifier tested with UP course materials
- [ ] Filesystem watcher tested (create/modify files in Downloads)
- [ ] Setup scripts tested on clean machine
- [ ] Ollama pre-pulling works (SmolLM2)
- [ ] Error cases handled gracefully (missing files, Ollama down, etc.)
- [ ] Code reviewed for security (path traversal, file size limits)

---

## CONCLUSION

**AcadSort has excellent architectural vision but incomplete implementation.** The technology choices are sound, the database schema is well-thought-out, and the configuration management is clean. However, **~60% of the codebase is missing** — specifically, the core business logic (classifier, file extraction, watcher) and all API routes.

**Recommendation:** Do NOT deploy yet. Completing the missing modules in Phase 1 (1-2 weeks) is essential before first user release. The skeleton is solid; execution is the blocker.

**Timeline Estimate for Completeness:**
- File extraction: 2-3 days
- Classifier engine: 3-5 days  
- Filesystem watcher: 2-3 days
- API routes: 2-3 days
- Frontend scaffold + Tauri integration: 3-5 days
- Testing + debugging: 3-5 days

**Total: 2-3 weeks to production-ready.**
