# ci.ps1 — run the same checks as .github/workflows/ci.yml locally.
#
# Usage:
#   .\ci.ps1              # everything: install deps, lint, typecheck, test
#   .\ci.ps1 lint         # ruff check + format check only
#   .\ci.ps1 typecheck    # ty only
#   .\ci.ps1 test         # pytest only
#
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('all', 'lint', 'typecheck', 'test')]
    [string]$Mode = 'all'
)

$ErrorActionPreference = 'Stop'

# --- cd to script dir (replaces: cd "$(dirname "$0)") ---------------------------
Set-Location -Path $PSScriptRoot

# --- configuration ---------------------------------------------------------------
$PyLock    = $env:PYLOCK
if (-not $PyLock) { $PyLock = 'pylock.toml' }
$GroupArgs = @('--group', 'dev')

$UseLock = Test-Path -LiteralPath $PyLock
# experimental lock file does not work yet
$UseLock = $false

# --- helpers ----------------------------------------------------------------------
function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Blue
}

function Fail {
    param([string]$Message)
    Write-Host "FAILED: $Message" -ForegroundColor Red
    exit 1
}

function Test-DepsInstalled {
    & $Script:Py -c "import PySide6, pytest, ruff" *> $null
    return ($LASTEXITCODE -eq 0)
}

# --- venv bootstrap (must come before any tool invocations) ------------------------
if (-not (Test-Path -LiteralPath '.venv' -PathType Container)) {
    Write-Step 'Creating venv'
    # Honor PYTHON env var, mirroring ${PYTHON:-python3}
    $Python = if ($env:PYTHON) { $env:PYTHON } else { 'python3' }
    & $Python -m venv .venv
    if ($LASTEXITCODE -ne 0) { Fail 'venv creation failed' }
}

# Pick the venv interpreter
if (Test-Path -LiteralPath '.venv\Scripts\python.exe') {
    $Script:Py = '.venv\Scripts\python.exe'
}
elseif (Test-Path -LiteralPath '.venv/bin/python') {
    $Script:Py = '.venv/bin/python'
}
else {
    Fail 'venv exists but no interpreter found (.venv incomplete?)'
}

# --- install ----------------------------------------------------------------------
function Install-Deps {
    if (Test-DepsInstalled) {
        Write-Step 'Dependencies appear to be installed'
        return
    }
    Write-Step 'Installing dependencies'
    if ($Script:UseLock) {
        & $Script:Py -m pip install --lock $Script:PyLock @Script:GroupArgs -e .
    }
    else {
        & $Script:Py -m pip install @Script:GroupArgs -e .
    }
    if ($LASTEXITCODE -ne 0) { Fail 'pip install failed' }
}

# --- checks -----------------------------------------------------------------------
function Invoke-Lint {
    Write-Step 'Ruff lint'
    & $Script:Py -m ruff check .
    if ($LASTEXITCODE -ne 0) { Fail 'ruff check' }

    Write-Step 'Ruff format'
    & $Script:Py -m ruff format --check .
    if ($LASTEXITCODE -ne 0) { Fail 'ruff format' }
}

function Invoke-Typecheck {
    Write-Step 'Type check (ty)'
    & $Script:Py -m ty check
    if ($LASTEXITCODE -ne 0) { Fail 'ty check' }
}

function Invoke-Tests {
    Write-Step 'Pytest'
    # No xvfb on Windows; use offscreen Qt platform directly.
    $env:QT_QPA_PLATFORM = 'offscreen'
    & $Script:Py -m pytest
    if ($LASTEXITCODE -ne 0) { Fail 'pytest' }
}

# --- main -------------------------------------------------------------------------
switch ($Mode) {
    'all' {
        Install-Deps
        Invoke-Lint
        Invoke-Typecheck
        Invoke-Tests
        Write-Step 'All checks passed ✔'
    }
    default {
        & (Get-Item "Function:Invoke-$Mode").ScriptBlock
    }
}
