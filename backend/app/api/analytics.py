import logging
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.analytics import (
    DailyAnalyticsResponse,
    LifetimeAnalyticsResponse,
    MonthlyAnalyticsResponse,
    WeeklyAnalyticsResponse,
)
from app.services.analytics.service import (
    get_daily_analytics,
    get_lifetime_analytics,
    get_monthly_analytics,
    get_weekly_analytics,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/daily", response_model=DailyAnalyticsResponse)
async def get_daily_stats(
    date: str | None = Query(None, description="Target date in YYYY-MM-DD format"),
    timezone: str = Query("Asia/Kolkata", description="User timezone"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> DailyAnalyticsResponse:
    """Get daily publication and diff change metrics."""
    return get_daily_analytics(db=db, user_id=user.id, target_date_str=date, tz_name=timezone)


@router.get("/weekly", response_model=WeeklyAnalyticsResponse)
async def get_weekly_stats(
    reference_date: str | None = Query(None, description="End date of 7-day window (YYYY-MM-DD)"),
    timezone: str = Query("Asia/Kolkata", description="User timezone"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> WeeklyAnalyticsResponse:
    """Get rolling 7-day publication and commit statistics."""
    return get_weekly_analytics(db=db, user_id=user.id, reference_date_str=reference_date, tz_name=timezone)


@router.get("/monthly", response_model=MonthlyAnalyticsResponse)
async def get_monthly_stats(
    year: int | None = Query(None, description="Year (e.g. 2026)"),
    month: int | None = Query(None, ge=1, le=12, description="Month (1-12)"),
    timezone: str = Query("Asia/Kolkata", description="User timezone"),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> MonthlyAnalyticsResponse:
    """Get monthly publishing aggregates and per-repository breakdown."""
    return get_monthly_analytics(db=db, user_id=user.id, year=year, month=month, tz_name=timezone)


@router.get("/lifetime", response_model=LifetimeAnalyticsResponse)
async def get_lifetime_stats(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> LifetimeAnalyticsResponse:
    """Get all-time cumulative statistics across all automated repositories."""
    return get_lifetime_analytics(db=db, user_id=user.id)
