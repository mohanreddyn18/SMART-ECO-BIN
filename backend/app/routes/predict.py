import time
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Header, Depends, Request, status
from app.services.model_service import classifier_service
from app.services.analytics_service import analytics_service
from app.models.schemas import PredictionResponse
from app.auth.dependencies import get_optional_current_user
from app.auth.models import AuthenticatedUser

router = APIRouter(tags=["Classification"])

import os

# Lightweight per-instance rate limiter (30 image classifications per minute per client)
# Note: In multi-instance Cloud Run, each container enforces its local concurrency guard.
# Distributed abuse prevention requires upstream Google Cloud Armor or Redis.
_rate_limit_records = defaultdict(list)
RATE_LIMIT_MAX_REQUESTS = 30
RATE_LIMIT_WINDOW_SECONDS = 60


def clear_rate_limits():
    """Resets in-memory rate limit records (used in test isolation)."""
    _rate_limit_records.clear()


def get_client_ip(request: Request) -> str:
    """
    Safely resolves client IP.
    By default, relies on request.client.host (the direct TCP connection).
    Only trusts X-Forwarded-For if TRUSTED_PROXIES is configured and the peer matches.
    Prevents arbitrary client IP spoofing via manipulated headers.
    """
    peer_ip = request.client.host if request.client else "127.0.0.1"
    trusted_proxies_env = os.getenv("TRUSTED_PROXIES", "").strip()
    if trusted_proxies_env:
        trusted_proxies = {p.strip() for p in trusted_proxies_env.split(",") if p.strip()}
        if peer_ip in trusted_proxies:
            forwarded = request.headers.get("x-forwarded-for")
            if forwarded:
                client_ip = forwarded.split(",")[0].strip()
                if client_ip:
                    return client_ip
    return peer_ip


def check_rate_limit(client_id: str):
    now = time.time()
    timestamps = _rate_limit_records[client_id]
    valid_timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW_SECONDS]
    if len(valid_timestamps) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: Maximum {RATE_LIMIT_MAX_REQUESTS} classifications per minute. Please retry shortly."
        )
    valid_timestamps.append(now)
    _rate_limit_records[client_id] = valid_timestamps


@router.post("/predict", response_model=PredictionResponse)
async def predict_waste(
    request: Request,
    file: UploadFile = File(...),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_current_user)
):
    """
    Accepts an uploaded image, processes it through MobileNetV2,
    returns authoritative waste segregation directives, and persists
    an auditable event into the unified ledger with verified citizen ownership.
    """
    # 0. Apply per-client rate limit
    client_ip = get_client_ip(request)
    rate_limit_key = current_user.uid if current_user else f"ip:{client_ip}"
    check_rate_limit(rate_limit_key)

    # 1. Validate content type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid image type. Accepted: JPEG, PNG, WEBP.")

    # 2. Read image contents and validate size (Max 10 MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image size exceeds 10MB limit.")

    # 3. Model inference
    try:
        result = classifier_service.predict_image_bytes(contents)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Model unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Image preprocessing or model inference failed: {str(e)}")

    # 4. Generate stable event record with citizen ownership
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    unique_suffix = uuid.uuid4().hex[:6]
    record_id = f"REC-{ts}-{unique_suffix}"
    user_id = current_user.uid if current_user else "public-citizen"

    history_entry = {
        "id": record_id,
        "itemName": f"Intake Sample ({file.filename})",
        "predictedClass": result["predictedClass"],
        "wasteType": result["wasteType"],
        "confidence": result["confidence"],
        "recommendation": result["recommendation"],
        "disposalBin": result.get("disposalBin"),
        "destinationCompartment": result.get("destinationCompartment"),
        "compartmentId": result.get("compartmentId"),
        "routingStatus": result.get("routingStatus"),
        "routingReason": result.get("routingReason"),
        "requiresManualReview": result.get("requiresManualReview", False),
        "simulationStatus": "SIMULATED",
        "timestamp": result["timestamp"],
        "userId": user_id
    }

    # Persist via single unified analytics & storage service
    analytics_service.add_record(history_entry, idempotency_key=x_idempotency_key)

    return PredictionResponse(**result)
