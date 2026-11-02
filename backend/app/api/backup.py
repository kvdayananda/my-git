import json
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import current_user
from app.db.models import BackupRecord, LocalProject, RepositoryConnection, User
from app.db.session import get_db
from app.schemas.backup import (
    BackupRecordResponse,
    BackupRunRequest,
    BackupScanPreview,
    LocalProjectCreate,
    LocalProjectResponse,
    LocalProjectUpdate,
    ScannedFileDetail,
)
from app.services.backup.engine import execute_backup
from app.services.backup.scanner import scan_local_project

router = APIRouter(prefix="/backups", tags=["backups"])
logger = logging.getLogger(__name__)


def _project_response(project: LocalProject, repo: RepositoryConnection | None = None) -> LocalProjectResponse:
    return LocalProjectResponse(
        id=project.id,
        user_id=project.user_id,
        repository_connection_id=project.repository_connection_id,
        repository_name=repo.name if repo else None,
        repository_owner=repo.owner if repo else None,
        name=project.name,
        local_path=project.local_path,
        target_branch=project.target_branch,
        backup_schedule=project.backup_schedule,
        is_active=project.is_active,
        last_backup_at=project.last_backup_at,
        last_backup_status=project.last_backup_status,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def _record_response(record: BackupRecord, project: LocalProject | None = None) -> BackupRecordResponse:
    try:
        backed_up = json.loads(record.files_backed_up) if record.files_backed_up else []
    except Exception:
        backed_up = []
    try:
        excluded = json.loads(record.files_excluded) if record.files_excluded else []
    except Exception:
        excluded = []

    return BackupRecordResponse(
        id=record.id,
        user_id=record.user_id,
        local_project_id=record.local_project_id,
        project_name=project.name if project else None,
        repository_connection_id=record.repository_connection_id,
        target_branch=record.target_branch,
        commit_sha=record.commit_sha,
        commit_url=record.commit_url,
        commit_message=record.commit_message,
        files_backed_up=backed_up,
        files_excluded=excluded,
        status=record.status,
        log_output=record.log_output,
        error_message=record.error_message,
        is_dry_run=record.is_dry_run,
        created_at=record.created_at,
    )


@router.get("/projects", response_model=list[LocalProjectResponse])
async def list_local_projects(
    user: User = Depends(current_user), db: Session = Depends(get_db)
) -> list[LocalProjectResponse]:
    projects = db.scalars(
        select(LocalProject).where(LocalProject.user_id == user.id).order_by(LocalProject.created_at.desc())
    ).all()
    results: list[LocalProjectResponse] = []
    for p in projects:
        repo = db.get(RepositoryConnection, p.repository_connection_id)
        results.append(_project_response(p, repo))
    return results


@router.post("/projects", response_model=LocalProjectResponse, status_code=201)
async def create_local_project(
    payload: LocalProjectCreate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> LocalProjectResponse:
    clean_path = payload.local_path.strip().strip('"').strip("'")
    target_dir = Path(clean_path)
    if not target_dir.is_dir():
        raise HTTPException(
            status_code=400,
            detail=f"The specified path is not a valid directory on the machine: {clean_path}",
        )

    repo = db.scalar(
        select(RepositoryConnection).where(
            (
                (RepositoryConnection.id == payload.repository_connection_id)
                | (RepositoryConnection.github_repository_id == payload.repository_connection_id)
            ),
            RepositoryConnection.user_id == user.id,
        )
    )
    if not repo:
        raise HTTPException(status_code=404, detail="Connected GitHub repository not found.")

    clean_target = payload.target_branch.strip().lstrip("/")
    if clean_target == repo.default_branch:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Safety Policy: Target backup branch cannot be the protected default branch '{repo.default_branch}'. "
                "Please specify a dedicated backup branch, e.g., 'backup/daily'."
            ),
        )

    project = LocalProject(
        user_id=user.id,
        repository_connection_id=repo.id,
        name=payload.name.strip(),
        local_path=str(target_dir.resolve()),
        target_branch=clean_target,
        backup_schedule=payload.backup_schedule.strip(),
        is_active=payload.is_active,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _project_response(project, repo)


@router.get("/projects/{project_id}", response_model=LocalProjectResponse)
async def get_local_project(
    project_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> LocalProjectResponse:
    project = db.scalar(
        select(LocalProject).where(LocalProject.id == project_id, LocalProject.user_id == user.id)
    )
    if not project:
        raise HTTPException(status_code=404, detail="Local project not found.")
    repo = db.get(RepositoryConnection, project.repository_connection_id)
    return _project_response(project, repo)


@router.put("/projects/{project_id}", response_model=LocalProjectResponse)
async def update_local_project(
    project_id: int,
    payload: LocalProjectUpdate,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> LocalProjectResponse:
    project = db.scalar(
        select(LocalProject).where(LocalProject.id == project_id, LocalProject.user_id == user.id)
    )
    if not project:
        raise HTTPException(status_code=404, detail="Local project not found.")
    repo = db.get(RepositoryConnection, project.repository_connection_id)

    if payload.target_branch is not None:
        clean_target = payload.target_branch.strip().lstrip("/")
        if repo and clean_target == repo.default_branch:
            raise HTTPException(
                status_code=400,
                detail=f"Safety Policy: Cannot target default branch '{repo.default_branch}'.",
            )
        project.target_branch = clean_target

    if payload.name is not None:
        project.name = payload.name.strip()
    if payload.backup_schedule is not None:
        project.backup_schedule = payload.backup_schedule.strip()
    if payload.is_active is not None:
        project.is_active = payload.is_active

    db.commit()
    db.refresh(project)
    return _project_response(project, repo)


@router.delete("/projects/{project_id}", status_code=204)
async def delete_local_project(
    project_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    project = db.scalar(
        select(LocalProject).where(LocalProject.id == project_id, LocalProject.user_id == user.id)
    )
    if not project:
        raise HTTPException(status_code=404, detail="Local project not found.")
    db.delete(project)
    db.commit()


@router.get("/projects/{project_id}/preview", response_model=BackupScanPreview)
async def preview_project_scan(
    project_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> BackupScanPreview:
    project = db.scalar(
        select(LocalProject).where(LocalProject.id == project_id, LocalProject.user_id == user.id)
    )
    if not project:
        raise HTTPException(status_code=404, detail="Local project not found.")

    local_dir = Path(project.local_path)
    if not local_dir.is_dir():
        raise HTTPException(status_code=400, detail="Local project directory not found on disk.")

    safe_files, excluded_secrets = scan_local_project(local_dir)
    return BackupScanPreview(
        local_path=project.local_path,
        target_branch=project.target_branch,
        safe_files=[
            ScannedFileDetail(
                path=f.path,
                status=f.status,
                size=f.size,
                is_secret=False,
            )
            for f in safe_files
        ],
        excluded_secrets=[
            ScannedFileDetail(
                path=f.path,
                status=f.status,
                size=f.size,
                is_secret=True,
                exclusion_reason=f.exclusion_reason,
            )
            for f in excluded_secrets
        ],
        total_safe_count=len(safe_files),
        total_excluded_count=len(excluded_secrets),
    )


@router.post("/projects/{project_id}/run", response_model=BackupRecordResponse)
async def run_backup(
    project_id: int,
    payload: BackupRunRequest = BackupRunRequest(),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> BackupRecordResponse:
    project = db.scalar(
        select(LocalProject).where(LocalProject.id == project_id, LocalProject.user_id == user.id)
    )
    if not project:
        raise HTTPException(status_code=404, detail="Local project not found.")

    record = await execute_backup(
        project=project,
        user=user,
        db=db,
        dry_run=payload.dry_run,
        custom_message=payload.custom_message,
    )
    return _record_response(record, project)


@router.get("/records", response_model=list[BackupRecordResponse])
async def list_backup_records(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[BackupRecordResponse]:
    records = db.scalars(
        select(BackupRecord).where(BackupRecord.user_id == user.id).order_by(BackupRecord.created_at.desc()).limit(limit)
    ).all()
    results: list[BackupRecordResponse] = []
    for r in records:
        proj = db.get(LocalProject, r.local_project_id)
        results.append(_record_response(r, proj))
    return results


@router.get("/records/{record_id}", response_model=BackupRecordResponse)
async def get_backup_record(
    record_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> BackupRecordResponse:
    record = db.scalar(
        select(BackupRecord).where(BackupRecord.id == record_id, BackupRecord.user_id == user.id)
    )
    if not record:
        raise HTTPException(status_code=404, detail="Backup record not found.")
    proj = db.get(LocalProject, record.local_project_id)
    return _record_response(record, proj)

