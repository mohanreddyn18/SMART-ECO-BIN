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

function Test-LocalPort([int]$Port) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connection = $client.ConnectAsync("127.0.0.1", $Port)
        return $connection.Wait(500) -and -not $connection.IsFaulted
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

function Test-HttpEndpoint([string]$Url) {
    $previousErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $null = & curl.exe -fsS --max-time 3 $Url 2>$null
        $curlExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorPreference
    }
    return $curlExitCode -eq 0
}

function Get-BackendHealth([string]$Url) {
    $previousErrorPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $response = & curl.exe -fsS --max-time 3 $Url 2>$null
        $curlExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorPreference
    }
    if ($curlExitCode -ne 0) {
        return $null
    }
    try {
        return $response | ConvertFrom-Json
    }
    catch {
        return $null
    }
}

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
    if ($sysPython.Name -eq "py.exe") {
        & $sysPython.Source -3 -m venv (Join-Path $backendDir ".venv")
    }
    else {
        & $sysPython.Source -m venv (Join-Path $backendDir ".venv")
    }
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $localVenvPy)) {
        throw "Could not create backend\.venv. Check that Python 3.11 or later is installed."
    }
}

$pythonExe = $localVenvPy
& $pythonExe -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"
if ($LASTEXITCODE -ne 0) {
    throw "Python 3.11 or later is required. Install a supported version and recreate backend\.venv."
}
& $pythonExe -c "import fastapi, uvicorn, dotenv, torch, torchvision, google.genai, firebase_admin, PIL, numpy, sklearn, multipart, httpx"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[Setup] Installing PyTorch (CPU) and backend dependencies..." -ForegroundColor Cyan
    & $localVenvPip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    if ($LASTEXITCODE -ne 0) {
        throw "CPU PyTorch installation failed. Check your internet connection and Python version."
    }
    & $localVenvPip install -r (Join-Path $backendDir "requirements.txt")
    if ($LASTEXITCODE -ne 0) {
        throw "Backend dependency installation failed. See the pip output above."
    }
}

# ------------------------------------------------------------------------------
# 2. Node.js & Frontend Dependencies Check
# ------------------------------------------------------------------------------
$nodeCmd = Get-Command node -ErrorAction SilentlyContinue
$npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue

if (-not $nodeCmd -or -not $npmCmd) {
    Write-Host "`n[ERROR] Node.js and npm are required to run the frontend." -ForegroundColor Red
    Write-Host "Please install Node.js 18+ from https://nodejs.org/" -ForegroundColor Yellow
    exit 1
}

$frontendNodeModules = Join-Path $frontendDir "node_modules"
if (-not (Test-Path $frontendNodeModules) -or
    -not (Test-Path (Join-Path $frontendNodeModules "vite\bin\vite.js")) -or
    -not (Test-Path (Join-Path $frontendNodeModules "react\package.json"))) {
    Write-Host "`n[Setup] Frontend node_modules not found. Running npm ci..." -ForegroundColor Yellow
    Push-Location $frontendDir
    try {
        & $npmCmd.Source ci
        if ($LASTEXITCODE -ne 0) {
            throw "Frontend dependency installation failed. See the npm output above."
        }
    }
    finally {
        Pop-Location
    }
}

# ------------------------------------------------------------------------------
# 3. Model Weight File Verification
# ------------------------------------------------------------------------------
$classifierWeights = Join-Path $mlDir "model\waste_model.pth"
$detectorWeights = Join-Path $mlDir "model\waste_detector.pt"

Write-Host "`n[Verification] Checking AI model weights..." -ForegroundColor Gray
if (Test-Path $classifierWeights) {
    Write-Host "  [INFO] Classifier checkpoint file exists (loadability is reported by /health)." -ForegroundColor Gray
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
$backendUrl = "http://127.0.0.1:8001"
$frontendUrl = "http://127.0.0.1:5173"
$backendHealth = Get-BackendHealth "$backendUrl/health"
$frontendReady = Test-HttpEndpoint "$frontendUrl/"

if ($backendHealth) {
    Write-Host "`n[1/2] Reusing the healthy backend already listening on port 8001." -ForegroundColor Green
}
else {
    if (Test-LocalPort 8001) {
        throw "Port 8001 is occupied, but the project backend health endpoint is unavailable."
    }
    Write-Host "`n[1/2] Starting FastAPI Backend on $backendUrl ..." -ForegroundColor Yellow
    $backendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "Set-Location '$backendDir'; `$env:ENVIRONMENT = 'development'; `$env:ALLOW_DEV_AUTH = 'true'; `$env:AUTH_PROVIDER = 'auto'; `$host.UI.RawUI.WindowTitle = 'EcoSort AI - FastAPI Backend'; & '$pythonExe' -m uvicorn main:app --host 127.0.0.1 --port 8001" -PassThru
}

if ($frontendReady) {
    Write-Host "[2/2] Reusing the healthy frontend already listening on port 5173." -ForegroundColor Green
}
else {
    if (Test-LocalPort 5173) {
        throw "Port 5173 is occupied, but the project frontend is not responding."
    }
    Write-Host "[2/2] Starting Vite React Frontend on $frontendUrl ..." -ForegroundColor Yellow
    $frontendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendDir'; `$host.UI.RawUI.WindowTitle = 'EcoSort AI - Vite Frontend'; & '$($npmCmd.Source)' run dev -- --host 127.0.0.1" -PassThru
}

# ------------------------------------------------------------------------------
# 6. Verify service readiness before reporting status
# ------------------------------------------------------------------------------
for ($attempt = 0; $attempt -lt 60; $attempt++) {
    if (-not $backendHealth) {
        $backendHealth = Get-BackendHealth "$backendUrl/health"
        if (-not $backendHealth -and $backendProcess -and $backendProcess.HasExited) {
            throw "Backend process exited before becoming healthy. Check the backend window for errors."
        }
    }
    if (-not $frontendReady) {
        $frontendReady = Test-HttpEndpoint "$frontendUrl/"
        if (-not $frontendReady -and $frontendProcess -and $frontendProcess.HasExited) {
            throw "Frontend process exited before becoming healthy. Check the frontend window for errors."
        }
    }
    if ($backendHealth -and $frontendReady) { break }
    Start-Sleep -Seconds 2
}

if ($backendHealth -and $frontendReady) {
    Write-Host "`n=================================================================" -ForegroundColor Green
    Write-Host "    EcoSort AI API and frontend responded successfully." -ForegroundColor Green
} else {
    Write-Host "`n=================================================================" -ForegroundColor Yellow
    Write-Host "    Startup is incomplete; inspect the open service windows." -ForegroundColor Yellow
}
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  Frontend HTTP 200 : $frontendReady" -ForegroundColor $(if ($frontendReady) { "Green" } else { "Yellow" })
Write-Host "  Backend responded: $([bool]$backendHealth)" -ForegroundColor $(if ($backendHealth) { "Green" } else { "Yellow" })
if ($backendHealth) {
    Write-Host "  Backend status   : $($backendHealth.status)" -ForegroundColor $(if ($backendHealth.status -eq "healthy") { "Green" } else { "Yellow" })
    Write-Host "  Classifier loaded: $($backendHealth.classifier_loaded)" -ForegroundColor Gray
    Write-Host "  Detector loaded  : $($backendHealth.detector_loaded)" -ForegroundColor Gray
}
Write-Host "  Frontend Web UI  : http://127.0.0.1:5173" -ForegroundColor Cyan
Write-Host "  Backend API      : http://127.0.0.1:8001" -ForegroundColor Cyan
Write-Host "  Interactive Docs : http://127.0.0.1:8001/docs" -ForegroundColor Cyan
Write-Host "  Health Status    : http://127.0.0.1:8001/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Gemini assistants: $(if ($backendHealth -and $backendHealth.gemini_configured) { 'configured' } else { 'optional; set GEMINI_API_KEY in backend\.env' })" -ForegroundColor Gray
Write-Host "=================================================================" -ForegroundColor Green
if (-not $backendHealth -or -not $frontendReady) {
    throw "Startup did not complete successfully. Check the service windows and retry."
}
Start-Process $frontendUrl
