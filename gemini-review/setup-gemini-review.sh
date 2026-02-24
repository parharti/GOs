#!/usr/bin/env bash
# ============================================================================
# setup-gemini-review.sh
# One-command setup for the Gemini Code Review CI/CD pipeline.
# Run from the root of your GitHub repository.
# ============================================================================

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}${BOLD}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          🤖 Gemini Code Review — Setup Script              ║"
echo "║          Python · PHP · Node.js · React · PostgreSQL       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Preflight checks ────────────────────────────────────────────────
check_command() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}✖ Required: '$1' not found. Please install it first.${NC}"
        exit 1
    fi
}

check_command git
check_command gh

# Check we're in a git repo
if ! git rev-parse --is-inside-work-tree &> /dev/null; then
    echo -e "${RED}✖ Not inside a git repository. Run this from your project root.${NC}"
    exit 1
fi

REPO_ROOT=$(git rev-parse --show-toplevel)
cd "$REPO_ROOT"

echo -e "${GREEN}✔ Git repository: $(basename "$REPO_ROOT")${NC}"
echo ""

# ── Step 1: Get Gemini API key ──────────────────────────────────────
echo -e "${BOLD}Step 1/5: Gemini API Key${NC}"
echo "Get your key at: https://aistudio.google.com/apikey"
echo ""

read -rp "Enter your Gemini API key (or press Enter to skip if already set): " API_KEY

if [ -n "$API_KEY" ]; then
    echo ""
    echo "Setting GEMINI_API_KEY as a GitHub repository secret..."

    # Detect repo name
    REPO=$(gh repo view --json nameWithOwner -q '.nameWithOwner' 2>/dev/null || true)
    if [ -z "$REPO" ]; then
        echo -e "${YELLOW}⚠ Could not detect repo. Setting secret manually...${NC}"
        read -rp "Enter repo (owner/name): " REPO
    fi

    echo "$API_KEY" | gh secret set GEMINI_API_KEY --repo "$REPO"
    echo -e "${GREEN}✔ Secret GEMINI_API_KEY set for $REPO${NC}"
else
    echo -e "${YELLOW}⏭ Skipped — make sure GEMINI_API_KEY is set in repo secrets.${NC}"
fi

echo ""

# ── Step 2: Create workflow directory ───────────────────────────────
echo -e "${BOLD}Step 2/5: Creating workflow files${NC}"

mkdir -p .github/workflows
mkdir -p docs

# ── Step 3: Copy workflow files ─────────────────────────────────────
echo -e "${BOLD}Step 3/5: Installing workflows${NC}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if source files exist (running from the gemini-review directory)
if [ -f "$SCRIPT_DIR/.github/workflows/gemini-code-review.yml" ]; then
    cp "$SCRIPT_DIR/.github/workflows/gemini-code-review.yml" .github/workflows/
    cp "$SCRIPT_DIR/.github/workflows/gemini-security-review.yml" .github/workflows/
    cp "$SCRIPT_DIR/.github/workflows/gemini-sql-audit.yml" .github/workflows/
    cp "$SCRIPT_DIR/docs/styleguide.md" docs/
    echo -e "${GREEN}✔ Copied workflow files from source${NC}"
else
    echo -e "${YELLOW}⚠ Source files not found beside this script.${NC}"
    echo "  Please manually copy the following files:"
    echo "    .github/workflows/gemini-code-review.yml"
    echo "    .github/workflows/gemini-security-review.yml"
    echo "    .github/workflows/gemini-sql-audit.yml"
    echo "    docs/styleguide.md"
fi

echo ""

# ── Step 4: Create labels ──────────────────────────────────────────
echo -e "${BOLD}Step 4/5: Creating GitHub labels${NC}"

create_label() {
    local name="$1"
    local color="$2"
    local desc="$3"
    gh label create "$name" --color "$color" --description "$desc" 2>/dev/null && \
        echo -e "${GREEN}  ✔ Label: $name${NC}" || \
        echo -e "${YELLOW}  ⏭ Label '$name' already exists${NC}"
}

create_label "sql-audit"     "0E8A16" "Weekly SQL audit report"
create_label "automated"     "1D76DB" "Created by automation"
create_label "security"      "D93F0B" "Security review finding"
create_label "gemini-review" "7057FF" "Reviewed by Gemini AI"

echo ""

# ── Step 5: Verify setup ───────────────────────────────────────────
echo -e "${BOLD}Step 5/5: Verification${NC}"

ALL_GOOD=true

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}  ✔ $1${NC}"
    else
        echo -e "${RED}  ✖ $1 — MISSING${NC}"
        ALL_GOOD=false
    fi
}

check_file ".github/workflows/gemini-code-review.yml"
check_file ".github/workflows/gemini-security-review.yml"
check_file ".github/workflows/gemini-sql-audit.yml"
check_file "docs/styleguide.md"

echo ""

# Check if secret exists
SECRET_SET=$(gh secret list 2>/dev/null | grep -c "GEMINI_API_KEY" || true)
if [ "$SECRET_SET" -gt 0 ]; then
    echo -e "${GREEN}  ✔ GEMINI_API_KEY secret is set${NC}"
else
    echo -e "${YELLOW}  ⚠ GEMINI_API_KEY secret not detected (may need manual setup)${NC}"
    ALL_GOOD=false
fi

echo ""

if [ "$ALL_GOOD" = true ]; then
    echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  ✅ Setup complete! Ready to review PRs.       ${NC}"
    echo -e "${GREEN}${BOLD}══════════════════════════════════════════════════${NC}"
else
    echo -e "${YELLOW}${BOLD}══════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}${BOLD}  ⚠️  Setup partially complete. Fix items above. ${NC}"
    echo -e "${YELLOW}${BOLD}══════════════════════════════════════════════════${NC}"
fi

echo ""
echo -e "${CYAN}Next steps:${NC}"
echo "  1. git add .github/ docs/"
echo "  2. git commit -m '[CHORE] Add Gemini code review workflows'"
echo "  3. git push origin main"
echo "  4. Open a PR to test the review pipeline!"
echo ""
echo -e "${CYAN}Workflows:${NC}"
echo "  • gemini-code-review.yml   — Reviews every PR (6 checks)"
echo "  • gemini-security-review.yml — Triggers on auth/API/DB changes"
echo "  • gemini-sql-audit.yml     — Weekly Monday report (GitHub Issue)"
echo ""
