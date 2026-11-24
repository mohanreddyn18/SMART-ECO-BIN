import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request
from app.models.schemas import AIQueryRequest, WasteAIResponse, SanitationAIResponse
from app.ai.gemini_client import GeminiServiceUnavailable, gemini_service
from app.services.analytics_service import analytics_service
from app.analytics.anomaly_detector import anomaly_detector
from app.utils.helpers import get_current_iso_time
from app.auth.dependencies import require_admin, get_optional_current_user
from app.auth.models import AuthenticatedUser
from app.routes.predict import get_client_ip
from typing import Optional

router = APIRouter(tags=["AI Assistants"])

_GEMINI_RATE_LIMIT_REQUESTS = 10
_GEMINI_RATE_LIMIT_WINDOW_SECONDS = 60
_gemini_request_timestamps = defaultdict(list)


def clear_gemini_rate_limits():
    _gemini_request_timestamps.clear()


def check_gemini_rate_limit(identity: str):
    now = time.monotonic()
    recent_requests = [
        timestamp
        for timestamp in _gemini_request_timestamps[identity]
        if now - timestamp < _GEMINI_RATE_LIMIT_WINDOW_SECONDS
    ]
    if len(recent_requests) >= _GEMINI_RATE_LIMIT_REQUESTS:
        _gemini_request_timestamps[identity] = recent_requests
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Gemini request limit reached. Please wait before trying again.",
        )
    recent_requests.append(now)
    _gemini_request_timestamps[identity] = recent_requests


@router.post("/wasteai", response_model=WasteAIResponse)
async def query_waste_ai(
    request: Request,
    payload: AIQueryRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_current_user)
):
    """
    Public citizen waste disposal knowledge assistant.
    Provides verified recycling directives and material advice.
    """
    identity = (
        f"user:{current_user.uid}"
        if current_user
        else f"ip:{get_client_ip(request)}"
    )
    check_gemini_rate_limit(identity)

    try:
        classification_result = (
            payload.classification_result.model_dump(mode="json")
            if payload.classification_result
            else None
        )
        reply = await gemini_service.query_waste_ai(
            payload.prompt,
            classification_result,
        )
    except GeminiServiceUnavailable as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    return {
        "reply": reply,
        "timestamp": get_current_iso_time(),
        "source": "WasteAI Knowledge Assistant"
    }

@router.post("/sanitationai", response_model=SanitationAIResponse)
async def query_sanitation_ai(
    payload: AIQueryRequest,
    admin_user: AuthenticatedUser = Depends(require_admin)
):
    """
    Municipal sanitation operations assistant grounded in a verified telemetry snapshot.
    Access Restricted: Requires verified administrator role.
    """
    telemetry = {
        "analytics": analytics_service.get_macro_analytics(),
        "sanitation": analytics_service.get_sanitation_posture(),
        "anomalies": anomaly_detector.get_active_anomalies()
    }
    check_gemini_rate_limit(f"user:{admin_user.uid}")

    try:
        result = await gemini_service.query_sanitation_ai(payload.prompt, telemetry)
    except GeminiServiceUnavailable as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    return {
        "reply": result["reply"],
        "function_called": result.get("function_called"),
        "telemetry_grounded": True,
        "timestamp": get_current_iso_time()
    }
