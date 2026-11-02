import hashlib
import json
import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.db.models import (
    BackupRecord,
    DevelopmentTask,
    GitHubConnection,
    LocalProject,
    RepositoryConnection,
    User,
)
from app.db.session import get_db
from app.schemas.profile import (
    GitHubProfileDetails,
    NotificationPreferences,
    ProfileSummaryDashboard,
    ProfileUpdateRequest,
    RecentBackupActivity,
    RecentTaskActivity,
    UserProfileResponse,
)
from app.services.github.client import GitHubClient, GitHubError
from app.services.security import decrypt_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["profile"])

AVATAR_UPLOAD_DIR = Path("backend/uploads/avatars")
AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2 MB

ALLOWED_IMAGE_TYPES = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


def _parse_notifications(raw: str | None) -> NotificationPreferences:
    if not raw:
        return NotificationPreferences()
    try:
        data = json.loads(raw)
        return NotificationPreferences(**data)
    except Exception:
        return NotificationPreferences()


async def _fetch_github_profile(user: User, db: Session) -> GitHubProfileDetails:
    connection = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    if not connection or not connection.encrypted_access_token:
        return GitHubProfileDetails(
            connected=False,
            login=user.github_login,
            name=user.github_name,
            email=user.github_email,
            avatar_url=user.github_avatar_url,
            html_url=f"https://github.com/{user.github_login}",
        )

    try:
        token = decrypt_token(connection.encrypted_access_token)
        client = GitHubClient(token)
        gh_user = await client.current_user()
        return GitHubProfileDetails(
            connected=True,
            github_id=gh_user.get("id"),
            login=gh_user.get("login") or user.github_login,
            name=gh_user.get("name") or user.github_name,
            email=gh_user.get("email") or user.github_email,
            avatar_url=gh_user.get("avatar_url") or user.github_avatar_url,
            html_url=gh_user.get("html_url") or f"https://github.com/{user.github_login}",
            public_repos=gh_user.get("public_repos", 0),
            followers=gh_user.get("followers", 0),
            following=gh_user.get("following", 0),
            github_created_at=str(gh_user.get("created_at")) if gh_user.get("created_at") else None,
        )
    except Exception as exc:
        logger.warning("Could not fetch remote GitHub profile for user_id=%s: %s", user.id, exc)
        return GitHubProfileDetails(
            connected=True,
            login=user.github_login,
            name=user.github_name,
            email=user.github_email,
            avatar_url=user.github_avatar_url,
            html_url=f"https://github.com/{user.github_login}",
        )


async def _build_profile_response(user: User, db: Session) -> UserProfileResponse:
    repo_count = db.scalar(
        select(func.count(RepositoryConnection.id)).where(RepositoryConnection.user_id == user.id)
    ) or 0
    project_count = db.scalar(
        select(func.count(LocalProject.id)).where(LocalProject.user_id == user.id)
    ) or 0
    active_backups = db.scalar(
        select(func.count(LocalProject.id)).where(
            LocalProject.user_id == user.id, LocalProject.is_active == True
        )
    ) or 0

    gh_profile = await _fetch_github_profile(user, db)
    display_name = user.custom_display_name or user.github_name or user.github_login
    effective_avatar = user.avatar_url or user.github_avatar_url or gh_profile.avatar_url

    return UserProfileResponse(
        id=user.id,
        github_id=user.github_id,
        github_login=user.github_login,
        github_name=user.github_name,
        github_email=user.github_email,
        custom_display_name=user.custom_display_name,
        display_name=display_name,
        avatar_url=effective_avatar,
        github_avatar_url=user.github_avatar_url or gh_profile.avatar_url,
        github_profile_url=f"https://github.com/{user.github_login}",
        timezone=user.timezone or "UTC",
        notification_preferences=_parse_notifications(user.notification_preferences),
        created_at=user.created_at,
        updated_at=user.updated_at,
        github_connected=gh_profile.connected,
        connected_repositories_count=repo_count,
        local_projects_count=project_count,
        automation_active=active_backups > 0,
        github_profile=gh_profile,
    )


@router.get("", response_model=UserProfileResponse)
async def get_user_profile(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Retrieve complete profile of the authenticated user and connected GitHub account."""
    return await _build_profile_response(user, db)


@router.patch("", response_model=UserProfileResponse)
async def update_user_profile(
    payload: ProfileUpdateRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Update profile settings (custom display name, preferred timezone, and notification preferences)."""
    if payload.custom_display_name is not None:
        clean_name = payload.custom_display_name.strip()
        user.custom_display_name = clean_name if clean_name else None

    if payload.timezone is not None:
        clean_tz = payload.timezone.strip()
        if clean_tz:
            user.timezone = clean_tz

    if payload.notification_preferences is not None:
        user.notification_preferences = json.dumps(payload.notification_preferences.model_dump())

    db.add(user)
    db.commit()
    db.refresh(user)
    return await _build_profile_response(user, db)


@router.post("/avatar", response_model=UserProfileResponse)
async def upload_profile_avatar(
    file: UploadFile = File(...),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Upload and validate a custom profile image file."""
    if not file.content_type or file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type '{file.content_type}'. Allowed types: PNG, JPEG, WebP, GIF.",
        )

    content = await file.read()
    if len(content) > MAX_AVATAR_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum allowed size of {MAX_AVATAR_BYTES // (1024 * 1024)} MB.",
        )

    # Magic bytes validation
    ext = ALLOWED_IMAGE_TYPES[file.content_type]
    is_valid = False
    if file.content_type == "image/png" and content.startswith(b"\x89PNG\r\n\x1a\n"):
        is_valid = True
    elif file.content_type == "image/jpeg" and content.startswith(b"\xff\xd8\xff"):
        is_valid = True
    elif file.content_type == "image/gif" and content.startswith((b"GIF87a", b"GIF89a")):
        is_valid = True
    elif file.content_type == "image/webp" and content.startswith(b"RIFF") and b"WEBP" in content[:16]:
        is_valid = True

    if not is_valid:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file header does not match a valid image structure.",
        )

    # Generate safe unique filename
    content_hash = hashlib.sha256(content).hexdigest()[:12]
    filename = f"avatar_u{user.id}_{content_hash}{ext}"
    dest_path = AVATAR_UPLOAD_DIR / filename
    dest_path.write_bytes(content)

    avatar_url = f"/api/v1/profile/avatar-file/{filename}"
    user.avatar_url = avatar_url
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("Custom avatar updated for user_id=%s file=%s", user.id, filename)
    return await _build_profile_response(user, db)


@router.delete("/avatar", response_model=UserProfileResponse)
async def remove_profile_avatar(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Remove custom profile avatar and revert to GitHub profile avatar."""
    user.avatar_url = None
    db.add(user)
    db.commit()
    db.refresh(user)
    return await _build_profile_response(user, db)


@router.get("/avatar-file/{filename}")
async def get_avatar_file(filename: str) -> FileResponse:
    """Serve validated user avatar images securely."""
    # Sanitize filename
    clean_name = Path(filename).name
    file_path = AVATAR_UPLOAD_DIR / clean_name
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Avatar image not found.")
    return FileResponse(file_path)


@router.get("/dashboard", response_model=ProfileSummaryDashboard)
async def get_profile_dashboard(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ProfileSummaryDashboard:
    """Summary dashboard card showing account, connection, backups, and recent activity."""
    repo_count = db.scalar(
        select(func.count(RepositoryConnection.id)).where(RepositoryConnection.user_id == user.id)
    ) or 0
    project_count = db.scalar(
        select(func.count(LocalProject.id)).where(LocalProject.user_id == user.id)
    ) or 0
    active_backups = db.scalar(
        select(func.count(LocalProject.id)).where(
            LocalProject.user_id == user.id, LocalProject.is_active == True
        )
    ) or 0

    latest_project = db.scalars(
        select(LocalProject)
        .where(LocalProject.user_id == user.id, LocalProject.last_backup_at != None)
        .order_by(LocalProject.last_backup_at.desc())
        .limit(1)
    ).first()

    gh_connection = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))

    # Recent backups (last 5)
    records = db.scalars(
        select(BackupRecord)
        .where(BackupRecord.user_id == user.id)
        .order_by(BackupRecord.created_at.desc())
        .limit(5)
    ).all()

    recent_backups: list[RecentBackupActivity] = []
    for r in records:
        proj = db.get(LocalProject, r.local_project_id)
        recent_backups.append(
            RecentBackupActivity(
                id=r.id,
                project_name=proj.name if proj else f"Project #{r.local_project_id}",
                status=r.status,
                commit_sha=r.commit_sha,
                commit_url=r.commit_url,
                is_dry_run=r.is_dry_run,
                created_at=r.created_at,
            )
        )

    # Recent tasks (last 5)
    tasks = db.scalars(
        select(DevelopmentTask)
        .where(DevelopmentTask.user_id == user.id)
        .order_by(DevelopmentTask.created_at.desc())
        .limit(5)
    ).all()

    recent_tasks: list[RecentTaskActivity] = []
    for t in tasks:
        repo = db.get(RepositoryConnection, t.repository_connection_id)
        recent_tasks.append(
            RecentTaskActivity(
                id=t.id,
                repository_name=f"{repo.owner}/{repo.name}" if repo else f"Repo #{t.repository_connection_id}",
                task_type=t.task_type,
                status=t.status,
                created_at=t.created_at,
            )
        )

    display_name = user.custom_display_name or user.github_name or user.github_login
    effective_avatar = user.avatar_url or user.github_avatar_url

    return ProfileSummaryDashboard(
        user_id=user.id,
        display_name=display_name,
        github_login=user.github_login,
        github_connected=gh_connection is not None,
        avatar_url=effective_avatar,
        timezone=user.timezone or "UTC",
        connected_repositories_count=repo_count,
        local_projects_count=project_count,
        automation_active=active_backups > 0,
        active_backups_count=active_backups,
        last_backup_at=latest_project.last_backup_at if latest_project else None,
        last_backup_status=latest_project.last_backup_status if latest_project else None,
        recent_backups=recent_backups,
        recent_tasks=recent_tasks,
    )


@router.post("/github/disconnect")
async def disconnect_github(
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Disconnect connected GitHub account upon user authorization."""
    connection = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    if not connection:
        return {"disconnected": True, "message": "No active GitHub connection to disconnect."}

    db.delete(connection)
    db.commit()
    logger.info("GitHub account disconnected by user_id=%s login=%s", user.id, user.github_login)
    return {
        "disconnected": True,
        "message": "GitHub account connection was successfully removed. You can reconnect at any time.",
    }

