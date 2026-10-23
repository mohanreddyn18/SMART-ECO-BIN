# RJ 147 — EcoSort AI Setup & Execution Manual

This guide describes how to run both the frontend and backend servers locally.

---

## Prerequisites

- **Node.js**: v18+ (tested with Node v24.19.0)
- **Python**: v3.10+ (tested with Python 3.10.21)
- **Model Checkpoint**: Ensure `ml/model/waste_model.pth` exists in the repository.

---

## 1. Environment Configuration

Copy the example environment file:
```bash
cp .env.example .env
```

Set the appropriate keys (optional for local testing; default emulation handles missing keys gracefully):
```ini
GEMINI_API_KEY=your_gemini_api_key_here
FIREBASE_CREDENTIALS_PATH=
FIREBASE_STORAGE_BUCKET=ecosort-ai.appspot.com
```

---

## 2. Backend Setup & Startup

1. Open PowerShell and navigate to the backend directory:
   ```powershell
   cd RJ147-Smart-Waste/backend
   ```

2. If using `uv`:
   ```powershell
   uv venv --python 3.10 .venv
   uv pip install -r requirements.txt --python .venv/Scripts/python.exe
   ```

3. Launch the FastAPI server:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
   ```

4. Verify backend health:
   ```powershell
   curl http://127.0.0.1:8000/health
   ```
   Interactive Swagger docs are available at: `http://127.0.0.1:8000/docs`

---

## 3. Frontend Setup & Startup

1. Open a new PowerShell terminal and navigate to the frontend:
   ```powershell
   cd RJ147-Smart-Waste/frontend
   ```

2. Install dependencies:
   ```powershell
   npm install
   ```

3. Start the Vite development server:
   ```powershell
   npm run dev
   ```

4. Open your browser at:
   ```
   http://127.0.0.1:5173
   ```

---

## 4. Default Demo Accounts

For offline and initial presentation testing, the following accounts are pre-configured:

- **Researcher / User Role**:
  - Email: `demo@ecosortai.com`
  - Password: `password123` (or any valid 6+ character password)
- **Administrator Role**:
  - Email: `admin@ecosortai.com`
  - Password: `adminpassword`
