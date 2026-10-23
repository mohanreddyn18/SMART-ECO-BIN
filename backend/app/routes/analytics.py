from typing import Optional
from fastapi import APIRouter, Query
from app.services.analytics_service import analytics_service
from app.models.schemas import AnalyticsResponse

router = APIRouter(tags=["Analytics"])

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_system_analytics(
    period: Optional[str] = Query("all", description="Time period filter: 'hourly', 'daily', 'weekly', 'monthly', 'yearly', 'custom', or 'all'"),
    start_date: Optional[str] = Query(None, description="ISO Start date for custom filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="ISO End date for custom filter (YYYY-MM-DD)")
):
    return analytics_service.get_macro_analytics(period=period, start_date=start_date, end_date=end_date)
