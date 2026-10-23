from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import List, Dict, Any, Optional
from app.services.analytics_service import analytics_service
from app.services.storage_service import storage_service
from app.models.schemas import HistoryRecord
from app.auth.dependencies import get_optional_current_user, require_admin
from app.auth.models import AuthenticatedUser, UserRole

router = APIRouter(tags=["History"])


@router.get("/history", response_model=List[HistoryRecord])
async def get_classification_history(
    limit: int = Query(50, ge=1, le=500),
    skip: int = Query(0, ge=0),
    category: Optional[str] = Query(None, description="Filter by operational waste category"),
    search: Optional[str] = Query(None, description="Search term across class, recommendation, or item name"),
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_current_user)
):
    """
    Returns auditable history records from the unified storage ledger.
    Enforces citizen data protection:
    - Administrators receive comprehensive municipal intake records.
    - Authenticated citizens receive only their personal historical records (userId == current_user.uid).
    - Unauthenticated citizens receive only public intake events.
    """
    # 1. Administrator: full municipal audit visibility across all records
    if current_user and current_user.is_admin:
        return storage_service.list_records(
            limit=limit, skip=skip, category=category, search=search
        )

    # 2. Authenticated Citizen: personal records only (userId == current_user.uid)
    if current_user:
        return storage_service.list_records(
            limit=limit, skip=skip, category=category, search=search, user_id=current_user.uid
        )

    # 3. Unauthenticated/Public: public citizen records only
    return storage_service.list_records(
        limit=limit, skip=skip, category=category, search=search, public_only=True
    )


@router.get("/history/{record_id}", response_model=HistoryRecord)
async def get_classification_record_by_id(
    record_id: str,
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_current_user)
):
    """
    Retrieves a single historical event by its stable record identifier.
    Enforces record ownership checks to prevent unauthorized data exposure.
    """
    record = storage_service.get_record(record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Classification event '{record_id}' not found.")

    # Administrator can view any record
    if current_user and current_user.is_admin:
        return record

    # Citizen can view their own record or general public intake
    record_owner = record.get("userId")
    if current_user:
        if record_owner == current_user.uid or record_owner in (None, "", "public-citizen"):
            return record
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to inspect another citizen's classification record."
        )

    # Anonymous user can only view public intake records
    if record_owner in (None, "", "public-citizen"):
        return record

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required to inspect private classification events."
    )


@router.delete("/history/{record_id}")
async def delete_classification_record(
    record_id: str,
    admin_user: AuthenticatedUser = Depends(require_admin)
):
    """
    Permanently deletes a classification record.
    Access Restricted: Requires verified administrator role.
    """
    deleted = storage_service.delete_record(record_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Record '{record_id}' not found for deletion.")
    return {"deleted": True, "record_id": record_id, "message": f"Record '{record_id}' permanently deleted."}
