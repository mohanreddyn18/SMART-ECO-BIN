# SMART ECO BIN — Windows Setup Guide

For production deployment of the original React/Vite + FastAPI application,
follow [docs/VERCEL_CLOUD_RUN_DEPLOYMENT.md](docs/VERCEL_CLOUD_RUN_DEPLOYMENT.md).
The `github-pages/` folder is a separate static preview and is not the full
application.

## Project layout

```text
SMART-ECO-BIN/
├── backend/       FastAPI API, authentication, routing, storage, and tests
├── frontend/      React + Vite application and API client
├── ml/            Model files, metadata, and training utilities
├── tests/         Python unittest suite
├── docs/          API, architecture, and model documentation
├── .env.example   Safe environment template
└── run_project.ps1
```

The existing layout is already separated by responsibility; no source, model,
dataset, or history files need to be moved to run the application.

## Prerequisites

- Windows PowerShell
- Python 3.11 or later
- Node.js 18 or later and npm

Do not share or commit `backend/.env`; it may contain local credentials.
`backend/.env.example` contains placeholders. Local development uses a JSON
ledger at `backend/data/classification_records.json`. Firestore is only used
when explicitly configured and valid credentials are available. Cloud image
storage is not verified/configured by this local setup.

## Quick start

From the repository root, run the launcher (or double-click it in File Explorer):

```powershell
.\run_project.bat
```

The batch file runs `run_project.ps1` with a process-scoped execution-policy
bypass, so no system policy change is required. The launcher installs
dependencies when needed, creates `backend/.env` from the safe template if it
is missing, reuses healthy services instead of starting duplicates, waits for
both services to respond, and opens the frontend. Keep the two service windows
open while using the app.

## Start the backend

Open PowerShell in the repository root:

```powershell
if (-not (Test-Path .\backend\.venv\Scripts\python.exe)) {
    py -3 -m venv .\backend\.venv
}
if (-not (Test-Path .\backend\.env)) {
    Copy-Item .\backend\.env.example .\backend\.env
}
Set-Location .\backend
$env:ENVIRONMENT = "development"
$env:ALLOW_DEV_AUTH = "true"
$env:AUTH_PROVIDER = "auto"
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

If imports fail because dependencies are missing, install them in this virtual
environment (CPU-only PyTorch is suitable for local development):

```powershell
.\.venv\Scripts\python.exe -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Check `http://127.0.0.1:8001/health`. A degraded status can still mean the API
is reachable; inspect `classifier_loaded`, `classifier_error`, and
`detector_loaded` before attempting inference.

## Start the frontend

Open a second PowerShell terminal in the repository root:

```powershell
Set-Location .\frontend
if (-not (Test-Path .\node_modules)) { npm ci }
npm run dev -- --host 127.0.0.1
```

The Vite development server proxies API requests to `127.0.0.1:8001`.

## Optional Gemini assistant setup

The Gemini assistant is separate from the original PyTorch classifier and
detector. It never receives the uploaded image; the optional explanation action
sends only the classifier's label, confidence, and disposal metadata.

1. Create a new key at [Google AI Studio API keys](https://aistudio.google.com/apikey).
   Revoke any previously exposed key; do not reuse it.
2. In a separate PowerShell window at the repository root, open the ignored
   backend environment file:

   ```powershell
   notepad .\backend\.env
   ```

3. Set `GEMINI_API_KEY` to the new key in that file. Keep it private; do not
   put it in `frontend/.env.local`, any `VITE_*` setting, or a committed file.
   The example model is `gemini-flash-latest`; the current official SDK is
   `google-genai` (`google-genai>=2.34.0,<3.0.0`).
4. Restart the backend. The WasteAI page and classification explanation button
   will report an unavailable service until the backend has a key. Gemini calls
   have a 20-second timeout and a best-effort per-instance request limit.

## Local URLs

- Web app: `http://127.0.0.1:5173/`
- Login: `http://127.0.0.1:5173/login`
- Image detection: `http://127.0.0.1:5173/detect`
- API health: `http://127.0.0.1:8001/health`
- Swagger API documentation: `http://127.0.0.1:8001/docs`
- OpenAPI schema: `http://127.0.0.1:8001/openapi.json`

Local development authentication is a demo flow, not production identity
verification. Do not use it as an account/password system in a deployed app.

## Model status and limitations

The working-tree classifier checkpoint matches the validated committed model.
The classifier and detector both loaded successfully in the existing local
backend virtual environment. No checkpoint replacement is needed.

The multi-object detector is a generic COCO detector with heuristic disposal
routing, not a validated waste-specific model. Review its output manually.
Successful model loading does not establish real-world waste-photo accuracy;
verify predictions with representative images before relying on them.
