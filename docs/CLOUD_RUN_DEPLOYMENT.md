# Google Cloud Run Deployment Architecture & Operations Guide

## SMART ECO BIN — Production Deployment

This guide outlines the production deployment architecture for **SMART ECO BIN** on Google Cloud Platform (GCP) using **Google Cloud Run** and **Google Cloud Firestore**.

---

## 1. System Architecture Overview

The application utilizes a stateless, serverless dual-container architecture designed for high availability, automatic scaling, and government-standard security:

```
[ Citizens & Municipal Clients ]
               │
               ▼ HTTPS (Port 443)
┌──────────────────────────────────────────────────────────────┐
│  Cloud Run Frontend Service (ecosort-frontend)               │
│  - Multi-stage build running unprivileged Nginx              │
│  - Serves pre-compiled React 18 / Vite single-page app      │
│  - Implements client-side routing & cache headers           │
└──────────────────────────────┬───────────────────────────────┘
                               │ API Requests (/api/*)
                               ▼ HTTPS (Port 443)
┌──────────────────────────────────────────────────────────────┐
│  Cloud Run Backend Gateway (ecosort-backend)                 │
│  - FastAPI Python 3.11 runtime (non-root appuser:10001)     │
│  - In-memory MobileNetV2 PyTorch 12-class neural inference  │
│  - Software-only digital segregation routing engine          │
│  - Scikit-Learn Isolation Forest anomaly detector           │
└──────────────┬───────────────────────────────┬───────────────┘
               │                               │
               ▼ ADC Authentication            ▼ Signed URLs (Optional)
┌──────────────────────────────┐ ┌──────────────────────────────┐
│  Google Cloud Firestore      │ │  Google Cloud Storage (GCS)  │
│  - Collection: waste_records │ │  - Bucket: private audit     │
│  - Distributed persistence   │ │  - Disabled by default       │
│  - Atomic idempotency check  │ │  - Zero-retention privacy    │
└──────────────────────────────┘ └──────────────────────────────┘
```

---

## 2. Least-Privilege IAM & Service Account Configuration

Do NOT deploy Cloud Run services under default editor or owner service accounts. Create a dedicated least-privilege Service Account.

### Step 2.1: Create Dedicated Service Account
```bash
gcloud iam service-accounts create smart-eco-bin-sa \
    --description="Least-privilege runtime service account for SMART ECO BIN" \
    --display-name="Smart Eco Bin Runtime SA"
```

### Step 2.2: Grant Minimum Required Roles
1. **Firestore Datastore User** (`roles/datastore.user`): Allows reading and writing to Firestore documents without database admin permissions.
   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
       --member="serviceAccount:smart-eco-bin-sa@PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/datastore.user"
   ```
2. **Cloud Storage Object Admin (Optional - only if GCS image archiving is enabled)**:
   ```bash
   gcloud storage buckets add-iam-policy-binding gs://BUCKET_NAME \
       --member="serviceAccount:smart-eco-bin-sa@PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/storage.objectUser"
   ```

---

## 3. Deployment Steps

### Step 3.1: Build and Deploy Backend Service
From the repository root directory:

```bash
# 1. Build and submit backend container to Google Artifact Registry (run from repository root)
gcloud builds submit \
    --tag gcr.io/PROJECT_ID/ecosort-backend:latest \
    -f backend/Dockerfile .

# 2. Deploy Backend to Cloud Run
# Initial conservative sizing: 1 CPU, 1-2 GiB memory, 1 worker process.
# This prevents PyTorch model memory contention and relies on Cloud Run horizontal autoscaling.
gcloud run deploy ecosort-backend \
    --image gcr.io/PROJECT_ID/ecosort-backend:latest \
    --platform managed \
    --region us-central1 \
    --service-account smart-eco-bin-sa@PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars STORAGE_PROVIDER=firestore,GOOGLE_CLOUD_PROJECT=PROJECT_ID,FIRESTORE_COLLECTION=waste_records,CORS_ORIGINS="https://ecosort-frontend-xyz.a.run.app" \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --allow-unauthenticated
```

Note the deployed backend URL (e.g. `https://ecosort-backend-xyz.a.run.app`).

### Step 3.2: Build and Deploy Frontend Service
From the `frontend/` directory:

```bash
# 1. Build frontend container with backend API URL injected
gcloud builds submit \
    --tag gcr.io/PROJECT_ID/ecosort-frontend:latest \
    --build-arg VITE_API_BASE_URL="https://ecosort-backend-xyz.a.run.app" \
    frontend/

# 2. Deploy Frontend to Cloud Run
gcloud run deploy ecosort-frontend \
    --image gcr.io/PROJECT_ID/ecosort-frontend:latest \
    --platform managed \
    --region us-central1 \
    --memory 256Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --allow-unauthenticated
```

> [!NOTE]
> **CORS Cross-Wiring**: After deploying the frontend, obtain its generated Cloud Run URL (e.g., `https://ecosort-frontend-xyz.a.run.app`) and update the backend's `CORS_ORIGINS` environment variable using `gcloud run services update ecosort-backend --update-env-vars CORS_ORIGINS="https://ecosort-frontend-xyz.a.run.app"`.

> [!IMPORTANT]
> **Administrative Security Pre-Production Gate**:
> Demonstration client-side authentication is included in this build for evaluation. Before opening administrative endpoints to untrusted public networks, an enterprise identity provider (such as Firebase Authentication or Google Cloud Identity Platform) must be configured with server-side bearer token validation. For initial secured testing, set `ADMIN_API_KEY` on the backend service.

---

## 4. Pre-Deployment Data Migration (Local to Firestore)

To migrate existing local records from `backend/data/classification_records.json` into Firestore:

```bash
# 1. Authenticate locally with Google Cloud ADC
gcloud auth application-default login

# 2. Configure target environment variables
export STORAGE_PROVIDER=firestore
export GOOGLE_CLOUD_PROJECT=PROJECT_ID

# 3. Perform dry-run preview (zero writes)
python backend/migrate_to_firestore.py --dry-run

# 4. Execute confirmed migration
python backend/migrate_to_firestore.py --confirm
```

---

## 5. Verification & Health Monitoring

### Backend Health Check:
```bash
curl https://ecosort-backend-xyz.a.run.app/health
```
Expected response:
```json
{
  "status": "healthy",
  "service": "EcoSort AI API Gateway",
  "version": "1.0.0",
  "model_loaded": true,
  "mode": "Software-Only (Pure Computational Intelligence)",
  "hardware_sensors": false,
  "storage_mode": "firestore"
}
```

### Storage Status Check:
```bash
curl https://ecosort-backend-xyz.a.run.app/api/storage/status
```
Expected response:
```json
{
  "mode": "firestore",
  "storage_backend": "FirestoreStorageProvider",
  "storage_file": null,
  "persistent_cloud_enabled": true,
  "cloud_provider": "Google Cloud Firestore",
  "record_count": 11,
  "idempotency_enabled": true,
  "project_id": "PROJECT_ID",
  "collection": "waste_records"
}
```

---

---

## 6. Authentication & Production Hardening Operations

### 6.1 Hardened Authentication Architecture
The backend gateway implements genuine server-side token validation and strict production startup verification:
- **Production Guardrails**: In production (`ENVIRONMENT=production`), development authentication (`ALLOW_DEV_AUTH=true`) is strictly prohibited. If set, container startup aborts immediately.
- **Secret Rejection**: Production startup rejects known public example secrets (`smart-eco-bin-local-dev-secret-key-32b`, `secret`, `changeme`, etc.) and development signing keys.
- **Zero Silent Fallback**: Token algorithm (`RS256` vs `HS256`) is inspected directly from the unverified header. If RS256 token verification fails against Firebase Admin, the request immediately fails with HTTP 401; it will **never** silently fall back to HMAC development token validation.
- **Algorithm Confusion Prevention**: Symmetric HS256 tokens are rejected unconditionally in production, preventing HMAC key substitution against asymmetric public certificates.
- **Safe Error Reporting**: Configuration and token errors describe the defect clearly without ever printing secret keys or sensitive hashes to logs or HTTP responses.

### 6.2 Complete Route Access Matrix
| Endpoint | Method | Classification | Minimum Role | Access Control & Privacy Rules |
|---|---|---|---|---|
| `/` | GET | Public Info | None (Public) | Welcome metadata & documentation |
| `/health` | GET | Public Probe | None (Public) | Liveness and readiness health probe |
| `/api/storage/status` | GET | Operational Info | None (Public) | Persistence telemetry; sanitizes filesystem paths |
| `/api/security/posture` | GET | Operational Info | None (Public) | Reports active verification & RBAC without exposing secrets |
| `/api/auth/verify` | POST | Authenticated | Citizen / Admin | Cryptographically validates bearer token |
| `/api/auth/me` | GET | Authenticated | Citizen / Admin | Returns verified server-side identity & claims |
| `/api/auth/demo-token` | POST | Development Only | Local Dev Only | Strictly **disabled (HTTP 403)** in production |
| `/api/predict` | POST | Public Citizen | None (Public) | Intake classification; rate-limited (30 req/min); binds `userId` |
| `/api/wasteai` | POST | Public Citizen | None (Public) | Citizen recycling knowledge assistant |
| `/api/history` | GET | Authenticated / Public | Optional / Citizen | Citizen: personal records only; Admin: full municipal audit |
| `/api/history/{id}` | GET | Authenticated / Public | Optional / Citizen | Citizen: own records only; Admin: any record; cross-tenant 403 |
| `/api/history/{id}` | DELETE | Privileged | `administrator` | Permanent record deletion (Citizens receive 403) |
| `/api/sanitation` | GET | Privileged | `administrator` | Municipal sanitation intelligence & fill indicators |
| `/api/anomalies` | GET | Privileged | `administrator` | Outlier telemetry & stream variance detection |
| `/api/predictive-insights` | GET | Privileged | `administrator` | Trend analysis (requires >= 100 samples) |
| `/api/sanitationai` | POST | Privileged | `administrator` | Operations assistant with grounded telemetry tool-calling |

### 6.3 Administrator Role Provisioning & Revocation Procedure
Administrative roles confer destructive capabilities (e.g., historical record deletion) and municipal operational intelligence.

#### 1. Provisioning via Firebase Custom Claims (Recommended for Production)
Execute server-side script using Firebase Admin SDK:
```python
import firebase_admin
from firebase_admin import auth

# Initialize with production service account
app = firebase_admin.initialize_app()

# Set authoritative administrative claims
auth.set_custom_user_claims(
    uid="TARGET_USER_FIREBASE_UID",
    {"admin": True, "role": "administrator"}
)
```

#### 2. Provisioning via Server-Side Whitelist (`ADMIN_EMAILS`)
For institutional administrators whose emails are verified:
```bash
gcloud run services update ecosort-backend \
    --region us-central1 \
    --update-env-vars ENVIRONMENT=production,ALLOW_DEV_AUTH=false,ADMIN_EMAILS="supervisor@sanitation.gov,director@city.gov"
```
> [!WARNING]
> In production, `ADMIN_EMAILS` cannot contain demo placeholders such as `admin@ecosortai.com` or `@example.com`. Such configurations fail startup immediately.

#### 3. Revocation Procedure
To immediately revoke administrator access:
1. Remove the custom claims:
   ```python
   auth.set_custom_user_claims(uid, {"admin": False, "role": "citizen"})
   ```
2. Force token revocation on Firebase:
   ```python
   auth.revoke_refresh_tokens(uid)
   ```
3. Remove the email from `ADMIN_EMAILS` if configured via whitelist, and redeploy.

### 6.4 Token Lifecycle and Browser Storage Considerations
- **Storage Tradeoffs**: The frontend stores bearer tokens in browser `localStorage`. While standard for decoupled Single Page Applications (SPAs) across distinct origins, this carries known Cross-Site Scripting (XSS) exposure. Strict Content Security Policy (CSP), subresource integrity, and sanitized innerHTML rendering are required. An `HttpOnly` cookie design requires a shared top-level domain between frontend and backend to support SameSite cookie exchange without cross-site blocking.
- **Session Termination vs Server Revocation**: Removing a token from browser storage terminates the local session immediately, but does not invalidate the underlying cryptographic signature. True immediate server-side revocation requires short token lifespans (e.g., 1 hour) paired with Firebase Admin `check_revoked=True` checks.

### 6.5 Rate Limiting & Abuse Protections
- **Per-Instance In-Memory Limiter**: `/api/predict` enforces a limit of 30 requests per minute per client key (authenticated `uid` or client IP).
- **Trusted Proxy Setting**: Client IP extraction strictly uses TCP socket peer IP (`request.client.host`) unless `TRUSTED_PROXIES` is explicitly set to the upstream Load Balancer IP, preventing `X-Forwarded-For` spoofing.
- **Architectural Limitation**: An in-memory rate limiter operates per container instance. In an autoscaling Cloud Run fleet, traffic distributed across multiple instances will have per-instance quotas. Distributed, cluster-wide rate limiting requires Google Cloud Armor edge security or an upstream Redis store.

### 6.6 Pre-Production Security Checklist
Before promoting to live public service:
- [ ] Set `ENVIRONMENT=production` and `ALLOW_DEV_AUTH=false`.
- [ ] Connect Firebase Authentication / Google Cloud Identity Platform with verified project ID.
- [ ] Configure `ADMIN_EMAILS` with verified institutional domains (e.g. `@sanitation.gov`).
- [ ] Enable `STORAGE_PROVIDER=firestore` with verified Workload Identity or Service Account.
- [ ] Restrict `CORS_ORIGINS` strictly to the custom domain of the frontend portal.
- [ ] Configure Google Cloud Armor edge WAF policies for distributed DDoS and rate limiting.

---

## 7. Staging Identity-Provider Integration & Validation Strategy

To prevent accidental production exposure and ensure zero-trust authorization, SMART ECO BIN enforces an explicit four-tier testing hierarchy:

1. **Unit & Specification-Mocked Tests (Automated CI)**:
   - Evaluates RS256 token verification, claims parsing, role assignment, and unverified email rejection using mathematically sound mock identity providers (`unittest.mock`).
   - Run via `python -m unittest discover -s tests -p "test_*.py"`.
   - *Boundary Marker*: Proves logic and defensive invariants against identity token specifications, but does NOT constitute proof of live identity-provider network integration.
2. **Local Firebase Auth Emulator Testing (Optional Pre-Staging)**:
   - Validates authentication paths against the official Google Firebase Emulator Suite running locally.
   - Requires Node.js and Java runtime (`firebase-tools`).
   - Startup command:
     ```bash
     # Install firebase-tools if not present
     npm install -g firebase-tools
     # Start Firebase Auth emulator on port 9099
     firebase emulators:start --only auth
     ```
   - Running backend against emulator:
     ```bash
     export FIREBASE_AUTH_EMULATOR_HOST="127.0.0.1:9099"
     export GOOGLE_CLOUD_PROJECT="demo-smart-eco-bin"
     export AUTH_PROVIDER="firebase"
     export ENVIRONMENT="development"
     python backend/main.py
     ```
   - *Security Guardrail*: `FIREBASE_AUTH_EMULATOR_HOST` is strictly rejected in `production` and `staging` environments (`SecurityConfigurationError`). Startup fails closed immediately if an emulator host is configured outside of local development/testing.
3. **Controlled Staging Identity Provider Validation (Pre-Production Gate)**:
   - Connects the backend and frontend to a dedicated, isolated Google Cloud staging project (`<STAGING_PROJECT_ID>`).
   - Exercises real OAuth2 / OIDC token issuance, email verification checks, and token revocation with real human users.
4. **Public Production Release**:
   - Only unlocked after all staging validation checklist items are completed and signed off.

### 7.1 Staging Identity-Provider Validation Checklist

> [!CAUTION]
> **DEPLOYMENT GATE: NOT READY FOR PUBLIC PRODUCTION**
> Public production deployment is strictly blocked until a human operator completes and verifies every item in this checklist against an isolated staging environment. Do not fabricate project IDs or credentials.

#### Step 1: Human Operator Staging Environment Configuration
- [ ] **Staging GCP Project Created**: Dedicated project `<STAGING_PROJECT_ID>` (distinct from any production project).
- [ ] **Firebase Authentication Enabled**: Email/Password and Google sign-in methods activated in `<STAGING_PROJECT_ID>`.
- [ ] **Authorized Staging Administrator Identity Created**:
  - Target Administrator Email: `<STAGING_ADMIN_EMAIL>` (e.g., `admin-staging@sanitation.yourcity.gov`).
  - Account email address must be marked **Verified** (`email_verified=true`) in Firebase Console.
- [ ] **Authorized Staging Citizen Identity Created**:
  - Target Citizen Email: `<STAGING_CITIZEN_EMAIL>` (e.g., `citizen-staging@example.org`).
- [ ] **Staging Backend Configuration**:
  ```bash
  ENVIRONMENT=staging
  AUTH_PROVIDER=firebase
  ALLOW_DEV_AUTH=false
  GOOGLE_CLOUD_PROJECT=<STAGING_PROJECT_ID>
  ADMIN_EMAILS="<STAGING_ADMIN_EMAIL>"
  STORAGE_PROVIDER=firestore
  FIRESTORE_COLLECTION=waste_records_staging
  CORS_ORIGINS="https://<STAGING_FRONTEND_DOMAIN>"
  ```

#### Step 2: Live Staging Boundary Verification
- [ ] **Check 1: Development Auth Fails Closed**:
  - Attempt to call `POST /api/auth/demo-token` on the staging backend.
  - Expected: HTTP 403 Forbidden (`Demo token generation is disabled`).
- [ ] **Check 2: Unverified Administrator Email Rejected**:
  - Register a new account `<UNVERIFIED_EMAIL>` matching the administrator domain but leave email unverified.
  - Call `GET /api/sanitation` with this token.
  - Expected: HTTP 403 Forbidden (RBAC rejects unverified email addresses).
- [ ] **Check 3: Verified Administrator Granted Access**:
  - Log in with `<STAGING_ADMIN_EMAIL>` (verified).
  - Call `GET /api/sanitation` and `GET /api/anomalies`.
  - Expected: HTTP 200 OK.
- [ ] **Check 4: Citizen Data Isolation**:
  - Submit a prediction under Citizen A's session (`<STAGING_CITIZEN_EMAIL>`).
  - Retrieve history under Citizen B's session.
  - Expected: Citizen B's `/api/history` contains zero records belonging to Citizen A.
  - Attempt `DELETE /api/history/{record_id}` with Citizen A's token.
  - Expected: HTTP 403 Forbidden.
- [ ] **Check 5: Revoked Token Handling**:
  - Trigger token revocation via Firebase Admin or user password change.
  - Immediate request to `/api/auth/me` with old token.
  - Expected: HTTP 401 Unauthorized (`Token has been revoked`).
- [ ] **Check 6: Cloud Storage Persistence**:
  - Verify records written to `waste_records_staging` collection in Google Cloud Console.
  - Confirm uploaded image payloads are NOT stored in Firestore or filesystem (zero retention verified).


