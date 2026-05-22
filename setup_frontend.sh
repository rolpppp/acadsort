#!/usr/bin/env bash
# setup_frontend.sh — IskoFiles frontend + Tauri environment setup
# Run from the project root: bash scripts/setup_frontend.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${CYAN}[iskofiles]${NC} $1"; }
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

log "Starting IskoFiles frontend + Tauri environment setup..."
echo ""

# ── 1. Node.js version check ────────────────────────────────
log "Checking Node.js..."
NODE_VER=$(node --version 2>/dev/null | sed 's/v//' || fail "Node.js not found. Install v20+ from https://nodejs.org")
NODE_MAJOR=$(echo "$NODE_VER" | cut -d. -f1)
if [ "$NODE_MAJOR" -lt 20 ]; then
  fail "Node.js v$NODE_VER found, but v20+ is required."
fi
ok "Node.js v$NODE_VER"

log "Checking npm..."
NPM_VER=$(npm --version 2>/dev/null || fail "npm not found")
ok "npm v$NPM_VER"

# ── 2. Rust check ───────────────────────────────────────────
log "Checking Rust / Cargo..."
if command -v cargo &>/dev/null; then
  ok "Cargo $(cargo --version)"
else
  warn "Rust not found. Tauri requires Rust."
  warn "Install via: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
  warn "Then restart your terminal and re-run this script."
  exit 1
fi

# ── 3. Tauri system dependencies (Linux only) ────────────────
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  log "Checking Linux Tauri dependencies..."
  MISSING_PKGS=()
  for pkg in libwebkit2gtk-4.1-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev; do
    dpkg -s "$pkg" &>/dev/null || MISSING_PKGS+=("$pkg")
  done
  if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    warn "Missing system packages: ${MISSING_PKGS[*]}"
    warn "Install with: sudo apt install ${MISSING_PKGS[*]}"
    exit 1
  fi
  ok "Linux Tauri dependencies present"
fi

# ── 4. Scaffold Tauri + React project ───────────────────────
log "Scaffolding Tauri + React + TypeScript project in frontend/..."
if [ -f "frontend/package.json" ]; then
  warn "frontend/package.json already exists. Skipping scaffold."
else
  cd frontend
  npm create tauri-app@latest . -- \
    --template react-ts \
    --manager npm \
    --yes 2>/dev/null || \
  npx create-tauri-app@latest . \
    --template react-ts \
    --manager npm \
    --yes
  cd ..
  ok "Tauri + React project scaffolded"
fi

# ── 5. Install npm dependencies ─────────────────────────────
log "Installing npm dependencies..."
cd frontend
npm install
ok "Base dependencies installed"

# ── 6. Install UI / state packages ──────────────────────────
log "Installing Tailwind CSS..."
npm install --save-dev tailwindcss@3 postcss autoprefixer
npx tailwindcss init -p 2>/dev/null || true

log "Installing shadcn/ui dependencies..."
npm install class-variance-authority clsx tailwind-merge lucide-react

log "Installing Zustand..."
npm install zustand

log "Installing additional utilities..."
npm install axios date-fns

cd ..
ok "All frontend packages installed"

# ── 7. Validate Tauri CLI ───────────────────────────────────
log "Checking Tauri CLI..."
cd frontend
if npx tauri --version &>/dev/null; then
  ok "Tauri CLI: $(npx tauri --version)"
else
  warn "Tauri CLI not accessible. Try: npm install --save-dev @tauri-apps/cli"
fi
cd ..

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ok "Frontend environment ready!"
echo ""
echo "  Dev server:   cd frontend && npm run tauri dev"
echo "  Build:        cd frontend && npm run tauri build"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
