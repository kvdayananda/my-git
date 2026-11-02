import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import GitHubConnection, RepositoryConnection, User
from app.db.session import get_db
from app.schemas.repository import Repository, RepositoryConnectRequest, RepositoryPage
from app.services.github.client import GitHubClient, GitHubError
from app.services.security import decrypt_token
from app.api.auth import current_user

router = APIRouter(prefix="/repositories", tags=["repositories"])
logger = logging.getLogger(__name__)


def github_client(user: User, db: Session) -> GitHubClient:
    connection = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    if connection is None:
        raise HTTPException(status_code=401, detail="Connect GitHub before accessing repositories.")
    try:
        return GitHubClient(decrypt_token(connection.encrypted_access_token))
    except ValueError as exc:
        raise HTTPException(status_code=500, detail="The GitHub connection must be re-established.") from exc


def repository_response(data: dict, connected: bool = False) -> Repository:
    permissions = data.get("permissions") or {}
    return Repository(
        id=int(data["id"]),
        name=data["name"],
        owner=data["owner"]["login"],
        description=data.get("description"),
        default_branch=data.get("default_branch") or "unknown",
        visibility=data.get("visibility") or ("private" if data.get("private") else "public"),
        language=data.get("language"),
        html_url=data["html_url"],
        can_push=bool(permissions.get("push")),
        connected=connected,
    )


@router.get("", response_model=RepositoryPage)
async def list_repositories(
    page: int = Query(1, ge=1, le=100),
    per_page: int = Query(30, ge=1, le=100),
    search: str = Query("", max_length=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> RepositoryPage:
    try:
        repositories = await github_client(user, db).repositories(page, per_page, search)
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    connected_ids = set(
        db.scalars(select(RepositoryConnection.github_repository_id).where(RepositoryConnection.user_id == user.id))
    )
    items = [repository_response(item, int(item["id"]) in connected_ids) for item in repositories]
    logger.info("repository listing completed user_id=%s count=%s", user.id, len(items))
    return RepositoryPage(items=items, page=page, per_page=per_page, has_next=len(items) == per_page)


@router.get("/connections", response_model=list[Repository])
async def connected_repositories(user: User = Depends(current_user), db: Session = Depends(get_db)) -> list[Repository]:
    connections = db.scalars(select(RepositoryConnection).where(RepositoryConnection.user_id == user.id)).all()
    return [
        Repository(
            id=item.github_repository_id, name=item.name, owner=item.owner, description=item.description,
            default_branch=item.default_branch, visibility=item.visibility, language=item.language,
            html_url=item.html_url, can_push=item.can_push, connected=True,
        )
        for item in connections
    ]


@router.get("/{repository_id}", response_model=Repository)
async def repository_details(
    repository_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> Repository:
    connection = db.scalar(
        select(RepositoryConnection).where(
            RepositoryConnection.user_id == user.id,
            RepositoryConnection.github_repository_id == repository_id,
        )
    )
    if connection is not None:
        return Repository(
            id=connection.github_repository_id, name=connection.name, owner=connection.owner,
            description=connection.description, default_branch=connection.default_branch,
            visibility=connection.visibility, language=connection.language, html_url=connection.html_url,
            can_push=connection.can_push, connected=True,
        )
    try:
        data = await github_client(user, db).repository(repository_id)
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return repository_response(data)


@router.post("/connect", response_model=Repository, status_code=201)
async def connect_repository(
    payload: RepositoryConnectRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> Repository:
    existing = db.scalar(
        select(RepositoryConnection).where(
            RepositoryConnection.user_id == user.id,
            RepositoryConnection.github_repository_id == payload.repository_id,
        )
    )
    if existing:
        return repository_response({
            "id": existing.github_repository_id, "name": existing.name, "owner": {"login": existing.owner},
            "description": existing.description, "default_branch": existing.default_branch,
            "visibility": existing.visibility, "language": existing.language, "html_url": existing.html_url,
            "permissions": {"push": existing.can_push},
        }, True)
    try:
        data = await github_client(user, db).repository(payload.repository_id)
    except GitHubError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    repository = RepositoryConnection(
        user_id=user.id, github_repository_id=int(data["id"]), owner=data["owner"]["login"], name=data["name"],
        description=data.get("description"), default_branch=data.get("default_branch") or "unknown",
        visibility=data.get("visibility") or ("private" if data.get("private") else "public"),
        language=data.get("language"), html_url=data["html_url"], can_push=bool((data.get("permissions") or {}).get("push")),
    )
    db.add(repository)
    db.commit()
    logger.info(
        "repository connection persisted user_id=%s repository_id=%s owner=%s name=%s",
        user.id, repository.github_repository_id, repository.owner, repository.name,
    )
    return repository_response(data, True)


@router.delete("/{repository_id}/connection", status_code=204)
async def disconnect_repository(
    repository_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
) -> None:
    repository = db.scalar(
        select(RepositoryConnection).where(
            RepositoryConnection.user_id == user.id, RepositoryConnection.github_repository_id == repository_id
        )
    )
    if repository is None:
        raise HTTPException(status_code=404, detail="Repository connection not found.")
    db.delete(repository)
    db.commit()
import logging
