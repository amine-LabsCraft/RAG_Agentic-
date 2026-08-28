# Run the project quality gates from the repository root.
# Usage: powershell -ExecutionPolicy Bypass -File .\test.ps1

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

if (-not (Test-Path "$projectRoot\backend\venv\Scripts\python.exe")) {
    throw "Missing backend virtual environment. Run the backend installation commands from README.md."
}

if (-not (Test-Path "$projectRoot\frontend\node_modules")) {
    throw "Missing frontend dependencies. Run npm install in the frontend folder."
}

Push-Location "$projectRoot\frontend"
try {
    npm run lint
    npm run build
} finally {
    Pop-Location
}

Push-Location "$projectRoot\backend"
try {
    & .\venv\Scripts\python.exe -m pip check
    & .\venv\Scripts\python.exe -m unittest discover -s tests -v
} finally {
    Pop-Location
}

Write-Host "All local quality checks passed." -ForegroundColor Green
