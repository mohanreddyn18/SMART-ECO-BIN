from fastapi import APIRouter, Depends
from app.services.analytics_service import analytics_service
from app.models.schemas import SanitationResponse
from app.auth.dependencies import require_admin
from app.auth.models import AuthenticatedUser

router = APIRouter(tags=["Sanitation"])

@router.get("/sanitation", response_model=SanitationResponse)
async def get_sanitation_intelligence(admin_user: AuthenticatedUser = Depends(require_admin)):
    """
    Returns pure software-computed sanitation status and indicators (No IoT/Hardware sensors).
    Access Restricted: Requires verified administrator role.
    """
    return analytics_service.get_sanitation_posture()
