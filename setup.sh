#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Setup Script for Critique-Oriented RAG
# ============================================================================
# This script:
#   1. Clones the paper repositories (requires GitHub access)
#   2. Installs Python dependencies
#   3. Runs the paper ingestion pipeline
#   4. Validates the setup
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo "  Critique-Oriented RAG — Setup"
echo "============================================"

# ── Check Python ──────────────────────────────────────────────────────────
PYTHON="${PYTHON:-python3}"
if ! command -v "$PYTHON" &>/dev/null; then
    echo "ERROR: Python 3 not found. Install Python 3.10+ and try again."
    exit 1
fi

PY_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python: $PYTHON ($PY_VERSION)"

# ── Check .env ────────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    echo ""
    echo "  ⚠️  No .env file found."
    echo "  Creating from .env.example — please edit it with your API key."
    cp .env.example .env
    echo ""
    echo "  → Edit .env with: nano .env"
    echo "  → Then re-run: bash setup.sh"
    exit 1
fi

# ── Install dependencies ─────────────────────────────────────────────────
echo ""
echo "  Installing Python dependencies..."
"$PYTHON" -m pip install -r requirements.txt --quiet 2>&1 | tail -3

# ── Clone paper repositories ─────────────────────────────────────────────
echo ""
echo "  Cloning paper repositories..."

GITHUB_TOKEN="${GITHUB_TOKEN:-}"

clone_repo() {
    local repo_url="$1"
    local target_dir="$2"
    
    if [ -d "$target_dir" ]; then
        echo "    ✓ $target_dir already exists, skipping"
        return
    fi
    
    if [ -n "$GITHUB_TOKEN" ]; then
        repo_url="${repo_url/https:\/\//https://${GITHUB_TOKEN}@}"
    fi
    
    echo "    Cloning $target_dir..."
    git clone --depth 1 "$repo_url" "$target_dir" 2>&1 | tail -1
}

clone_repo "https://github.com/Ilovecodinghhh/research-methane-isotope-db.git" \
           "research-methane-isotope-db"

clone_repo "https://github.com/Ilovecodinghhh/research-methane-OH.git" \
           "research-methane-OH"

clone_repo "https://github.com/Ilovecodinghhh/upgrade_two_isotope_model.git" \
           "upgrade_two_isotope_model"

# ── Verify paper directories ─────────────────────────────────────────────
ISOTOPE_DIR="research-methane-isotope-db/methane_isotope_db/mineru_extractions_trimmed"
OH_DIR="research-methane-OH/research-methane-OH/papers_md_trimmed"

n_isotope=$(find "$ISOTOPE_DIR" -name "*.md" 2>/dev/null | wc -l)
n_oh=$(find "$OH_DIR" -name "*.md" 2>/dev/null | wc -l)

echo ""
echo "  Papers found:"
echo "    Isotope DB:   $n_isotope papers"
echo "    OH Papers:    $n_oh papers"
echo "    Total:        $(( n_isotope + n_oh )) papers"

if [ "$n_isotope" -eq 0 ] && [ "$n_oh" -eq 0 ]; then
    echo ""
    echo "  ERROR: No papers found. Check repository access."
    exit 1
fi

# ── Run ingestion ─────────────────────────────────────────────────────────
echo ""
echo "  Running paper ingestion pipeline..."
echo "  (This downloads the embedding model on first run — may take a few minutes)"
echo ""
"$PYTHON" ingest_papers.py

# ── Validate ──────────────────────────────────────────────────────────────
echo ""
if [ -d "chroma_db" ] && [ -f "all_chunks.json" ]; then
    n_chunks=$("$PYTHON" -c "import json; print(len(json.load(open('all_chunks.json'))))")
    echo "  ✅ Setup complete!"
    echo "     $n_chunks chunks indexed in ChromaDB + BM25"
    echo ""
    echo "  Next steps:"
    echo "    # Full comprehensive review"
    echo "    $PYTHON run_review.py --mode full"
    echo ""
    echo "    # Review a single parameter"
    echo "    $PYTHON run_review.py --mode single --param 'OH KIE'"
    echo ""
    echo "    # Review all 21 parameters individually"
    echo "    $PYTHON run_review.py --mode parameter"
else
    echo "  ❌ Setup failed — check errors above."
    exit 1
fi
