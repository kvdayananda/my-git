import base64
import hashlib
import secrets

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, Request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.config import get_settings


def _serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    if not settings.app_secret_key:
        raise HTTPException(status_code=500, detail="APP_SECRET_KEY is not configured.")
    return URLSafeTimedSerializer(settings.app_secret_key, salt="gitauto-session")


def create_session_token(user_id: int) -> str:
    return _serializer().dumps({"user_id": user_id})


def read_session_user_id(token: str) -> int | None:
    try:
        payload = _serializer().loads(token, max_age=get_settings().session_ttl_seconds)
        return int(payload["user_id"])
    except (BadSignature, SignatureExpired, KeyError, TypeError, ValueError):
        return None


def create_oauth_state() -> str:
    return secrets.token_urlsafe(32)


def encrypt_token(token: str) -> str:
    secret = hashlib.sha256(get_settings().app_secret_key.encode()).digest()
    key = base64.urlsafe_b64encode(secret)
    return Fernet(key).encrypt(token.encode()).decode()


def decrypt_token(value: str) -> str:
    secret = hashlib.sha256(get_settings().app_secret_key.encode()).digest()
    key = base64.urlsafe_b64encode(secret)
    try:
        return Fernet(key).decrypt(value.encode()).decode()
    except (InvalidToken, UnicodeDecodeError) as exc:
        raise ValueError("Stored GitHub credential could not be decrypted.") from exc


def session_user_id(request: Request) -> int | None:
    token = request.cookies.get(get_settings().session_cookie_name)
    return read_session_user_id(token) if token else None
