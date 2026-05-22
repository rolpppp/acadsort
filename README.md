# AcadSort
**Your automatic semester workspace organizer for UP Tacloban students.**

Watches your Downloads folder, classifies academic files using a local AI pipeline, and moves them into organized course folders — no internet required, no data leaves your device.

---

## Prerequisites

Install these on your machine before running the setup scripts.

| Tool | Version | Install |
|---|---|---|
| Python | 3.11+ | https://python.org |
| Node.js | 20+ | https://nodejs.org |
| Rust | latest stable | `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs \| sh` |
| Ollama | latest | https://ollama.com |

**Linux only** — install Tauri system dependencies:
```bash
sudo apt install libwebkit2gtk-4.1-dev libgtk-3-dev \
  libayatana-appindicator3-dev librsvg2-dev
```

**macOS only** — install Xcode Command Line Tools:
```bash
xcode-select --install
```

---

## Setup

### 1. Clone and initialize

```bash
git clone https://github.com/your-org/iskofiles.git
cd iskofiles
git checkout -b dev
```

### 2. Backend

```bash
bash scripts/setup_backend.sh
```

This will:
- Create a Python virtual environment at `.venv/`
- Install all backend dependencies
- Validate all critical imports
- Download the multilingual embedding model (~420MB, one-time)
- Check Ollama and warn if SmolLM2 isn't pulled

### 3. Pull the LLM (if not done automatically)

```bash
ollama pull smollm2:1.7b
```

### 4. Frontend

```bash
bash scripts/setup_frontend.sh
```

This will:
- Scaffold the Tauri + React project in `frontend/`
- Install npm dependencies
- Install Tailwind CSS, shadcn/ui, Zustand

### 5. Copy environment config

```bash
cp backend/.env.example backend/.env
# Edit backend/.env if you want to change ports or thresholds
```

---

## Running in Development

Start the Python backend (terminal 1):
```bash
source .venv/bin/activate
cd backend
uvicorn main:app --host 127.0.0.1 --port 8765 --reload
```

Start the Tauri dev server (terminal 2):
```bash
cd frontend
npm run tauri dev
```

The Tauri window will open once it detects the backend is healthy at `http://127.0.0.1:8765/health`.

---

## Project Structure

```
iskofiles/
├── frontend/           Tauri + React + TypeScript
├── backend/            Python FastAPI
│   ├── classifier/     Rule engine, embeddings, LLM fallback
│   ├── extraction/     PDF, DOCX, PPTX text extraction
│   ├── organizer/      File moving, renaming, folder creation
│   ├── watcher/        Filesystem monitor
│   ├── database/       SQLModel schema + engine
│   └── api/            FastAPI route handlers
├── data/
│   └── course_registry/  Seed UP Tacloban course data
├── models/             Downloaded models (gitignored)
├── tests/
└── scripts/            Setup scripts
```

---

## Week 1 Validation Gates

Before building any features, confirm these three things work:

- [ ] `GET http://127.0.0.1:8765/health` returns `{"status":"ok"}`
- [ ] PyMuPDF extracts readable text from a sample UP academic PDF
- [ ] Multilingual embeddings produce stable cosine scores for Filipino text

See `docs/week1_validation.md` for detailed test procedures.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop framework | Tauri 2 |
| Frontend | React 18 + TypeScript + Tailwind CSS + shadcn/ui |
| State | Zustand |
| Backend | Python 3.11 + FastAPI |
| Database | SQLite via SQLModel |
| Embeddings | paraphrase-multilingual-MiniLM-L12-v2 |
| LLM fallback | SmolLM2-1.7B via Ollama |
| File extraction | PyMuPDF, python-docx, python-pptx |
| File watching | watchdog |
