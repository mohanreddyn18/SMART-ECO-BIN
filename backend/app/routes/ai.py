from fastapi import APIRouter, Depends
from app.models.schemas import AIQueryRequest, WasteAIResponse, SanitationAIResponse
from app.ai.gemini_client import gemini_service
from app.services.analytics_service import analytics_service
from app.analytics.anomaly_detector import anomaly_detector
from app.utils.helpers import get_current_iso_time
from app.auth.dependencies import require_admin, get_optional_current_user
from app.auth.models import AuthenticatedUser
from typing import Optional

router = APIRouter(tags=["AI Assistants"])

@router.post("/wasteai", response_model=WasteAIResponse)
async def query_waste_ai(
    request: AIQueryRequest,
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_current_user)
):
    """
    Public citizen waste disposal knowledge assistant.
    Provides verified recycling directives and material advice.
    """
    reply = gemini_service.query_waste_ai(request.prompt)
    return {
        "reply": reply,
        "timestamp": get_current_iso_time(),
        "source": "WasteAI Knowledge Assistant"
    }

@router.post("/sanitationai", response_model=SanitationAIResponse)
async def query_sanitation_ai(
    request: AIQueryRequest,
    admin_user: AuthenticatedUser = Depends(require_admin)
):
    """
    Municipal sanitation operations AI assistant with grounded tool calling.
    Access Restricted: Requires verified administrator role.
    """
    telemetry = {
        "analytics": analytics_service.get_macro_analytics(),
        "sanitation": analytics_service.get_sanitation_posture(),
        "anomalies": anomaly_detector.get_active_anomalies()
    }
    result = gemini_service.query_sanitation_ai(request.prompt, telemetry)
    return {
        "reply": result["reply"],
        "function_called": result.get("function_called"),
        "telemetry_grounded": True,
        "timestamp": get_current_iso_time()
    }
