# RJ 147 — EcoSort AI API Documentation

The local backend service listens at `http://127.0.0.1:8001` in this workspace.  
All public endpoints are documented with OpenAPI schemas at `/docs`.

---

## Endpoint Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status and pure-software validation |
| `POST` | `/api/predict` | Upload image for MobileNetV2 waste classification |
| `GET` | `/api/history` | Retrieve classification audit records |
| `GET` | `/api/analytics` | Macro waste distribution and 7-day intake volume |
| `GET` | `/api/sanitation` | Software-computed sanitation intelligence posture |
| `GET` | `/api/anomalies` | Admin-only, threshold-based checks over recent classification records |
| `GET` | `/api/predictive-insights`| Authenticated, scoped exploratory trend and data sufficiency audit |
| `POST` | `/api/wasteai` | Gemini-generated recycling guidance and optional classifier-result explanation |
| `POST` | `/api/sanitationai` | Admin-only Gemini explanation of an actual backend telemetry snapshot |

---

## Detailed Specifications

### 1. Health Check
- **Route:** `GET /health`
- **Response:**
  ```json
  {
    "status": "healthy",
    "service": "EcoSort AI API Gateway",
    "version": "1.0.0",
    "mode": "Software-Only (Pure Computational Intelligence)",
    "hardware_sensors": false
  }
  ```

### 2. Waste Classification Inference
- **Route:** `POST /api/predict`
- **Content-Type:** `multipart/form-data`
- **Parameters:** `file` (Binary image file: JPEG, PNG, or WEBP; Max 10MB)
- **Authentication:** Optional in local/development configurations. Stored events are scoped to the verified account when a valid token is supplied; otherwise they are recorded as public-citizen events.
- **Response:**
  ```json
  {
    "predictedClass": "plastic",
    "confidence": 96.82,
    "wasteType": "Recyclable / Dry Waste",
    "recommendation": "Empty and rinse container. Place in Blue Plastic Recycling Bin.",
    "disposalBin": "Blue Plastic Recycling Bin",
    "timestamp": "2026-09-25T11:42:00Z",
    "model": "MobileNetV2 (12-class image classifier)",
    "isDemo": false
  }
  ```

### 3. Data-driven Sanitation Intelligence
- **Route:** `GET /api/sanitation`
- **Authorization:** Requires a verified administrator identity.
- **Data:** Uses classification-event records only. It does not report bin fill levels, connected sensors, or physical locations.
- **Response:**
  ```json
  {
    "currentStatus": "UNAVAILABLE",
    "reason": "No classification events recorded.",
    "hardwareSensors": false,
    "telemetrySource": "Software Classification Ledger (Zero IoT Hardware)",
    "supportingIndicators": [],
    "locationSignals": [],
    "recommendations": ["Submit classification events to establish a record-based baseline."]
  }
  ```

### 4. Anomaly Detection
- **Route:** `GET /api/anomalies`
- **Authorization:** Requires a verified administrator identity.
- **Method:** After at least 10 events, checks the latest 20 records for a hazardous-stream share of at least 20% or at least 3 classifications below 60% confidence. These deterministic rules are not an Isolation Forest model and do not use sensor or location data.
- **Response:**
  ```json
  {
    "status": "Awaiting Telemetry",
    "totalAnomalies": 0,
    "algorithm": "Rule-based checks on recent classification records",
    "anomalies": [],
    "message": "Insufficient historical observations for threshold checks (0/10 events logged).",
    "recordsSampled": 0
  }
  ```

### 5. Predictive Insights
- **Route:** `GET /api/predictive-insights`
- **Authorization:** Requires a verified user. Citizens are scoped to their own records; verified administrators receive system-wide scope.
- **Policy:** Requires at least 100 timestamped events spanning at least 30 distinct dates. Missing dates in the most recent 30-day window are treated as zero for the trend calculation.
- **Method:** Ordinary least-squares linear trend over daily event counts, projected 7 days. Exploratory only; not independently validated.
- **Response (< Threshold):**
  ```json
  {
    "sufficientData": false,
    "currentSamples": 0,
    "requiredSamples": 100,
    "currentEvents": 0,
    "requiredEvents": 100,
    "observationDays": 0,
    "requiredDays": 30,
    "readinessPct": 0.0,
    "scope": "personal",
    "generatedAt": "ISO-8601 timestamp",
    "message": "Insufficient historical telemetry for an exploratory trend.",
    "projections": null,
    "forecast": null
  }
  ```

### 6. Gemini AI Assistants

- **WasteAI:** `POST /api/wasteai`, public with optional verified user context.
- **SanitationAI:** `POST /api/sanitationai`, requires a verified administrator.
- **Request body:** Both accept a `prompt` string (1-2000 characters). WasteAI
  also accepts optional classifier metadata. The metadata is descriptive only;
  it does not change the result, and uploaded image bytes are never sent to
  Gemini.
  ```json
  {
    "prompt": "Explain this classifier result.",
    "classification_result": {
      "predicted_class": "battery",
      "confidence": 92.5,
      "waste_type": "Hazardous / E-Waste",
      "recommendation": "Use a designated battery collection point.",
      "disposal_bin": "Hazardous Waste Depot",
      "requires_manual_review": true
    }
  }
  ```
- **Provenance:** Gemini text is AI-generated, not another classification or
  authoritative local disposal rule. SanitationAI can only describe the
  telemetry JSON supplied by the backend; the application has no physical
  sensors.
- **Limits and errors:** The backend uses `GEMINI_API_KEY` from its server
  environment, defaults to `gemini-flash-latest`, enforces a 20-second timeout,
  limits requests to 10/minute per user or observed client IP per instance,
  and returns HTTP 503 when Gemini is unconfigured or unavailable. Provider
  exception details are not returned to callers.
