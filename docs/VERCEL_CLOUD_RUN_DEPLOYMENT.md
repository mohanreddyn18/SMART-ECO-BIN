# Deploy the original SMART ECO BIN application

This deploys the existing React/Vite application and FastAPI backend. It does
not deploy the separate `github-pages/` browser-only preview.

## What goes where

| Component | Source | Hosting |
|---|---|---|
| Original website, routes, pages, upload UI | `frontend/` | Vercel |
| REST API and application routes | `backend/` | Google Cloud Run |
| Classifier and object detector weights | `ml/model/` | Included in the backend Docker image |
| Persistent classification history | Firestore | Google Cloud project |
| Optional WasteAI/SanitationAI generation | FastAPI backend | Gemini API key stored in Secret Manager |

The root `vercel.json` builds `frontend/` and publishes its Vite output. Set
Vercel's project Root Directory to the repository root. Do not select
`github-pages/` as the Vercel root. Alternatively, if using `frontend/` as the
Vercel Root Directory, remove/ignore the root Vercel config in that Vercel
project and use `frontend/vercel.json`.

## 1. Prepare Firebase Authentication and Firestore

1. Create or select a Google Cloud/Firebase project.
2. In Firebase Console, enable **Authentication → Email/Password**.
3. Create a Firebase Web App and note its API key, Auth domain, project ID, and
   app ID. The Web App configuration is public client configuration; never put
   a Gemini key, service-account key, or other server credential in a `VITE_*`
   variable.
4. In Firebase Authentication settings, add the final Vercel production domain
   (for example, `your-project.vercel.app`) to Authorized domains.
5. Create a Firestore database in Native mode. The backend will use Cloud Run's
   service identity (Application Default Credentials), not a downloaded JSON
   key.

## 2. Configure Gemini AI safely (optional)

WasteAI and SanitationAI call Gemini only from the FastAPI backend. The existing
MobileNetV2 classifier and object detector remain the only image inference
pipeline; the Gemini explanation feature receives a small JSON result summary,
never the uploaded image. Gemini text is clearly labeled as AI-generated and
does not replace model output or backend analytics.

1. Open [Google AI Studio API keys](https://aistudio.google.com/apikey), create
   a new key, and keep it private. Revoke any previously exposed key; do not
   reuse it.
2. For local development, open `backend/.env` and set `GEMINI_API_KEY` to the
   new key. This file is ignored by Git. Never put this value in a `VITE_*`
   variable, a frontend file, or either `.env.example`.
3. The default model is `gemini-flash-latest`, using Google's current
   `google-genai` Python SDK (`google-genai>=2.34.0,<3.0.0`). See Google's
   [official Python SDK](https://github.com/googleapis/python-genai) and
   [Gemini API model catalog](https://ai.google.dev/gemini-api/docs/models).
   `GEMINI_MODEL` may select another model available to your API key.
4. For Cloud Run, create a Secret Manager secret named `gemini-api-key` and
   add the new key as its secret value in the Google Cloud Console. Then grant
   the runtime service account access and attach it to the service:

   ```powershell
   gcloud secrets add-iam-policy-binding gemini-api-key --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/secretmanager.secretAccessor"
   gcloud run services update $SERVICE --region $REGION --update-secrets=GEMINI_API_KEY=gemini-api-key:latest --update-env-vars="GEMINI_MODEL=gemini-flash-latest,GEMINI_REQUEST_TIMEOUT_SECONDS=20"
   ```

The backend times out Gemini requests after 20 seconds, caps generated output,
returns generic errors rather than provider details, and limits each user or
observed client IP to 10 requests per minute per running instance. This
in-process limit is not a global quota across Cloud Run instances; use an API
gateway or Cloud Armor if you need a centrally enforced public quota. A blank
key leaves the assistants unavailable rather than generating mock answers.

## 3. Deploy the backend to Cloud Run

Install Docker Desktop and the Google Cloud CLI, sign in, and select the target
project. Run the following in PowerShell from the repository root; replace the
example values with your own:

```powershell
$PROJECT_ID = "your-google-cloud-project-id"
$REGION = "us-central1"
$REPOSITORY = "smart-eco-bin"
$SERVICE = "ecosort-backend"
$SERVICE_ACCOUNT_NAME = "smart-eco-bin-runtime"
$ADMIN_EMAIL = "your-verified-admin@example.org"

gcloud config set project $PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com firestore.googleapis.com firebase.googleapis.com identitytoolkit.googleapis.com secretmanager.googleapis.com
gcloud artifacts repositories create $REPOSITORY --repository-format=docker --location=$REGION
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME --display-name="SMART ECO BIN Cloud Run runtime"
$SERVICE_ACCOUNT = "$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/datastore.user"
gcloud projects add-iam-policy-binding $PROJECT_ID --member="serviceAccount:$SERVICE_ACCOUNT" --role="roles/firebaseauth.viewer"
gcloud auth configure-docker "$REGION-docker.pkg.dev"

$IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/backend:initial"
docker build -f backend/Dockerfile -t $IMAGE .
docker push $IMAGE
```

Deploy with a temporary HTTPS origin because the Vercel origin is not known
until Vercel has created the project URL. This placeholder is not a real
allowed site; update it in step 3:

```powershell
gcloud run deploy $SERVICE --image $IMAGE --region $REGION --service-account $SERVICE_ACCOUNT --allow-unauthenticated --port 8080 --memory 2Gi --cpu 2 --timeout 300 --set-env-vars "^~^ENVIRONMENT=production~ALLOW_DEV_AUTH=false~AUTH_PROVIDER=firebase~STORAGE_PROVIDER=firestore~GOOGLE_CLOUD_PROJECT=$PROJECT_ID~FIRESTORE_COLLECTION=waste_records~ADMIN_EMAILS=$ADMIN_EMAIL~CORS_ORIGINS=https://placeholder.invalid~GEMINI_MODEL=gemini-flash-latest~GEMINI_REQUEST_TIMEOUT_SECONDS=20"
$BACKEND_URL = gcloud run services describe $SERVICE --region $REGION --format="value(status.url)"
Invoke-RestMethod "$BACKEND_URL/health"
```

Set `ADMIN_EMAIL` to a real account that exists in Firebase and has a verified
email address. Do not use the example admin identity from local development.
Cloud Run's service account needs Firestore access and Firebase Authentication
user-read access. Keep the service public at the HTTP layer so the browser can
reach it; application endpoints enforce Firebase token verification and
administrator authorization.

Follow step 2 to attach the optional Gemini secret. Without it, AI assistant
endpoints report that the service is unavailable; they do not return simulated
Gemini answers.

## 4. Deploy the original frontend to Vercel

1. Import `mohanreddyn18/SMART-ECO-BIN` in Vercel.
2. Keep **Root Directory** as `./` (the repository root). Vercel uses the root
   `vercel.json` to install dependencies in `frontend/`, run the Vite build,
   and publish `frontend/dist`.
3. Add these Production Environment Variables in Vercel. Use the values from
   your Firebase Web App and the Cloud Run URL printed above:

   | Variable | Value |
   |---|---|
   | `VITE_API_BASE_URL` | `$BACKEND_URL` (HTTPS origin only; no trailing slash and no `/api`) |
   | `VITE_FIREBASE_API_KEY` | Firebase Web App API key |
   | `VITE_FIREBASE_AUTH_DOMAIN` | e.g. `your-project-id.firebaseapp.com` |
   | `VITE_FIREBASE_PROJECT_ID` | Firebase/Google Cloud project ID |
   | `VITE_FIREBASE_APP_ID` | Firebase Web App app ID |

   Do not add `GEMINI_API_KEY` to Vercel. It belongs only in backend local
   environment configuration or Google Cloud Secret Manager.

4. Deploy the Vercel project. The resulting `https://<project>.vercel.app/` URL
   serves the original landing page and React application; Vercel may also show
   a stable production alias under **Domains**.
5. Set the exact production site origin on Cloud Run:

   ```powershell
   $FRONTEND_ORIGIN = "https://your-project.vercel.app"
   gcloud run services update $SERVICE --region $REGION --update-env-vars "CORS_ORIGINS=$FRONTEND_ORIGIN"
   ```

6. Open the production URL and test login, registration, image classification,
   mixed-object detection, history, analytics, sanitation, anomalies, and
   predictive insights. Check `$BACKEND_URL/health` for model status.
   To test Gemini, use the WasteAI page and the optional explanation button on
   a completed classification. The health endpoint reports whether a server
   key is configured; it does not reveal the key.

For Vercel preview deployments on additional domains, add each exact HTTPS
origin to `CORS_ORIGINS` deliberately and redeploy the backend. Wildcards,
HTTP origins, paths, and localhost are rejected for production/staging CORS.

## Authentication and data notes

- Production login/register uses Firebase Email/Password authentication. Enable
  that provider in Firebase Console and add the deployed domain to Authorized
  domains. The browser sends Firebase ID tokens; the backend verifies them
  using Firebase Admin and Cloud Run Application Default Credentials.
- Administrator access requires a verified email that is explicitly listed in
  the backend's `ADMIN_EMAILS`, or trusted administrator custom claims when no
  email allowlist is configured. The directory is read-only; role changes must
  be made by an authorized Firebase/backend administrator.
- Set a unique `ADMIN_EMAILS` allowlist. Do not leave it empty in a public
  production service unless custom claims are intentionally provisioned.
- Production storage must use Firestore. Do not rely on Cloud Run's local
  filesystem for user history; local JSON storage is for development only.
- Local `.env` values and Cloud Run secrets belong in their respective local
  environment or provider secret stores. Do not commit credentials.
- Do not use a previously exposed Gemini key. Create a replacement and revoke
  the old key in Google AI Studio.

## GitHub Pages clarification

`github-pages/` is a separate, optional browser-only preview. It does not host
the original React app, FastAPI APIs, Firestore data, or backend AI. The
workflow `.github/workflows/github-pages.yml` now only builds that directory
manually and stores a downloadable artifact; it has no automatic push trigger
and no GitHub Pages deployment step.

This repository's existing Pages URL may continue showing a previously
published static build until Pages is disabled in repository **Settings →
Pages**. Disable that Pages publishing configuration if you do not want the
static preview served at all. The original full application's public URL is
the Vercel production domain created in step 3, not the GitHub Pages URL.

## Deployment automation

The GitHub Actions workflow only deploys the backend when manually run with
`deploy_confirmed=true`. Configure GitHub Actions variables for
`GCP_PROJECT_ID`, `GCP_REGION`, `ARTIFACT_REPO`, `GCP_SERVICE_ACCOUNT`,
`GCP_WORKLOAD_IDENTITY_PROVIDER`, `FRONTEND_ORIGIN`, `ADMIN_EMAILS`,
plus Google Workload Identity Federation permissions. Configure the
`VITE_FIREBASE_*` and `VITE_API_BASE_URL` variables in Vercel itself. This
workflow does not deploy
the frontend; Vercel handles the frontend separately. No deploy is performed
by following this guide until you run the commands or approve the workflow.
