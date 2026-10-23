# ==============================================================================
# SMART ECO BIN / EcoSort AI — Windows PowerShell One-Click Launcher
# ==============================================================================
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$backendDir = Join-Path $root "backend"
$frontendDir = Join-Path $root "frontend"
$mlDir = Join-Path $root "ml"
$backendEnv = Join-Path $backendDir ".env"
$backendEnvExample = Join-Path $backendDir ".env.example"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "    SMART ECO BIN / EcoSort AI - Autonomous Waste Segregation" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Initializing local runtime environment..." -ForegroundColor Gray

# ------------------------------------------------------------------------------
# 1. Python Environment Check & Initialization
# ------------------------------------------------------------------------------
$localVenvPy = Join-Path $backendDir ".venv\Scripts\python.exe"
$localVenvPip = Join-Path $backendDir ".venv\Scripts\pip.exe"

if (-not (Test-Path $localVenvPy)) {
    Write-Host "`n[Setup] Backend virtual environment (.venv) not found." -ForegroundColor Yellow
    $sysPython = Get-Command python -ErrorAction SilentlyContinue
    if (-not $sysPython) {
        $sysPython = Get-Command py -ErrorAction SilentlyContinue
    }
    if (-not $sysPython) {
        Write-Host "[ERROR] Python 3.11+ is not installed or not in PATH." -ForegroundColor Red
        Write-Host "Please install Python from https://www.python.org/downloads/ and check 'Add to PATH'." -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[Setup] Creating virtual environment at backend\.venv using $($sysPython.Source)..." -ForegroundColor Cyan
    & $sysPython.Source -m venv (Join-Path $backendDir ".venv")
    
    Write-Host "[Setup] Installing PyTorch (CPU) and backend dependencies..." -ForegroundColor Cyan
    & $localVenvPip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    & $localVenvPip install -r (Join-Path $backendDir "requirements.txt")
}

$pythonExe = $localVenvPy

# ------------------------------------------------------------------------------
# 2. Node.js & Frontend Dependencies Check
# ------------------------------------------------------------------------------
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
$npmCmd = Get-Command npm -ErrorAction SilentlyContinue

if (-not $nodeCmd -or -not $npmCmd) {
    Write-Host "`n[ERROR] Node.js and npm are required to run the frontend." -ForegroundColor Red
    Write-Host "Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

$frontendNodeModules = Join-Path $frontendDir "node_modules"
if (-not (Test-Path $frontendNodeModules)) {
    Write-Host "`n[Setup] Frontend node_modules not found. Running npm install..." -ForegroundColor Yellow
    Push-Location $frontendDir
    & npm install
    Pop-Location
}

# ------------------------------------------------------------------------------
# 3. Model Weight File Verification
# ------------------------------------------------------------------------------
$classifierWeights = Join-Path $mlDir "model\waste_model.pth"
$detectorWeights = Join-Path $mlDir "model\waste_detector.pt"

Write-Host "`n[Verification] Checking AI model weights..." -ForegroundColor Gray
if (Test-Path $classifierWeights) {
    Write-Host "  [OK] MobileNetV2 12-Class Classifier weights verified (waste_model.pth)." -ForegroundColor Green
} else {
    Write-Host "  [WARNING] Classifier weights not found at $classifierWeights" -ForegroundColor Yellow
}

if (Test-Path $detectorWeights) {
    Write-Host "  [OK] SSDLite320-MobileNetV3 Multi-Object Detector weights verified (waste_detector.pt)." -ForegroundColor Green
} else {
    Write-Host "  [INFO] Detector weights not present. Single-item classification remains active." -ForegroundColor Gray
}

# ------------------------------------------------------------------------------
# 4. Initialize Local Backend Configuration Without Replacing User Settings
# ------------------------------------------------------------------------------
if (-not (Test-Path $backendEnv)) {
    if (-not (Test-Path $backendEnvExample)) {
        throw "Backend environment template not found: $backendEnvExample"
    }
    Copy-Item -Path $backendEnvExample -Destination $backendEnv
    Write-Host "`n[Setup] Created backend\.env from the development template." -ForegroundColor Cyan
}

# ------------------------------------------------------------------------------
# 5. Launch Backend & Frontend Services
# ------------------------------------------------------------------------------
Write-Host "`n[1/2] Starting FastAPI Backend on http://127.0.0.1:8001 ..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$backendDir'; `$env:ENVIRONMENT = 'development'; `$env:ALLOW_DEV_AUTH = 'true'; `$env:AUTH_PROVIDER = 'auto'; `$host.UI.RawUI.WindowTitle = 'EcoSort AI - FastAPI Backend'; & '$pythonExe' -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload"

Write-Host "[2/2] Starting Vite React Frontend on http://127.0.0.1:5173 ..." -ForegroundColor Yellow
Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "cd '$frontendDir'; `$host.UI.RawUI.WindowTitle = 'EcoSort AI - Vite Frontend'; npm run dev"

# ------------------------------------------------------------------------------
# 6. Summary & Quick Access
# ------------------------------------------------------------------------------
Write-Host "`n=================================================================" -ForegroundColor Green
Write-Host "    EcoSort AI Services Successfully Launched!" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  Frontend Web UI   : http://127.0.0.1:5173" -ForegroundColor Cyan
Write-Host "  Backend API       : http://127.0.0.1:8001" -ForegroundColor Cyan
Write-Host "  Interactive Docs  : http://127.0.0.1:8001/docs" -ForegroundColor Cyan
Write-Host "  Health Status     : http://127.0.0.1:8001/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Demo Administrator: admin@ecosortai.com (any password)" -ForegroundColor Gray
Write-Host "  Citizen Access    : Register any citizen account or visit /detect" -ForegroundColor Gray
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "Keep the opened PowerShell windows running to maintain the services.`n"
