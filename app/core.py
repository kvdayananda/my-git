"""CommitGuard Core Engine."""
import re
from dataclasses import dataclass
from typing import Optional

ALLOWED_TYPES = {"feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"}
PATTERN = re.compile(r"^([a-z]+)(?:\(([a-zA-Z0-9_-]+)\))?(!)?:\s+(.+)$")


@dataclass
class ValidationResult:
    is_valid: bool
    type: Optional[str] = None
    scope: Optional[str] = None
    is_breaking: bool = False
    description: Optional[str] = None
    error: Optional[str] = None


def validate_commit(message: str) -> ValidationResult:
    header = message.strip().splitlines()[0] if message.strip() else ""
    if not header:
        return ValidationResult(is_valid=False, error="Commit message is empty.")

    if len(header) > 72:
        return ValidationResult(is_valid=False, error=f"Header exceeds 72 characters ({len(header)} chars).")

    match = PATTERN.match(header)
    if not match:
        return ValidationResult(is_valid=False, error="Does not match format: '<type>(<scope>): <description>'")

    commit_type, scope, breaking_marker, desc = match.groups()
    if commit_type not in ALLOWED_TYPES:
        return ValidationResult(is_valid=False, error=f"Invalid type '{commit_type}'. Allowed: {sorted(ALLOWED_TYPES)}")

    if desc[0].isupper():
        return ValidationResult(is_valid=False, error="Description should start with a lowercase letter.")

    if desc.endswith("."):
        return ValidationResult(is_valid=False, error="Description should not end with a period.")

    return ValidationResult(
        is_valid=True,
        type=commit_type,
        scope=scope,
        is_breaking=bool(breaking_marker),
        description=desc,
    )
