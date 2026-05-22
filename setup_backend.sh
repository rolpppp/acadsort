#!/usr/bin/env bash
# setup_backend.sh — AcadSort backend environment setup
# Run from the project root: bash setup_backend.sh

set -e

VENV_DIR=".venv"
PYTHON_MIN="3.11"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[acadsort]${NC} $1"; }
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

log "Starting AcadSort backend environment setup..."
echo ""

# ── 1. Python version check ──────────────────────────────────
log "Checking Python version..."
PYTHON_BIN=$(command -v python3 || command -v python || fail "Python not found. Install Python 3.11+")
PYTHON_VER=$($PYTHON_BIN --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VER" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VER" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || { [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]; }; then
  fail "Python $PYTHON_VER found, but 3.11+ is required. Install via https://python.org"
fi
ok "Python $PYTHON_VER"

# ── 2. Create virtual environment ───────────────────────────
log "Creating virtual environment at $VENV_DIR..."
if [ -d "$VENV_DIR" ]; then
  warn "Virtual environment already exists. Skipping creation."
else
  $PYTHON_BIN -m venv "$VENV_DIR"
  ok "Virtual environment created"
fi

# ── 3. Activate and install dependencies ────────────────────
log "Activating virtual environment..."
source "$VENV_DIR/bin/activate" 2>/dev/null || source "$VENV_DIR/Scripts/activate" 2>/dev/null || fail "Could not activate venv"
ok "Virtual environment active: $(which python)"

log "Upgrading pip..."
pip install --quiet --upgrade pip

log "Installing backend dependencies (this may take a few minutes)..."
pip install --quiet -r backend/requirements.txt
ok "Dependencies installed"

# ── 4. Validate critical imports ────────────────────────────
echo ""
log "Validating critical imports..."

python - <<'EOF'
import sys
checks = [
    ("fastapi",                  "FastAPI"),
    ("sqlmodel",                 "SQLModel"),
    ("watchdog",                 "watchdog"),
    ("fitz",                     "PyMuPDF"),
    ("docx",                     "python-docx"),
    ("pptx",                     "python-pptx"),
    ("sentence_transformers",    "sentence-transformers"),
    ("ollama",                   "ollama client"),
    ("structlog",                "structlog"),
]
failed = []
for module, label in checks:
    try:
        __import__(module)
        print(f"  \033[32m✓\033[0m  {label}")
    except ImportError as e:
        print(f"  \033[31m✗\033[0m  {label} — {e}")
        failed.append(label)

if failed:
    print(f"\n\033[31mFailed imports: {', '.join(failed)}\033[0m")
    sys.exit(1)
else:
    print("\n\033[32mAll imports verified.\033[0m")
EOF

# ── 5. Check Ollama ─────────────────────────────────────────
echo ""
log "Checking Ollama installation..."
if command -v ollama &>/dev/null; then
  ok "Ollama found: $(ollama --version)"
  log "Checking if SmolLM2 model is available..."
  if ollama list 2>/dev/null | grep -q "smollm2"; then
    ok "SmolLM2 model already pulled"
  else
    warn "SmolLM2 not pulled yet. Run: ollama pull smollm2:1.7b"
  fi
else
  warn "Ollama not found. Install from https://ollama.com"
  warn "After installing, run: ollama pull smollm2:1.7b"
fi

# ── 6. Embedding model warm-up ──────────────────────────────
echo ""
log "Pre-downloading multilingual embedding model (first run only)..."
python - <<'EOF'
from sentence_transformers import SentenceTransformer
import os

model_cache = os.path.join("models", "embeddings")
os.makedirs(model_cache, exist_ok=True)

print("  Downloading paraphrase-multilingual-MiniLM-L12-v2...")
print("  (This is ~420MB and only downloads once)")
model = SentenceTransformer(
    "paraphrase-multilingual-MiniLM-L12-v2",
    cache_folder=model_cache
)
# Quick sanity check: Filipino + English
test_sentences = [
    "File Processing and Database Systems — Week 1 Lecture",
    "Aralin 1 — Kasaysayan ng Pilipinas",
]
embeddings = model.encode(test_sentences)
assert embeddings.shape == (2, 384), "Unexpected embedding shape"
print("  \033[32m✓\033[0m  Model downloaded and verified (Filipino + English test passed)")
EOF

# ── 7. Summary ───────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ok "Backend environment ready!"
echo ""
echo "  Activate venv:    source .venv/bin/activate"
echo "  Start backend:    cd backend && uvicorn main:app --reload --port 8765"
echo "  Run tests:        pytest tests/"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
