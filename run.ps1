# Launch the full application from the repository root.
# Usage: powershell -ExecutionPolicy Bypass -File .\run.ps1

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

if (-not (Test-Path "$projectRoot\backend\.env")) {
    throw "Missing backend\.env. Follow the environment configuration section in README.md."
}

if (-not (Test-Path "$projectRoot\frontend\.env")) {
    throw "Missing frontend\.env. Follow the environment configuration section in README.md."
}

if (-not (Test-Path "$projectRoot\backend\venv\Scripts\python.exe")) {
    throw "Missing backend virtual environment. Run the backend installation commands from README.md."
}

if (-not (Test-Path "$projectRoot\frontend\node_modules")) {
    throw "Missing frontend dependencies. Run npm install in the frontend folder."
}

& "$projectRoot\scripts\start-all.ps1"
