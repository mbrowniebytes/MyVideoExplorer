#!/bin/bash
#
# ci.sh — run the same checks as .github/workflows/ci.yml locally.
#
# Usage:
#   ./ci.sh              # everything: install deps, lint, typecheck, test
#   ./ci.sh lint         # ruff check + format check only
#   ./ci.sh typecheck    # ty only
#   ./ci.sh test         # pytest only
#
set -euo pipefail

#cd "$(dirname "$0")"
# replace: cd "$(dirname "$0")"
script_dir=${BASH_SOURCE[0]%/*}
if [[ "$script_dir" == "${BASH_SOURCE[0]}" ]]; then
    script_dir=.
fi
cd "$script_dir"

# --- venv bootstrap (must come before any tool invocations) --------------------
if [[ ! -d .venv ]]; then
    step="Creating venv"
    printf '\033[1;34m==> %s\033[0m\n' "$step"
    ${PYTHON:-python3} -m venv .venv
fi

# Pick the venv interpreter for either layout (Windows uses Scripts/)
if [[ -x .venv/Scripts/python.exe ]]; then
    PY=".venv/Scripts/python.exe"
elif [[ -x .venv/bin/python ]]; then
    PY=".venv/bin/python"
else
    echo "ERROR: venv exists but no interpreter found (.venv incomplete?)" >&2
    exit 1
fi

# --- configuration -------------------------------------------------------------
PYLOCK=${PYLOCK:-pylock.toml}
GROUP_ARGS=("--group" "dev")

PYLOCK=${PYLOCK:-pylock.toml}
GROUP_ARGS=("--group" "dev")
USE_LOCK=0
[[ -f "$PYLOCK" ]] && USE_LOCK=1
# experimental lock file does not work yet
USE_LOCK=0

# --- helpers ---------------------------------------------------------------------
step() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
fail() { printf '\033[1;31mFAILED: %s\033[0m\n' "$*" >&2; exit 1; }

run_pytest() {
    if command -v xvfb-run >/dev/null 2>&1; then
        xvfb-run -a "$PY" -m pytest "$@"
    else
        QT_QPA_PLATFORM=offscreen "$PY" -m pytest "$@"
    fi
}

# --- install ----------------------------------------------------------------------
deps_installed() {
    "$PY" -c "import PySide6, pytest, ruff" >/dev/null 2>&1
}

install_deps() {
    if deps_installed; then
        step "Dependencies appear to be installed"
        return
    fi
    step "Installing dependencies"
    if (( USE_LOCK )); then
        "$PY" -m pip install --lock "$PYLOCK" "${GROUP_ARGS[@]}" -e . ||
            fail "pip install failed (check pip >= 25.1 for --group support)"
    else
        "$PY" -m pip install "${GROUP_ARGS[@]}" -e . || fail "pip install failed"
    fi
}

# --- checks -----------------------------------------------------------------------
lint() {
    step "Ruff lint"
    "$PY" -m ruff check . || fail "ruff check"
    step "Ruff format"
    "$PY" -m ruff format --check . || fail "ruff format"
}

typecheck() {
    step "Type check (ty)"
    "$PY" -m ty check || fail "ty check"
}

test_checks() {
    step "Pytest"
    run_pytest || fail "pytest"
}

# --- main -------------------------------------------------------------------------
case "${1:-all}" in
    lint|typecheck|test)  MODE="$1" ;;
    all|"")               MODE="all" ;;
    *)                    echo "Usage: $0 [lint|typecheck|test|all]" >&2; exit 2 ;;
esac

if [[ "$MODE" == "all" ]]; then
    install_deps
    lint
    typecheck
    test_checks
    step "All checks passed ✔"
else
    "$MODE"
fi
