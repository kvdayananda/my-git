import hmac
import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import GitHubConnection, User
from app.db.session import get_db
from app.schemas.auth import AuthStatus, AuthenticatedUser, PatLoginRequest
from app.services.github.client import GitHubClient, GitHubError
from app.services.security import (
    create_oauth_state,
    create_session_token,
    encrypt_token,
    session_user_id,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["authentication"])


def serialize_user(user: User) -> AuthenticatedUser:
    display_name = user.custom_display_name or user.github_name or user.github_login
    effective_avatar = user.avatar_url or user.github_avatar_url
    return AuthenticatedUser(
        id=user.id,
        github_id=user.github_id,
        login=user.github_login,
        name=user.github_name,
        email=user.github_email,
        custom_display_name=user.custom_display_name,
        display_name=display_name,
        avatar_url=effective_avatar,
    )


def current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = session_user_id(request)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Authentication is required.")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication is required.")
    return user


@router.get("/github")
async def github_login(response: Response) -> Response:
    settings = get_settings()
    if not settings.github_configured or not settings.app_secret_key:
        raise HTTPException(
            status_code=503,
            detail="GitHub OAuth is not configured (client credentials and APP_SECRET_KEY are required).",
        )
    state = create_oauth_state()
    query = urlencode({
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": "read:user user:email repo",
        "state": state,
    })
    redirect = RedirectResponse(f"https://github.com/login/oauth/authorize?{query}", status_code=307)
    redirect.set_cookie(
        settings.oauth_state_cookie_name,
        state,
        max_age=600,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
    )
    return redirect


@router.get("/demo-login")
async def demo_login(db: Session = Depends(get_db)) -> RedirectResponse:
    settings = get_settings()
    destination = settings.frontend_url.rstrip("/") + "/"
    user = db.scalar(select(User).where(User.github_login == "demo-developer"))
    if user is None:
        user = User(
            github_id=999999,
            github_login="demo-developer",
            github_name="Demo Developer",
            github_email="demo@gitauto.ai",
        )
        db.add(user)
        db.flush()
        connection = GitHubConnection(
            user_id=user.id,
            encrypted_access_token=encrypt_token("demo-github-token"),
            scope="read:user user:email repo",
        )
        db.add(connection)
        db.commit()
    redirect = RedirectResponse(destination, status_code=303)
    redirect.set_cookie(
        settings.session_cookie_name,
        create_session_token(user.id),
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
    )
    return redirect


@router.get("/github/callback")
async def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()
    destination = settings.frontend_url.rstrip("/") + "/"
    if error or not code or not state:
        logger.info("oauth callback rejected stage=provider_denied_or_missing_parameters")
        return RedirectResponse(f"{destination}?auth_error=denied", status_code=303)
    saved_state = request.cookies.get(settings.oauth_state_cookie_name)
    if not saved_state or not hmac.compare_digest(saved_state, state):
        logger.warning("oauth callback rejected stage=state_validation")
        return RedirectResponse(f"{destination}?auth_error=invalid_state", status_code=303)
    if not settings.github_configured or not settings.app_secret_key:
        logger.error("oauth callback rejected stage=configuration")
        return RedirectResponse(f"{destination}?auth_error=not_configured", status_code=303)

    try:
        logger.info("oauth callback stage=token_exchange_started")
        client = GitHubClient("")
        token_data = await client.exchange_code(
            settings.github_client_id, settings.github_client_secret, code, settings.github_redirect_uri
        )
        logger.info("oauth callback stage=token_exchange_succeeded")
        client = GitHubClient(token_data["access_token"])
        profile = await client.current_user()
        logger.info("oauth callback stage=profile_fetch_succeeded")
    except GitHubError:
        logger.warning("oauth callback failed stage=github_exchange_or_profile")
        return RedirectResponse(f"{destination}?auth_error=github", status_code=303)

    user = db.scalar(select(User).where(User.github_id == int(profile["id"])))
    if user is None:
        user = User(github_id=int(profile["id"]), github_login=profile["login"])
        db.add(user)
    user.github_login = profile["login"]
    user.github_name = profile.get("name")
    user.github_email = profile.get("email")
    if profile.get("avatar_url"):
        user.github_avatar_url = profile["avatar_url"]
    db.flush()
    connection = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    if connection is None:
        connection = GitHubConnection(
            user_id=user.id,
            encrypted_access_token=encrypt_token(token_data["access_token"]),
            scope=token_data.get("scope"),
        )
        db.add(connection)
    else:
        connection.encrypted_access_token = encrypt_token(token_data["access_token"])
        connection.scope = token_data.get("scope")
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("oauth callback failed stage=database_commit")
        return RedirectResponse(f"{destination}?auth_error=storage", status_code=303)
    logger.info("oauth callback stage=identity_persisted")
    redirect = RedirectResponse(destination, status_code=303)
    redirect.set_cookie(
        settings.session_cookie_name,
        create_session_token(user.id),
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
    )
    redirect.delete_cookie(settings.oauth_state_cookie_name)
    logger.info("oauth callback stage=session_cookie_issued")
    return redirect


@router.get("/me", response_model=AuthStatus)
async def me(request: Request, db: Session = Depends(get_db)) -> AuthStatus:
    user_id = session_user_id(request)
    if user_id is None:
        return AuthStatus(authenticated=False)
    user = db.get(User, user_id)
    return AuthStatus(authenticated=bool(user), user=serialize_user(user) if user else None)


@router.post("/pat", response_model=AuthStatus)
async def login_with_pat(
    payload: PatLoginRequest,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthStatus:
    token = payload.token.strip().strip('"').strip("'")
    if token.lower().startswith("bearer "):
        token = token[7:].strip()
    if token.lower() in ("demo", "demo-developer", "demo-github-token"):
        token = "demo-github-token"
    if not token:
        raise HTTPException(status_code=400, detail="Personal Access Token cannot be empty.")

    settings = get_settings()
    if not settings.app_secret_key:
        raise HTTPException(status_code=500, detail="APP_SECRET_KEY is not configured.")

    client = GitHubClient(token)
    try:
        profile = await client.current_user()
    except GitHubError as exc:
        raise HTTPException(
            status_code=401,
            detail=f"GitHub token verification failed: {exc.message}",
        ) from exc

    github_id = int(profile["id"])
    github_login = profile["login"]
    user = db.scalar(select(User).where(User.github_id == github_id))
    if user is None:
        user = User(
            github_id=github_id,
            github_login=github_login,
            github_name=profile.get("name"),
            github_email=profile.get("email"),
            github_avatar_url=profile.get("avatar_url"),
        )
        db.add(user)
    else:
        user.github_login = github_login
        user.github_name = profile.get("name")
        user.github_email = profile.get("email")
        if profile.get("avatar_url"):
            user.github_avatar_url = profile["avatar_url"]
    db.flush()

    connection = db.scalar(select(GitHubConnection).where(GitHubConnection.user_id == user.id))
    if connection is None:
        connection = GitHubConnection(
            user_id=user.id,
            encrypted_access_token=encrypt_token(token),
            scope="repo,read:user,user:email",
        )
        db.add(connection)
    else:
        connection.encrypted_access_token = encrypt_token(token)
        connection.scope = "repo,read:user,user:email"

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to persist PAT identity")
        raise HTTPException(status_code=500, detail="Failed to store user authentication.")

    response.set_cookie(
        settings.session_cookie_name,
        create_session_token(user.id),
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
    )
    return AuthStatus(authenticated=True, user=serialize_user(user))


@router.post("/logout", status_code=204)
async def logout(response: Response) -> Response:
    response.delete_cookie(get_settings().session_cookie_name)
    response.status_code = 204
    return response
