"""CommitGuard Main Application."""
from app.core import validate_commit, ValidationResult


class CommitGuard:
    @staticmethod
    def check(msg: str) -> dict:
        result = validate_commit(msg)
        return {
            "valid": result.is_valid,
            "type": result.type,
            "scope": result.scope,
            "breaking": result.is_breaking,
            "error": result.error,
        }
