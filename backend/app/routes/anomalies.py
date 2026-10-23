from fastapi import APIRouter, Depends
from app.analytics.anomaly_detector import MINIMUM_EVENTS, anomaly_detector
from app.models.schemas import AnomalyResponse
from app.services.storage_service import storage_service
from app.auth.dependencies import require_admin
from app.auth.models import AuthenticatedUser

router = APIRouter(tags=["Anomalies"])

@router.get("/anomalies", response_model=AnomalyResponse)
async def get_anomalies(admin_user: AuthenticatedUser = Depends(require_admin)):
    """
    Returns threshold-based checks derived from stored classification records.
    Access Restricted: Requires verified administrator role.
    """
    record_count = storage_service.count_records()
    anomalies = anomaly_detector.get_active_anomalies()

    if record_count < MINIMUM_EVENTS:
        status = "Awaiting Telemetry"
        msg = f"Insufficient historical observations for threshold checks ({record_count}/{MINIMUM_EVENTS} events logged)."
    elif len(anomalies) > 0:
        status = "Active Attention"
        msg = f"Identified {len(anomalies)} statistical anomalies across recent stream intake."
    else:
        status = "Nominal"
        msg = "Stream distribution and classification velocities are within nominal bounds."

    return {
        "status": status,
        "totalAnomalies": len(anomalies),
        "algorithm": "Rule-based checks on recent classification records",
        "anomalies": anomalies,
        "message": msg,
        "recordsSampled": record_count
    }
