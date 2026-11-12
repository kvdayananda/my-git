"""Tests for CommitGuard Validator."""
from app.core import validate_commit
from app.main import CommitGuard


def test_valid_commits():
    res1 = validate_commit("feat(auth): implement token rotation")
    assert res1.is_valid is True
    assert res1.type == "feat"
    assert res1.scope == "auth"

    res2 = validate_commit("fix: resolve off-by-one index error")
    assert res2.is_valid is True
    assert res2.scope is None


def test_invalid_commits():
    assert validate_commit("feat: Implement user login").is_valid is False
    assert validate_commit("fix: correct calculation.").is_valid is False
    assert validate_commit("random: unexpected update").is_valid is False


def test_breaking_change():
    res = validate_commit("feat(api)!: remove deprecated v1 endpoints")
    assert res.is_valid is True
    assert res.is_breaking is True


def test_facade():
    res = CommitGuard.check("docs(readme): add installation instructions")
    assert res["valid"] is True
    assert res["type"] == "docs"
