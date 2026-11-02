import re
from pathlib import PurePosixPath

from app.core.config import Settings

PROTECTED = re.compile(
    r"(^|/)(\.env(\..*)?|.*\.(pem|key|p12|pfx|crt)|.*(credentials|secrets?).*)$",
    re.IGNORECASE,
)
SECRET_VALUE = re.compile(r"(api[_-]?key|password|secret|token)\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE)


def safe_path(path: str) -> str:
    if not path or "\\" in path or path.startswith("/") or re.match(r"^[A-Za-z]:", path):
        raise ValueError("Generated paths must be relative POSIX paths.")
    normalized = str(PurePosixPath(path))
    if normalized in {".", ""} or normalized == ".." or normalized.startswith("../"):
        raise ValueError("Generated path escapes the task workspace.")
    if PROTECTED.search(normalized):
        raise ValueError("Protected files cannot be generated or modified.")
    return normalized


def validate_change(path: str, operation: str, content: str, settings: Settings) -> list[str]:
    errors: list[str] = []
    try:
        safe_path(path)
    except ValueError as exc:
        errors.append(str(exc))
    if operation not in {"create", "modify", "delete"}:
        errors.append("Unsupported file operation.")
    if operation != "delete" and not content:
        errors.append("Create and modify operations require content.")
    if len(content.encode("utf-8")) > settings.workspace_max_size_bytes:
        errors.append("Generated file exceeds the configured size limit.")
    if SECRET_VALUE.search(content):
        errors.append("Generated content contains a credential-like value.")
    return errors


def validate_plan_paths(plan: dict, settings: Settings) -> list[str]:
    errors: list[str] = []
    paths = plan.get("files_to_create", []) + plan.get("files_to_modify", [])
    for path in paths:
        try:
            safe_path(path)
        except ValueError as exc:
            errors.append(f"{path}: {exc}")
    if len(paths) > settings.workspace_max_files:
        errors.append("Plan exceeds the configured file limit.")
    return errors
