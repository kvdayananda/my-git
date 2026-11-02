import calendar
from datetime import date, datetime, time, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.models import AutomationRun, RepositoryConnection
from app.schemas.analytics import (
    DailyAnalyticsResponse,
    DayData,
    LifetimeAnalyticsResponse,
    MonthlyAnalyticsResponse,
    RepoStats,
    RunSummary,
    WeeklyAnalyticsResponse,
)


def _to_run_summary(r: AutomationRun, repo_map: dict[int, RepositoryConnection]) -> RunSummary:
    repo = repo_map.get(r.repository_connection_id)
    repo_name = f"{repo.owner}/{repo.name}" if repo else f"repo-{r.repository_connection_id}"
    return RunSummary(
        id=r.id,
        repository_id=r.repository_connection_id,
        repository_name=repo_name,
        status=r.status,
        commit_sha=r.commit_sha,
        commit_url=r.commit_url,
        pull_request_number=r.pull_request_number,
        pull_request_url=r.pull_request_url,
        commit_message=r.commit_message,
        lines_added=r.lines_added or 0,
        lines_deleted=r.lines_deleted or 0,
        files_created_count=r.files_created_count or 0,
        files_modified_count=r.files_modified_count or 0,
        files_deleted_count=r.files_deleted_count or 0,
        speed_target_met=r.speed_target_met,
        publishing_duration_ms=r.publishing_duration_ms,
        created_at=r.created_at,
        completed_at=r.completed_at,
    )


def get_daily_analytics(
    db: Session,
    user_id: int,
    target_date_str: str | None = None,
    tz_name: str = "Asia/Kolkata",
) -> DailyAnalyticsResponse:
    """Retrieve publication and code change metrics for a specific calendar day."""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Asia/Kolkata")

    if target_date_str:
        try:
            target_date = datetime.strptime(target_date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            target_date = datetime.now(tz).date()
    else:
        target_date = datetime.now(tz).date()

    start_local = datetime.combine(target_date, time.min, tzinfo=tz)
    end_local = datetime.combine(target_date, time.max, tzinfo=tz)
    start_utc = start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    end_utc = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    runs = db.scalars(
        select(AutomationRun)
        .where(
            AutomationRun.user_id == user_id,
            AutomationRun.created_at >= start_utc,
            AutomationRun.created_at <= end_utc,
        )
        .order_by(AutomationRun.created_at.desc())
    ).all()

    # Pre-fetch repository names
    repo_ids = {r.repository_connection_id for r in runs}
    repos = db.scalars(select(RepositoryConnection).where(RepositoryConnection.id.in_(repo_ids))).all() if repo_ids else []
    repo_map = {repo.id: repo for repo in repos}

    durations = [r.publishing_duration_ms for r in runs if r.publishing_duration_ms is not None]
    avg_duration = int(sum(durations) / len(durations)) if durations else None

    return DailyAnalyticsResponse(
        date=target_date.strftime("%Y-%m-%d"),
        runs_count=len(runs),
        successful_runs=sum(1 for r in runs if r.status == "completed"),
        failed_runs=sum(1 for r in runs if r.status == "failed"),
        commits_count=sum(1 for r in runs if r.commit_sha),
        prs_count=sum(1 for r in runs if r.pull_request_number),
        lines_added=sum(r.lines_added or 0 for r in runs),
        lines_deleted=sum(r.lines_deleted or 0 for r in runs),
        files_created_count=sum(r.files_created_count or 0 for r in runs),
        files_modified_count=sum(r.files_modified_count or 0 for r in runs),
        files_deleted_count=sum(r.files_deleted_count or 0 for r in runs),
        speed_target_met_count=sum(1 for r in runs if r.speed_target_met is True),
        avg_publishing_duration_ms=avg_duration,
        runs=[_to_run_summary(r, repo_map) for r in runs],
    )


def get_weekly_analytics(
    db: Session,
    user_id: int,
    reference_date_str: str | None = None,
    tz_name: str = "Asia/Kolkata",
) -> WeeklyAnalyticsResponse:
    """Retrieve rolling 7-day publication and commit statistics."""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Asia/Kolkata")

    if reference_date_str:
        try:
            ref_date = datetime.strptime(reference_date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            ref_date = datetime.now(tz).date()
    else:
        ref_date = datetime.now(tz).date()

    start_date = ref_date - timedelta(days=6)
    start_local = datetime.combine(start_date, time.min, tzinfo=tz)
    end_local = datetime.combine(ref_date, time.max, tzinfo=tz)
    start_utc = start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    end_utc = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    runs = db.scalars(
        select(AutomationRun).where(
            AutomationRun.user_id == user_id,
            AutomationRun.created_at >= start_utc,
            AutomationRun.created_at <= end_utc,
        )
    ).all()

    # Bucket runs by local date
    daily_buckets: dict[str, list[AutomationRun]] = {
        (start_date + timedelta(days=i)).strftime("%Y-%m-%d"): [] for i in range(7)
    }

    for r in runs:
        local_dt = r.created_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
        d_key = local_dt.strftime("%Y-%m-%d")
        if d_key in daily_buckets:
            daily_buckets[d_key].append(r)

    daily_breakdown: list[DayData] = []
    for d_str, day_runs in daily_buckets.items():
        dt_obj = datetime.strptime(d_str, "%Y-%m-%d")
        daily_breakdown.append(
            DayData(
                date=d_str,
                day_name=dt_obj.strftime("%a"),
                runs=len(day_runs),
                commits=sum(1 for r in day_runs if r.commit_sha),
                prs=sum(1 for r in day_runs if r.pull_request_number),
                lines_added=sum(r.lines_added or 0 for r in day_runs),
                lines_deleted=sum(r.lines_deleted or 0 for r in day_runs),
            )
        )

    return WeeklyAnalyticsResponse(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=ref_date.strftime("%Y-%m-%d"),
        total_runs=len(runs),
        total_commits=sum(1 for r in runs if r.commit_sha),
        total_prs=sum(1 for r in runs if r.pull_request_number),
        total_lines_added=sum(r.lines_added or 0 for r in runs),
        total_lines_deleted=sum(r.lines_deleted or 0 for r in runs),
        daily_breakdown=daily_breakdown,
    )


def get_monthly_analytics(
    db: Session,
    user_id: int,
    year: int | None = None,
    month: int | None = None,
    tz_name: str = "Asia/Kolkata",
) -> MonthlyAnalyticsResponse:
    """Retrieve monthly publishing aggregates and per-repository breakdown."""
    try:
        tz = ZoneInfo(tz_name)
    except Exception:
        tz = ZoneInfo("Asia/Kolkata")

    now_local = datetime.now(tz)
    y = year or now_local.year
    m = month or now_local.month

    days_in_month = calendar.monthrange(y, m)[1]
    start_local = datetime(y, m, 1, 0, 0, 0, tzinfo=tz)
    end_local = datetime(y, m, days_in_month, 23, 59, 59, tzinfo=tz)
    start_utc = start_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
    end_utc = end_local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

    runs = db.scalars(
        select(AutomationRun).where(
            AutomationRun.user_id == user_id,
            AutomationRun.created_at >= start_utc,
            AutomationRun.created_at <= end_utc,
        )
    ).all()

    # Pre-fetch repository names
    repo_ids = {r.repository_connection_id for r in runs}
    repos = db.scalars(select(RepositoryConnection).where(RepositoryConnection.id.in_(repo_ids))).all() if repo_ids else []
    repo_map = {repo.id: repo for repo in repos}

    # Group by repository
    repo_groups: dict[int, list[AutomationRun]] = {}
    for r in runs:
        repo_groups.setdefault(r.repository_connection_id, []).append(r)

    repo_breakdown: list[RepoStats] = []
    for r_id, r_runs in repo_groups.items():
        rp = repo_map.get(r_id)
        name = f"{rp.owner}/{rp.name}" if rp else f"repo-{r_id}"
        repo_breakdown.append(
            RepoStats(
                repository_id=r_id,
                repository_name=name,
                runs=len(r_runs),
                commits=sum(1 for r in r_runs if r.commit_sha),
                prs=sum(1 for r in r_runs if r.pull_request_number),
                lines_added=sum(r.lines_added or 0 for r in r_runs),
                lines_deleted=sum(r.lines_deleted or 0 for r in r_runs),
            )
        )

    # Daily breakdown for the month
    daily_buckets: dict[str, list[AutomationRun]] = {
        f"{y:04d}-{m:02d}-{d:02d}": [] for d in range(1, days_in_month + 1)
    }
    for r in runs:
        local_dt = r.created_at.replace(tzinfo=ZoneInfo("UTC")).astimezone(tz)
        d_key = local_dt.strftime("%Y-%m-%d")
        if d_key in daily_buckets:
            daily_buckets[d_key].append(r)

    daily_breakdown: list[DayData] = []
    for d_str, day_runs in daily_buckets.items():
        dt_obj = datetime.strptime(d_str, "%Y-%m-%d")
        daily_breakdown.append(
            DayData(
                date=d_str,
                day_name=dt_obj.strftime("%a"),
                runs=len(day_runs),
                commits=sum(1 for r in day_runs if r.commit_sha),
                prs=sum(1 for r in day_runs if r.pull_request_number),
                lines_added=sum(r.lines_added or 0 for r in day_runs),
                lines_deleted=sum(r.lines_deleted or 0 for r in day_runs),
            )
        )

    return MonthlyAnalyticsResponse(
        year=y,
        month=m,
        total_runs=len(runs),
        total_commits=sum(1 for r in runs if r.commit_sha),
        total_prs=sum(1 for r in runs if r.pull_request_number),
        total_lines_added=sum(r.lines_added or 0 for r in runs),
        total_lines_deleted=sum(r.lines_deleted or 0 for r in runs),
        active_repositories_count=len(repo_groups),
        repository_breakdown=repo_breakdown,
        daily_breakdown=daily_breakdown,
    )


def get_lifetime_analytics(db: Session, user_id: int) -> LifetimeAnalyticsResponse:
    """Retrieve all-time cumulative statistics across all automated repositories."""
    runs = db.scalars(
        select(AutomationRun)
        .where(AutomationRun.user_id == user_id)
        .order_by(AutomationRun.created_at.asc())
    ).all()

    repo_ids = {r.repository_connection_id for r in runs}
    repos = db.scalars(select(RepositoryConnection).where(RepositoryConnection.id.in_(repo_ids))).all() if repo_ids else []
    repo_map = {repo.id: repo for repo in repos}

    total_runs = len(runs)
    successful_runs = sum(1 for r in runs if r.status == "completed")
    failed_runs = sum(1 for r in runs if r.status == "failed")
    commits_count = sum(1 for r in runs if r.commit_sha)
    prs_count = sum(1 for r in runs if r.pull_request_number)
    lines_added = sum(r.lines_added or 0 for r in runs)
    lines_deleted = sum(r.lines_deleted or 0 for r in runs)
    total_changed = lines_added + lines_deleted

    success_rate = round((successful_runs / total_runs * 100), 1) if total_runs > 0 else 100.0

    speed_evaluated = [r for r in runs if r.speed_target_met is not None]
    speed_met = sum(1 for r in speed_evaluated if r.speed_target_met is True)
    speed_compliance = round((speed_met / len(speed_evaluated) * 100), 1) if speed_evaluated else 100.0

    durations = [r.publishing_duration_ms for r in runs if r.publishing_duration_ms is not None]
    avg_duration = int(sum(durations) / len(durations)) if durations else None

    # Group by repository
    repo_groups: dict[int, list[AutomationRun]] = {}
    for r in runs:
        repo_groups.setdefault(r.repository_connection_id, []).append(r)

    repo_breakdown: list[RepoStats] = []
    for r_id, r_runs in repo_groups.items():
        rp = repo_map.get(r_id)
        name = f"{rp.owner}/{rp.name}" if rp else f"repo-{r_id}"
        repo_breakdown.append(
            RepoStats(
                repository_id=r_id,
                repository_name=name,
                runs=len(r_runs),
                commits=sum(1 for r in r_runs if r.commit_sha),
                prs=sum(1 for r in r_runs if r.pull_request_number),
                lines_added=sum(r.lines_added or 0 for r in r_runs),
                lines_deleted=sum(r.lines_deleted or 0 for r in r_runs),
            )
        )

    first_date = runs[0].created_at if runs else None
    latest_date = runs[-1].created_at if runs else None

    return LifetimeAnalyticsResponse(
        total_automated_repositories=len(repo_groups),
        total_runs=total_runs,
        total_successful_runs=successful_runs,
        total_failed_runs=failed_runs,
        total_commits=commits_count,
        total_prs=prs_count,
        total_lines_added=lines_added,
        total_lines_deleted=lines_deleted,
        total_lines_changed=total_changed,
        success_rate_percent=success_rate,
        speed_target_met_count=speed_met,
        speed_compliance_percent=speed_compliance,
        avg_publishing_duration_ms=avg_duration,
        first_run_date=first_date,
        latest_run_date=latest_date,
        repository_breakdown=repo_breakdown,
    )

