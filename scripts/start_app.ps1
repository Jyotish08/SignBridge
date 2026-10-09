# PowerShell script to start SignBridge on Windows
$ErrorActionPreference = "Stop"

Write-Host "[SignBridge] Starting SignBridge on Windows..." -ForegroundColor Green

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = (Resolve-Path "$ScriptDir\..").Path
Set-Location $ProjectRoot

# Paths
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$VenvPython = Join-Path $BackendDir "venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    $VenvPython = Join-Path $BackendDir "py311_venv\Scripts\python.exe"
}

if (-not (Test-Path $VenvPython)) {
    $VenvPython = Join-Path $ProjectRoot ".venv_exp\Scripts\python.exe"
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "[Backend] Python venv not found in backend. Creating venv..." -ForegroundColor Yellow
    Set-Location $BackendDir
    python -m venv venv
    $VenvPython = Join-Path $BackendDir "venv\Scripts\python.exe"
    & $VenvPython -m pip install -r requirements.txt
    Set-Location $ProjectRoot
}

# Check if backend is already running on port 8000
$BackendRunning = $false
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        $BackendRunning = $true
    }
} catch {
    $BackendRunning = $false
}

if ($BackendRunning) {
    Write-Host "[Backend] Backend is already running on http://127.0.0.1:8000" -ForegroundColor Green
} else {
    Write-Host "[Backend] Starting Backend server..." -ForegroundColor Cyan
    $BackendProcess = Start-Process -FilePath $VenvPython -ArgumentList "run_backend.py" -WorkingDirectory $BackendDir -PassThru
    
    Write-Host "[Backend] Waiting for backend to initialize (loading offline models)..." -ForegroundColor Yellow
    $ready = $false
    for ($i = 1; $i -le 35; $i++) {
        Start-Sleep -Seconds 1
        try {
            $resp = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
            if ($resp.StatusCode -eq 200) {
                $ready = $true
                break
            }
        } catch {}
    }
    
    if ($ready) {
        Write-Host "[Backend] Backend ready on http://127.0.0.1:8000!" -ForegroundColor Green
    } else {
        Write-Host "[Backend] Error: Backend failed to start on port 8000." -ForegroundColor Red
        exit 1
    }
}

# Start Frontend
Write-Host "[Frontend] Starting Frontend (Vite on http://localhost:5173)..." -ForegroundColor Cyan
Set-Location $FrontendDir
if (Get-Command npm.cmd -ErrorAction SilentlyContinue) {
    & npm.cmd run dev
} else {
    npm run dev
}
