@echo off
title SMART ECO BIN - EcoSort AI Launcher
echo =================================================================
echo     SMART ECO BIN / EcoSort AI - Autonomous Waste Segregation
echo =================================================================
echo.

set ROOT_DIR=%~dp0
set BACKEND_DIR=%ROOT_DIR%backend
set FRONTEND_DIR=%ROOT_DIR%frontend
set PYTHON_EXE=%BACKEND_DIR%\.venv\Scripts\python.exe

if not exist "%PYTHON_EXE%" (
    echo [Setup] Backend virtual environment not found. Checking system Python...
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] Python 3.11+ is not installed or not in PATH.
        echo Please install Python from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo [Setup] Creating virtual environment at backend\.venv ...
    python -m venv "%BACKEND_DIR%\.venv"
    echo [Setup] Installing PyTorch and backend dependencies...
    "%BACKEND_DIR%\.venv\Scripts\pip.exe" install torch torchvision --index-url https://download.pytorch.org/whl/cpu
    "%BACKEND_DIR%\.venv\Scripts\pip.exe" install -r "%BACKEND_DIR%\requirements.txt"
)

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js and npm are required. Install from https://nodejs.org/
    pause
    exit /b 1
)

if not exist "%FRONTEND_DIR%\node_modules" (
    echo [Setup] Installing frontend dependencies...
    cd /d "%FRONTEND_DIR%"
    call npm install
    cd /d "%ROOT_DIR%"
)

if not exist "%BACKEND_DIR%\.env" (
    if not exist "%BACKEND_DIR%\.env.example" (
        echo [ERROR] Backend environment template is missing.
        pause
        exit /b 1
    )
    copy /Y "%BACKEND_DIR%\.env.example" "%BACKEND_DIR%\.env" >nul
    if errorlevel 1 (
        echo [ERROR] Could not create backend\.env from the development template.
        pause
        exit /b 1
    )
    echo [Setup] Created backend\.env from the development template.
)

echo [1/2] Starting FastAPI Backend on http://127.0.0.1:8001 ...
start "EcoSort AI - Backend" cmd /k "set ENVIRONMENT=development&&set ALLOW_DEV_AUTH=true&&set AUTH_PROVIDER=auto&&cd /d "%BACKEND_DIR%"&&"%PYTHON_EXE%" -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload"

echo [2/2] Starting Vite Frontend on http://127.0.0.1:5173 ...
start "EcoSort AI - Frontend" cmd /k "cd /d "%FRONTEND_DIR%" && npm run dev"

echo.
echo =================================================================
echo   Services successfully started!
echo   Frontend Web UI  : http://127.0.0.1:5173
echo   Backend API Gateway: http://127.0.0.1:8001
echo   API Documentation: http://127.0.0.1:8001/docs
echo   Health Check     : http://127.0.0.1:8001/health
echo.
echo   Admin Login: admin@ecosortai.com (any password)
echo =================================================================
echo Keep opened terminal windows running to maintain services.
echo.
pause
