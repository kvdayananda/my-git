import json
import logging
from datetime import datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.base import utc_now
from app.db.models import (
    AutomationRun,
    AutomationSetting,
    GitHubConnection,
    RepositoryConnection,
    User,
)
from app.services.automation.engine import (
    approve_and_publish_automation_run,
    execute_daily_ai_automation,
)

logger = logging.getLogger(__name__)


def compute_next_run(schedule_time: str, tz_name: str, reference_utc: datetime | None = None) -> datetime:
    """Calculate the next execution time in UTC for a given HH:MM schedule and timezone."""
    if reference_utc is None:
        reference_utc = utc_now()

    try:
        tz = ZoneInfo(tz_name.strip() if tz_name else "Asia/Kolkata")
    except Exception:
        tz = ZoneInfo("Asia/Kolkata")

    # Parse HH:MM
    try:
        parts = schedule_time.strip().split(":")
        target_hour = int(parts[0])
        target_minute = int(parts[1]) if len(parts) > 1 else 0
    except Exception:
        target_hour, target_minute = 20, 0  # 8:00 PM default

    target_time = time(hour=target_hour, minute=target_minute)

    # Reference time in target timezone
    if reference_utc.tzinfo is None:
        ref_utc_aware = reference_utc.replace(tzinfo=ZoneInfo("UTC"))
    else:
        ref_utc_aware = reference_utc.astimezone(ZoneInfo("UTC"))
    local_now = ref_utc_aware.astimezone(tz)
    candidate_today = datetime.combine(local_now.date(), target_time, tzinfo=tz)

    if local_now < candidate_today:
        next_local = candidate_today
    else:
        next_local = candidate_today + timedelta(days=1)

    # Return as UTC datetime
    return next_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)


def is_schedule_due(
    setting: AutomationSetting, reference_utc: datetime | None = None
) -> tuple[bool, str]:
    """Check if an automation schedule is due right now or missed today.
    
    Returns (is_due, reason).
    """
    if not setting.is_enabled:
        return False, "Setting is disabled"

    if reference_utc is None:
        reference_utc = utc_now()

    try:
        tz = ZoneInfo(setting.timezone if setting.timezone else "Asia/Kolkata")
    except Exception:
        tz = ZoneInfo("Asia/Kolkata")

    if reference_utc.tzinfo is None:
        ref_utc_aware = reference_utc.replace(tzinfo=ZoneInfo("UTC"))
    else:
        ref_utc_aware = reference_utc.astimezone(ZoneInfo("UTC"))
    local_now = ref_utc_aware.astimezone(tz)

    # Parse HH:MM
    try:
        parts = setting.schedule_time.strip().split(":")
        target_hour = int(parts[0])
        target_minute = int(parts[1]) if len(parts) > 1 else 0
    except Exception:
        target_hour, target_minute = 20, 0

    target_time = time(hour=target_hour, minute=target_minute)
    scheduled_today_local = datetime.combine(local_now.date(), target_time, tzinfo=tz)
    scheduled_today_utc = scheduled_today_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    # Check if already executed today in this timezone
    if setting.last_run_at:
        last_local = setting.last_run_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
        if last_local.date() == local_now.date():
            return False, f"Already executed today on {last_local.date()}"

    # If current time is past or within 10 minutes of scheduled time today
    if reference_utc >= scheduled_today_utc:
        # Check missed schedule window (e.g., within last 24 hours)
        time_diff = reference_utc - scheduled_today_utc
        if time_diff < timedelta(hours=24):
            return True, "Scheduled time reached or missed recovery"

    return False, "Not yet scheduled time today"


async def evaluate_and_dispatch_due_schedules(db: Session) -> list[int]:
    """Inspect all active automation settings and trigger due daily executions."""
    now_utc = utc_now()
    active_settings = db.scalars(
        select(AutomationSetting).where(AutomationSetting.is_enabled == True)  # noqa: E712
    ).all()

    dispatched_run_ids: list[int] = []

    for setting in active_settings:
        due, reason = is_schedule_due(setting, now_utc)
        if not due:
            # Update next_run_at if empty or in the past
            expected_next = compute_next_run(setting.schedule_time, setting.timezone, now_utc)
            if not setting.next_run_at or setting.next_run_at < now_utc:
                setting.next_run_at = expected_next
                db.commit()
            continue

        repo = db.get(RepositoryConnection, setting.repository_connection_id)
        user = db.get(User, setting.user_id)
        if not repo or not user:
            continue

        # Pre-flight check: Write permission
        if not repo.can_push:
            logger.warning(
                "Skipping scheduled automation for %s/%s: write permission (can_push) is false.",
                repo.owner, repo.name,
            )
            setting.last_run_at = now_utc
            setting.last_run_status = "permission_denied"
            setting.next_run_at = compute_next_run(setting.schedule_time, setting.timezone, now_utc)
            db.commit()
            continue

        logger.info(
            "Dispatching scheduled daily automation for %s/%s (reason: %s)",
            repo.owner, repo.name, reason,
        )

        try:
            # Execute Phase 3 engine
            run = await execute_daily_ai_automation(repo=repo, user=user, db=db, setting=setting)
            dispatched_run_ids.append(run.id)

            # Check for Phase 5 Automatic Publishing Opt-in
            if setting.auto_publish and run.status == "pending_approval" and run.tests_passed:
                logger.info(
                    "Auto-publish opt-in enabled for setting #%s; initiating immediate PR publish for run #%s",
                    setting.id, run.id,
                )
                published_run = await approve_and_publish_automation_run(run_id=run.id, user=user, db=db)
                logger.info(
                    "Auto-publish completed for run #%s. Target met: %s, duration: %sms",
                    published_run.id, published_run.speed_target_met, published_run.publishing_duration_ms,
                )

            # Update next run time
            setting.next_run_at = compute_next_run(setting.schedule_time, setting.timezone, now_utc)
            db.commit()
        except Exception as exc:
            logger.exception("Error executing scheduled automation for setting #%s: %s", setting.id, exc)

    return dispatched_run_ids

