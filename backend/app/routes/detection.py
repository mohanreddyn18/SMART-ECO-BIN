"""
SMART ECO BIN — Multi-Object Mixed Waste Detection API Route
============================================================
Provides object-level waste detection, localization bounding boxes,
and per-item wet/dry/hazardous disposal routing for mixed-waste images.
"""

from typing import Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Header, Depends, Request, status, Query

from app.models.schemas import WasteDetectionResponse
from app.services.detector_service import detector_service
from app.services.annotation_service import annotation_service
from app.auth.dependencies import get_optional_current_user
from app.auth.models import AuthenticatedUser
from app.routes.predict import get_client_ip, check_rate_limit

router = APIRouter(tags=["Multi-Object Detection"])

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp", "image/jpg"]
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/detect-waste", response_model=WasteDetectionResponse)
async def detect_mixed_waste(
    request: Request,
    file: UploadFile = File(...),
    include_annotation: bool = True,
    conf_threshold: Optional[float] = Query(None, ge=0.05, le=1.0, description="Minimum confidence threshold for object detection"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_current_user)
):
    """
    Accepts an uploaded image containing multiple waste items, detects individual
    objects, outputs bounding boxes and confidence scores, and determines
    authoritative wet/dry/hazardous disposal instructions for every item separately.
    """
    # 1. Enforce per-client rate limit (30 requests/min)
    client_ip = get_client_ip(request)
    rate_limit_key = current_user.uid if current_user else f"ip:{client_ip}"
    check_rate_limit(rate_limit_key)

    # 2. Validate MIME content type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image type. Accepted formats: JPEG, PNG, WEBP."
        )

    # 3. Read image bytes and validate size
    contents = await file.read()
    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size exceeds 10MB limit."
        )

    # 4. Execute multi-object detection
    try:
        response = detector_service.detect_image_bytes(contents, conf_threshold=conf_threshold)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format: {str(e)}"
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Detector service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Detection inference failed: {str(e)}"
        )

    # 5. Optionally generate visual annotation preview
    if include_annotation and response.detections:
        response.annotated_image_base64 = annotation_service.generate_annotated_base64(
            contents,
            response.detections
        )

    # 6. Persist event record for cloud storage, audit history, and analytics tracking
    if response.success and response.model_status == "loaded":
        from datetime import datetime
        import uuid
        from app.services.analytics_service import analytics_service

        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_suffix = uuid.uuid4().hex[:6]
        record_id = f"DET-{ts}-{unique_suffix}"
        user_id = current_user.uid if current_user else "public-citizen"

        dominant_type = "Recyclable / Dry Waste"
        if response.summary.wet_items > response.summary.dry_items:
            dominant_type = "Organic / Wet Waste"
        elif response.summary.hazardous_items > 0:
            dominant_type = "Hazardous / Other"
        elif response.summary.total_detections == 0:
            dominant_type = "Uncertain / Manual Review"

        avg_conf = (
            round(sum(d.confidence for d in response.detections) / len(response.detections) * 100.0, 1)
            if response.detections
            else 0.0
        )

        detected_labels = list(dict.fromkeys(d.label for d in response.detections))
        item_summary = ", ".join(detected_labels[:3]) if detected_labels else "Mixed Waste Intake"

        record_entry = {
            "id": record_id,
            "type": "multi_object_detection",
            "itemName": f"Mixed Waste ({file.filename}) — {item_summary}",
            "predictedClass": detected_labels[0] if detected_labels else "mixed_waste",
            "wasteType": dominant_type,
            "confidence": avg_conf,
            "recommendation": f"Sort {response.summary.total_detections} detected items into respective chutes: {response.summary.wet_items} wet, {response.summary.dry_items} dry, {response.summary.hazardous_items} hazardous, {response.summary.manual_review_items} review.",
            "disposalBin": "Multi-Chute Segregation Depot",
            "destinationCompartment": "Multi-Chute Segregation Depot",
            "compartmentId": "bin_multi",
            "routingStatus": "MANUAL_REVIEW" if response.summary.manual_review_items > 0 or response.summary.total_detections == 0 else "AUTOMATED_ROUTED",
            "routingReason": f"Multi-object detection identified {response.summary.total_detections} individual items.",
            "requiresManualReview": response.summary.manual_review_items > 0 or response.summary.total_detections == 0,
            "simulationStatus": "SIMULATED",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "userId": user_id,
            "totalDetections": response.summary.total_detections,
            "summary": response.summary.model_dump(),
            "detections": [d.model_dump() for d in response.detections]
        }

        analytics_service.add_record(record_entry, idempotency_key=x_idempotency_key)

    return response
