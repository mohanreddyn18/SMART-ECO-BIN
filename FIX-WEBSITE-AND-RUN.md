# SMART ECO BIN — VS Code Run and Website Fix Checklist

## Local development (Windows)

1. Install Python 3.11+ and Node.js LTS.
2. At the repository root run `Copy-Item .env.example backend/.env`.
3. Backend terminal:
   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
   pip install -r requirements.txt
   $env:ENVIRONMENT="development"; $env:ALLOW_DEV_AUTH="true"; $env:AUTH_PROVIDER="auto"
   python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload
   ```
4. A second terminal, from repository root:
   ```powershell
   cd frontend
   npm ci
   npm run dev
   ```
5. Open `http://localhost:5173`; test backend at `http://127.0.0.1:8001/health` and API docs at `http://127.0.0.1:8001/docs`.

Keep both terminals open. Local `.env` must be at `backend/.env` because Uvicorn is started from `backend/`.

## Public deployment

GitHub Pages can publish static frontend files only. It cannot run Python/FastAPI or load the PyTorch models. Deploy the frontend to Vercel and backend to Google Cloud Run (or another Python host).

- Vercel root-directory deployment: Root Directory = repository root, Build Command = `cd frontend && npm ci && npm run build`, Output Directory = `frontend/dist`.
- Vercel frontend-root deployment: Root Directory = `frontend`, Build Command = `npm run build`, Output Directory = `dist`.
- Set the Vercel frontend build environment variable `VITE_API_BASE_URL` to the backend HTTPS origin only, without `/api` and without a trailing slash.
- Set backend `CORS_ORIGINS` to the exact public frontend origin.
- Redeploy frontend after changing environment variables.
- Production must not use development auth: never set `ALLOW_DEV_AUTH=true`; configure real Firebase/OIDC identity and an actual authorized-admin allowlist.
- Never commit `.env`, API keys, private keys, or service-account JSON.
