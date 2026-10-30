# Smart Eco Bin — GitHub Pages edition

This is a separate, static React/Vite website for GitHub Pages. It does not
start or call the original FastAPI backend. The original `frontend/`, `backend/`,
and model source remain in the repository unchanged by this standalone edition.

## What works here

- Responsive overview, image upload with drag and drop, image preview, local
  classification history, analytics, sanitation indicators, anomaly review,
  and predictive-readiness pages.
- A local display profile is optional and is not secure authentication.
- Single-image classification is intended to run in the browser with the
  exported MobileNetV2 ONNX model and ONNX Runtime Web (WebAssembly). Images are
  decoded and processed locally; they are not sent to an external service.
- History is stored in this browser's `localStorage`; it does not sync to other
  browsers or devices.

The classifier recognizes the existing twelve labels but is not a general
object detector. Mixed-waste bounding boxes and backend-generated municipal
analytics are not available in this static version. Accuracy claims from the
training metadata are not independently validated by this website.

## Local development

```powershell
Set-Location github-pages
npm ci
npm run dev
```

Build and preview:

```powershell
npm run build
npm run preview
```

The ONNX model is generated from the repository's existing classifier checkpoint
with `scripts/export_model.py`; it is checked into `public/models/` for the
browser to load. To avoid changing the original backend environment, install
export dependencies in a separate Python environment:

```powershell
py -3.12 -m venv .venv-export
.\.venv-export\Scripts\python.exe -m pip install -r github-pages\requirements-export.txt
.\.venv-export\Scripts\python.exe github-pages\scripts\export_model.py
```

Verify ONNX Runtime Web CPU inference with `npm run test:model`.

## GitHub Pages configuration

The repository is `mohanreddyn18/SMART-ECO-BIN`, so the project-site base path
is `/SMART-ECO-BIN/`, set in `vite.config.js`. The workflow at
`.github/workflows/github-pages.yml` builds `github-pages/` and deploys its
`dist/` output. Enable **Settings → Pages → Build and deployment → GitHub
Actions**. After explicitly pushing the workflow and site, the URL format is:

`https://mohanreddyn18.github.io/SMART-ECO-BIN/`

No deploy or push is performed by preparing this directory.
