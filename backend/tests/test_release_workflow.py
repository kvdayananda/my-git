from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.api.releases import _claim_release, _update_owned
from app.db.base import Base, utc_now
from app.db.models import DevelopmentTask, ProposedChange, ReleaseCandidate, RepositoryConnection, TestRun as _TestRunModel, User
from app.services.release import branch_name, candidate_hash, validate_candidate_changes, valid_branch_name


def _change(path: str = "src/main.py", content: str = "print('ok')") -> ProposedChange:
    return ProposedChange(
        development_task_id=7,
        file_path=path,
        operation="modify",
        reason="Apply the approved implementation.",
        proposed_content=content,
    )


def test_candidate_hash_is_order_independent_and_content_bound() -> None:
    first = [_change("b.py", "b"), _change("a.py", "a")]
    second = list(reversed(first))
    assert candidate_hash(first, "base-a") == candidate_hash(second, "base-a")
    assert candidate_hash(first, "base-a") != candidate_hash(first, "base-b")
    assert candidate_hash(first, "base-a") != candidate_hash([_change("b.py", "changed"), _change("a.py", "a")], "base-a")


def test_candidate_branch_name_is_dedicated_and_valid() -> None:
    name = branch_name(7)
    assert name.startswith("gitauto/task-7-")
    assert valid_branch_name(name)
    assert not valid_branch_name("main")
    assert not valid_branch_name("gitauto/task-7-../../main")


def test_candidate_validation_rejects_protected_paths_and_secrets() -> None:
    class Task:
        status = "awaiting_review"
        base_commit_sha = "base-a"

    errors, _ = validate_candidate_changes(
        [_change(".env", 'token = "a-real-secret-value"')],
        Task(),  # type: ignore[arg-type]
        Settings(),
    )
    assert any("Protected" in error for error in errors)
    assert any("secret" in error.lower() for error in errors)


def test_database_claim_is_atomic_across_two_sessions() -> None:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    setup = sessions()
    user = User(github_id=901, github_login="lock-user")
    repository = RepositoryConnection(
        user_id=0, github_repository_id=901, owner="octocat", name="lock",
        default_branch="main", visibility="private", html_url="https://github.com/octocat/lock",
        can_push=True,
    )
    setup.add(user)
    setup.flush()
    repository.user_id = user.id
    setup.add(repository)
    setup.flush()
    task = DevelopmentTask(
        user_id=user.id, repository_connection_id=repository.id, base_commit_sha="base",
        task_type="improvement", instructions="lock", status="awaiting_review",
        workspace_path="C:\\workspace", plan="{}",
    )
    setup.add(task)
    setup.flush()
    test_run = _TestRunModel(
        user_id=user.id, development_task_id=task.id, base_commit_sha="base",
        candidate_hash="hash", execution_profile="python-pytest",
        command_classification="pytest", status="passed",
    )
    setup.add(test_run)
    setup.flush()
    candidate = ReleaseCandidate(
        user_id=user.id, repository_connection_id=repository.id, development_task_id=task.id,
        test_run_id=test_run.id, base_commit_sha="base", target_branch="main",
        candidate_branch="gitauto/task-1-abcdef12", approved_file_paths="[]",
        diff_hash="hash", secret_scan_status="passed", status="approved",
    )
    setup.add(candidate)
    setup.commit()
    candidate_id, user_id = candidate.id, user.id
    setup.close()

    first, second = sessions(), sessions()
    now = utc_now()
    assert _claim_release(first, candidate_id, user_id, now, now + timedelta(minutes=5), "first")
    assert not _claim_release(second, candidate_id, user_id, now, now + timedelta(minutes=5), "second")
    first.close()
    second.close()


def test_expired_lease_can_be_reclaimed_but_stale_worker_cannot_update() -> None:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    setup = sessions()
    user = User(github_id=902, github_login="expiry-user")
    setup.add(user)
    setup.flush()
    repository = RepositoryConnection(
        user_id=user.id, github_repository_id=902, owner="octocat", name="expiry",
        default_branch="main", visibility="private", html_url="https://github.com/octocat/expiry",
        can_push=True,
    )
    setup.add(repository)
    setup.flush()
    task = DevelopmentTask(
        user_id=user.id, repository_connection_id=repository.id, base_commit_sha="base",
        task_type="improvement", instructions="expiry", status="awaiting_review",
        workspace_path="C:\\workspace", plan="{}",
    )
    setup.add(task)
    setup.flush()
    test_run = _TestRunModel(
        user_id=user.id, development_task_id=task.id, base_commit_sha="base",
        candidate_hash="hash", execution_profile="python-pytest",
        command_classification="pytest", status="passed",
    )
    setup.add(test_run)
    setup.flush()
    candidate = ReleaseCandidate(
        user_id=user.id, repository_connection_id=repository.id, development_task_id=task.id,
        test_run_id=test_run.id, base_commit_sha="base", target_branch="main",
        candidate_branch="gitauto/task-2-abcdef12", approved_file_paths="[]",
        diff_hash="hash", secret_scan_status="passed", status="approved",
    )
    setup.add(candidate)
    setup.commit()
    candidate_id, user_id = candidate.id, user.id
    setup.close()

    first, second = sessions(), sessions()
    now = utc_now()
    assert _claim_release(first, candidate_id, user_id, now, now - timedelta(seconds=1), "expired")
    assert _claim_release(second, candidate_id, user_id, now, now + timedelta(minutes=5), "current")
    assert not _update_owned(first, candidate_id, "expired", {"status": "released"})
    assert _update_owned(second, candidate_id, "current", {"error_summary": "owned"})
    first.close()
    second.close()
