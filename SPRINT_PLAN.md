# AcadSort First Sprint Plan
**Goal:** Complete Phase 1 (MVP Implementation) for first deployment  
**Target Duration:** 2-3 weeks  
**Success Criteria:** All Week 1 validation gates pass + full E2E test succeeds

---

## Sprint Overview

This sprint is organized into **6 waves**, each with clear dependencies and milestones. Start each wave only after the previous one is complete.

---

## WAVE 1: Foundation & Setup (Days 1-2)
*Get the codebase structure right and configured.*

### Tasks
- [ ] **1.1** Reorganize codebase to backend/ directory structure
  - Move Python files to `backend/`
  - Create `backend/api/`, `backend/classifier/`, `backend/extraction/`, `backend/watcher/`, `backend/organizer/`, `backend/database/` directories
  - Move `main.py` → `backend/main.py`
  - Create `__init__.py` files for all packages
  - Update setup scripts to reference new paths

- [ ] **1.2** Create `.env.example` configuration template
  - Document all config options from `config.py`
  - Include comments for each setting
  - Provide realistic defaults for UP Tacloban users

- [ ] **1.3** Update main.py to fix import paths
  - Change imports to reference new module locations
  - Test that `python backend/main.py` doesn't crash with ImportError

**Deliverable:** Code structure matches README exactly; imports don't fail

---

## WAVE 2: Core Extraction & Classification (Days 3-6)
*Build the intelligence layer.*

### Tasks
- [ ] **2.1** Implement file extraction pipeline
  - Create `backend/extraction/pdf.py` — PyMuPDF text extraction with fallback
  - Create `backend/extraction/docx.py` — python-docx extraction
  - Create `backend/extraction/pptx.py` — python-pptx extraction
  - Create `backend/extraction/utils.py` — Character limit handling, cleanup
  - **Test:** Extract text from sample UP PDF, DOCX, PPTX files
  - Document max character limits (should respect `extraction_max_chars=2000`)

- [ ] **2.2** Implement classifier engine with embeddings
  - Create `backend/classifier/engine.py`
  - Implement `classify_file(text: str, courses: List[Course]) -> ClassificationResult`
  - Cosine similarity scoring against course keywords
  - Return top 3 candidates with confidence scores
  - **Test:** Verify embeddings are consistent for Filipino text ("Leksyon" = lecture)

- [ ] **2.3** Implement LLM fallback classifier
  - Create `backend/classifier/llm_fallback.py`
  - Implement Ollama integration with retry logic (tenacity)
  - Prompt engineering for course + material_type classification
  - Timeout handling (30-second limit)
  - **Test:** Verify Ollama responds with valid course codes

- [ ] **2.4** Create classifier integration tests
  - Test embedding consistency
  - Test cosine similarity scoring
  - Test LLM fallback on ambiguous files
  - Test Week 1 validation gate #3 (embeddings produce stable scores)

**Deliverable:** Classification pipeline works end-to-end; can classify sample UP materials

---

## WAVE 3: File Organization & Watching (Days 7-9)
*Watch Downloads and organize files.*

### Tasks
- [ ] **3.1** Implement filesystem watcher
  - Create `backend/watcher/monitor.py`
  - Use watchdog to monitor Downloads folder
  - Implement 2-second debounce (from config)
  - Error handling for folder permissions, file locks
  - **Test:** Create test files in folder; verify callback triggers

- [ ] **3.2** Implement file organizer/mover
  - Create `backend/organizer/mover.py`
  - Implement `organize_file(source, course, material_type, week) -> destination`
  - Support two organization styles: "week" and "type" (from config)
  - Implement undo with grace period (30 seconds)
  - Path validation to prevent traversal attacks
  - **Test:** Move test file and verify it lands in correct folder

- [ ] **3.3** Implement end-to-end file pipeline
  - Create `backend/watcher/pipeline.py`
  - Orchestrate: Extract → Classify → Organize
  - Handle classification confidence thresholds:
    - ≥ 0.90: auto-move silently
    - 0.70-0.90: move + notify user
    - < 0.70: put in review queue
  - Error recovery (retry logic, fallback)

**Deliverable:** Files in Downloads automatically organize into course folders

---

## WAVE 4: Database & Data Models (Days 10-11)
*Persist everything.*

### Tasks
- [ ] **4.1** Finalize database schema
  - Create `backend/database/models.py` complete with all tables
  - Add `ProcessingJob` table for queue visibility (OPTIONAL for MVP)
  - Verify foreign key relationships
  - Create migration helper or init script

- [ ] **4.2** Implement database engine
  - Create `backend/database/engine.py`
  - Async SQLite setup with aiosqlite
  - Implement `get_session()` dependency for FastAPI
  - Add graceful connection error handling

- [ ] **4.3** Seed course registry
  - Load UP Tacloban courses from `up_tacloban_courses.json`
  - Implement `backend/database/seed.py`
  - Script to initialize courses on first run
  - **Test:** Verify courses are in database after startup

- [ ] **4.4** Create database tests
  - Test session creation
  - Test CRUD operations on all tables
  - Test foreign key constraints
  - Test transaction rollback on error

**Deliverable:** All data persists correctly; course registry seeded

---

## WAVE 5: FastAPI Routes (Days 12-14)
*Build the HTTP API.*

### Tasks
- [ ] **5.1** Implement /health endpoint
  - Create `backend/api/health.py`
  - Return status, version, ollama_available
  - **Test:** Week 1 validation gate #1 (health returns 200)

- [ ] **5.2** Implement /api/files routes
  - `POST /api/files/upload` — Receive file, extract, classify, organize
  - `GET /api/files` — List all files with status filter
  - `GET /api/files/{id}` — Get single file details
  - `POST /api/files/{id}/undo` — Undo move within grace period
  - `POST /api/files/{id}/correct` — User correction for retraining

- [ ] **5.3** Implement /api/courses routes
  - `GET /api/courses` — List all courses
  - `POST /api/courses` — Add new course (custom)
  - `PUT /api/courses/{code}` — Update keywords/syllabus
  - `DELETE /api/courses/{code}` — Remove course
  - `POST /api/courses/sync` — Re-sync from JSON seed

- [ ] **5.4** Implement /api/settings routes
  - `GET /api/settings` — Get user preferences
  - `PUT /api/settings` — Update preferences (confidence thresholds, org style)
  - `POST /api/settings/activate-semester` — Switch active semester

- [ ] **5.5** Implement /api/queue routes (OPTIONAL for MVP)
  - `GET /api/queue` — Get pending files for user review
  - `POST /api/queue/{id}/confirm` — User confirms classification

- [ ] **5.6** Add global error handlers
  - HTTP 500 error handler (log stack trace, return generic message in production)
  - HTTP 404 handler
  - Timeout handler (504 Gateway Timeout for Ollama hangs)
  - File not found handler

- [ ] **5.7** API testing
  - Create `backend/tests/test_api.py` with fixtures
  - Test all routes with valid/invalid inputs
  - Test error cases (file too large, course not found, etc.)

**Deliverable:** All APIs respond correctly; can upload and classify a file via HTTP

---

## WAVE 6: Frontend & Integration (Days 15-18)
*Build the UI and connect everything.*

### Tasks
- [ ] **6.1** Set up Tauri frontend scaffold
  - Run Tauri scaffolder: `cargo create-tauri-app`
  - Configure Tauri to spawn backend as sidecar
  - Set backend binary path to `./backend/.venv/bin/python`
  - Update `tauri.conf.json` with backend command

- [ ] **6.2** Create frontend components
  - Status monitor component (is backend healthy?)
  - File watcher status (listening to Downloads)
  - Recent files UI (auto-organized files list)
  - Course manager (add custom courses)
  - Settings panel (confidence thresholds, org style)

- [ ] **6.3** Implement frontend-backend communication
  - Async health check loop (polls every 2 seconds)
  - Show "waiting for backend" spinner until `/health` returns 200
  - WebSocket or polling for real-time file updates
  - Error state handling (backend crashed, Ollama down, etc.)

- [ ] **6.4** Test Tauri dev environment
  - `npm run tauri dev` launches backend + frontend
  - UI detects backend health correctly
  - Simulate file upload and verify UI updates
  - Test error scenarios

**Deliverable:** Click "organize my downloads" → files organize themselves

---

## WAVE 7: Testing & Validation (Days 19-21)
*Verify everything works together.*

### Tasks
- [ ] **7.1** Test Week 1 validation gates
  - ✅ GET `/health` returns `{"status":"ok"}`
  - ✅ PyMuPDF extracts readable text from sample UP PDF
  - ✅ Embeddings produce stable cosine scores for Filipino text

- [ ] **7.2** Run integration tests
  - Create `backend/tests/test_integration.py`
  - E2E scenario: Download → Extract → Classify → Organize → Verify
  - Test with real UP course materials (CMSC 11 lecture, CMSC 127 assignment, etc.)
  - Test both high-confidence and ambiguous files

- [ ] **7.3** Performance profiling
  - Time file extraction (should be <2s per file)
  - Time embedding inference (should be <1s per batch)
  - Monitor memory usage (model + database shouldn't exceed 500MB)
  - Identify bottlenecks

- [ ] **7.4** Security review
  - Check file size limits enforced (config missing this)
  - Verify path traversal protection (e.g., no `../` escapes)
  - Verify no secrets in logs
  - Test with malformed files (corrupted PDF, zip files, etc.)

- [ ] **7.5** Documentation
  - Create `docs/deployment.md` with step-by-step instructions
  - Create `docs/api-reference.md` (endpoint descriptions)
  - Create `docs/troubleshooting.md` (common issues)
  - Create `docs/development.md` (how to extend classifier)

**Deliverable:** All validation gates pass; confident to release

---

## WAVE 8: Pre-Deployment Checklist (Day 22)
*Final sanity checks.*

- [ ] **8.1** Test setup scripts on fresh machine
  - Run `bash setup_backend.sh` on clean install (no .venv)
  - Verify all dependencies install correctly
  - Verify model downloads (~420MB embedding model)
  - Verify Ollama warning appears if SmolLM2 not pulled

- [ ] **8.2** Test setup on multiple OS
  - macOS (primary target): ✅
  - Windows (WSL or native): ? (verify setup scripts work)
  - Linux (if applicable): ? (verify Tauri dependencies install)

- [ ] **8.3** Verify .env.example completeness
  - All config options documented
  - Example values realistic
  - Instructions clear for overrides

- [ ] **8.4** Create release notes
  - List features ready for MVP
  - Document known limitations
  - Provide user setup instructions

**Deliverable:** Ready to ship

---

## Dependencies & Sequencing

```
WAVE 1 (Foundation)
    ↓
WAVE 2 (Classification) ← needs to test independently
    ↓
WAVE 3 (Watching) ← depends on WAVE 2
    ↓
WAVE 4 (Database) ← independent, but needed by WAVE 5
    ↓
WAVE 5 (APIs) ← depends on WAVE 2, 3, 4
    ↓
WAVE 6 (Frontend) ← depends on WAVE 5
    ↓
WAVE 7 (Testing) ← depends on everything
    ↓
WAVE 8 (Deploy) ← final checks
```

---

## Success Metrics

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Code builds without errors | 100% | `python -m py_compile backend/**/*.py` |
| Imports work | 100% | `python backend/main.py` starts server |
| `/health` responds | 100% | `curl http://localhost:8765/health` |
| File extraction works | 100% | Week 1 validation gate #2 |
| Embeddings stable | 100% | Week 1 validation gate #3 |
| E2E test passes | 100% | Upload file → Verify organized |
| Setup scripts work | 100% | Test on fresh machine |
| No console errors | 99% | Review logs during manual testing |

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Ollama hangs on LLM call | MEDIUM | HIGH | 30-second timeout + circuit breaker |
| File extraction fails on PDF | MEDIUM | MEDIUM | Try multiple extraction methods |
| Windows path issues | LOW | HIGH | Use `pathlib.Path` everywhere |
| Performance regression | LOW | MEDIUM | Profile early (Wave 7) |
| Concurrent file watch events | LOW | LOW | 2-second debounce implemented |

---

## Estimated Time Breakdown

| Wave | Focus | Est. Hours | Notes |
|------|-------|-----------|-------|
| 1 | Setup | 4 | Mostly refactoring |
| 2 | Classification | 16 | Complex logic + testing |
| 3 | Watching | 12 | Error handling critical |
| 4 | Database | 8 | Straightforward |
| 5 | APIs | 12 | Many endpoints to implement |
| 6 | Frontend | 12 | Tauri scaffolding + React |
| 7 | Testing | 12 | Integration + security review |
| 8 | Deploy prep | 4 | Documentation + final checks |
| **TOTAL** | | **80 hours** | ~2 weeks @ 40hrs/week |

---

## Code Review Checkpoints

- [ ] After Wave 1: Codebase structure correct
- [ ] After Wave 2: Classification logic sound
- [ ] After Wave 5: All APIs tested and working
- [ ] After Wave 7: Full E2E test passes
- [ ] Before Wave 8: Security review complete

---

## Communication Plan

- Daily standup: Review which tasks completed, blockers
- End of each wave: Demo to stakeholders
- End of Week 2: Go/No-Go decision for deployment

