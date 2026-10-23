from collections import Counter
from datetime import date, datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from app.models.schemas import PredictiveInsightsResponse
from app.services.storage_service import storage_service
from app.auth.dependencies import get_current_user
from app.auth.models import AuthenticatedUser

router = APIRouter(tags=["Predictive Insights"])
REQUIRED_SAMPLES = 100
REQUIRED_DAYS = 30
FORECAST_DAYS = 7

@router.get("/predictive-insights", response_model=PredictiveInsightsResponse)
async def get_predictive_insights(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Builds an explicitly exploratory linear trend from the authenticated user's
    records, or system-wide records for a verified administrator.
    """
    is_admin = current_user.is_admin and current_user.role == "administrator"
    records = storage_service.list_records(
        limit=100000,
        user_id=None if is_admin else current_user.uid,
    )
    daily_counts: Counter[date] = Counter()

    for record in records:
        timestamp = record.get("timestamp")
        if not isinstance(timestamp, str):
            continue
        try:
            observed_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if observed_at.tzinfo is not None:
                observed_at = observed_at.astimezone(timezone.utc).replace(tzinfo=None)
        except ValueError:
            continue
        daily_counts[observed_at.date()] += 1

    current_count = sum(daily_counts.values())
    observation_days = len(daily_counts)
    readiness_pct = round(
        min(
            100.0,
            current_count / REQUIRED_SAMPLES * 100.0,
            observation_days / REQUIRED_DAYS * 100.0,
        ),
        1,
    )
    sufficient_data = current_count >= REQUIRED_SAMPLES and observation_days >= REQUIRED_DAYS

    response = {
        "sufficientData": sufficient_data,
        "currentSamples": current_count,
        "requiredSamples": REQUIRED_SAMPLES,
        "currentEvents": current_count,
        "requiredEvents": REQUIRED_SAMPLES,
        "observationDays": observation_days,
        "requiredDays": REQUIRED_DAYS,
        "readinessPct": readiness_pct,
        "scope": "system" if is_admin else "personal",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "message": (
            "Exploratory linear trend from actual daily records. This forecast is not independently validated."
            if sufficient_data
            else (
                f"Insufficient historical telemetry for an exploratory trend "
                f"({current_count}/{REQUIRED_SAMPLES} timestamped events across "
                f"{observation_days}/{REQUIRED_DAYS} distinct days)."
            )
        ),
        "projections": None,
        "forecast": None,
    }
    if not sufficient_data:
        return response

    latest_day = max(daily_counts)
    first_day = latest_day - timedelta(days=REQUIRED_DAYS - 1)
    observations = [
        daily_counts.get(first_day + timedelta(days=offset), 0)
        for offset in range(REQUIRED_DAYS)
    ]
    mean_x = (REQUIRED_DAYS - 1) / 2
    mean_y = sum(observations) / REQUIRED_DAYS
    variance_x = sum((x - mean_x) ** 2 for x in range(REQUIRED_DAYS))
    slope = sum(
        (x - mean_x) * (value - mean_y)
        for x, value in enumerate(observations)
    ) / variance_x
    intercept = mean_y - slope * mean_x

    response["forecast"] = [
        {
            "label": (latest_day + timedelta(days=offset)).isoformat(),
            "value": round(max(0.0, intercept + slope * (REQUIRED_DAYS - 1 + offset)), 2),
        }
        for offset in range(1, FORECAST_DAYS + 1)
    ]
    response["projections"] = {
        "model": "Ordinary least-squares linear trend",
        "forecastHorizonDays": FORECAST_DAYS,
        "validation": "Exploratory only; not independently validated.",
    }
    return response
