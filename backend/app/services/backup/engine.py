import json
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.db.base import utc_now
from app.db.models import BackupRecord, GitHubConnection, LocalProject, RepositoryConnection, User
from app.services.backup.scanner import scan_local_project
from app.services.github.client import GitHubClient, GitHubError
from app.services.security import decrypt_token

logger = logging.getLogger(__name__)


class BackupSafetyError(Exception):
    """Raised when a safety rule would be violated."""
    pass


async def execute_backup(
    *,
    project: LocalProject,
    user: User,
    db: Session,
    dry_run: bool = False,
    custom_message: str | None = None,
) -> BackupRecord:
    logs: list[str] = []

    def log(msg: str) -> None:
        timestamp = utc_now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        logs.append(entry)
        logger.info("backup project_id=%s %s", project.id, msg)

    log(f"Initiating {'DRY-RUN' if dry_run else 'LIVE'} backup for '{project.name}'")
    local_dir = Path(project.local_path)

    # Safety Check 1: Directory exists
    if not local_dir.is_dir():
        err = f"Local project directory does not exist: {project.local_path}"
        log(f"ERROR: {err}")
        record = BackupRecord(
            user_id=user.id,
            local_project_id=project.id,
            repository_connection_id=project.repository_connection_id,
            target_branch=project.target_branch,
            commit_message="Backup failed - invalid directory",
            files_backed_up="[]",
            files_excluded="[]",
            status="failed",
            log_output="\n".join(logs),
            error_message=err,
            is_dry_run=dry_run,
        )
        db.add(record)
        project.last_backup_at = utc_now()
        project.last_backup_status = "failed"
        db.commit()
        db.refresh(record)
        return record

    # Safety Check 2: Repository connection exists
    repo = db.get(RepositoryConnection, project.repository_connection_id)
    if not repo:
        err = "Connected GitHub repository was not found."
        log(f"ERROR: {err}")
        record = BackupRecord(
            user_id=user.id,
            local_project_id=project.id,
            repository_connection_id=project.repository_connection_id,
            target_branch=project.target_branch,
            commit_message="Backup failed - missing repository",
            files_backed_up="[]",
            files_excluded="[]",
            status="failed",
            log_output="\n".join(logs),
            error_message=err,
            is_dry_run=dry_run,
        )
        db.add(record)
        project.last_backup_at = utc_now()
        project.last_backup_status = "failed"
        db.commit()
        db.refresh(record)
        return record

    # Safety Check 3: Protected default branch check
    # Rule: "Never push directly to protected default branches"
    clean_target = project.target_branch.strip().lstrip("/").replace("refs/heads/", "")
    clean_default = repo.default_branch.strip().lstrip("/").replace("refs/heads/", "")
    if clean_target == clean_default:
        err = (
            f"Safety Violation: Cannot push backup directly to protected default branch '{clean_default}'. "
            f"Please configure a dedicated backup branch (e.g., 'backup/daily')."
        )
        log(f"SAFETY ERROR: {err}")
        record = BackupRecord(
            user_id=user.id,
            local_project_id=project.id,
            repository_connection_id=repo.id,
            target_branch=clean_target,
            commit_message="Backup rejected - protected branch safety rule",
            files_backed_up="[]",
            files_excluded="[]",
            status="failed",
            log_output="\n".join(logs),
            error_message=err,
            is_dry_run=dry_run,
        )
        db.add(record)
        project.last_backup_at = utc_now()
        project.last_backup_status = "failed"
        db.commit()
        db.refresh(record)
        return record

    # Step 4: Scan directory with secret & sensitive file filtering
    log(f"Scanning directory: {local_dir}")
    safe_files, excluded_secrets = scan_local_project(local_dir)

    log(f"Scan complete: {len(safe_files)} safe files detected, {len(excluded_secrets)} sensitive/secret files excluded")
    for sec in excluded_secrets:
        log(f"  [EXCLUDED SECRET] {sec.path} ({sec.exclusion_reason})")

    safe_paths = [f.path for f in safe_files]
    excluded_paths = [f"{f.path}: {f.exclusion_reason}" for f in excluded_secrets]

    # Step 5: Check if any safe files exist to commit
    if not safe_files:
        log("No safe changes or files found to back up. Backup skipped.")
        record = BackupRecord(
            user_id=user.id,
            local_project_id=project.id,
            repository_connection_id=repo.id,
            target_branch=clean_target,
            commit_message="No changes detected",
            files_backed_up="[]",
            files_excluded=json.dumps(excluded_paths),
            status="skipped_no_changes",
            log_output="\n".join(logs),
            error_message=None,
            is_dry_run=dry_run,
        )
        db.add(record)
        project.last_backup_at = utc_now()
        project.last_backup_status = "skipped_no_changes"
        db.commit()
        db.refresh(record)
        return record

    commit_msg = (
        custom_message
        or f"backup(daily): {utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')} - {len(safe_files)} files backed up"
    )

    # Step 6: Handle Dry-Run
    if dry_run:
        log("DRY-RUN completed successfully. No remote changes were pushed.")
        for sf in safe_files[:20]:
            log(f"  [WOULD STAGE] {sf.path} ({sf.status}, {sf.size} bytes)")
        if len(safe_files) > 20:
            log(f"  ... and {len(safe_files) - 20} more safe files.")

        record = BackupRecord(
            user_id=user.id,
            local_project_id=project.id,
            repository_connection_id=repo.id,
            target_branch=clean_target,
            commit_message=commit_msg,
            files_backed_up=json.dumps(safe_paths),
            files_excluded=json.dumps(excluded_paths),
            status="dry_run",
            log_output="\n".join(logs),
            error_message=None,
            is_dry_run=True,
        )
        db.add(record)
        project.last_backup_at = utc_now()
        project.last_backup_status = "dry_run"
        db.commit()
        db.refresh(record)
        return record

    # Step 7: Live Backup to GitHub
    log(f"Authenticating with GitHub to push to branch '{clean_target}'...")
    conn = db.query(GitHubConnection).filter(GitHubConnection.user_id == user.id).first()
    if not conn:
        err = "GitHub connection not found for user."
        log(f"ERROR: {err}")
        record = BackupRecord(
            user_id=user.id,
            local_project_id=project.id,
            repository_connection_id=repo.id,
            target_branch=clean_target,
            commit_message=commit_msg,
            files_backed_up=json.dumps(safe_paths),
            files_excluded=json.dumps(excluded_paths),
            status="failed",
            log_output="\n".join(logs),
            error_message=err,
            is_dry_run=False,
        )
        db.add(record)
        project.last_backup_at = utc_now()
        project.last_backup_status = "failed"
        db.commit()
        db.refresh(record)
        return record

    try:
        client = GitHubClient(decrypt_token(conn.encrypted_access_token))

        # Check existing remote backup branch head
        log(f"Checking remote ref: {clean_target}")
        remote_sha = await client.ref(repo.owner, repo.name, clean_target)

        # If backup branch doesn't exist, branch off default branch
        parent_sha: str | None = remote_sha
        if not parent_sha:
            log(f"Branch '{clean_target}' does not exist yet. Resolving default branch '{clean_default}' as base...")
            default_sha = await client.ref(repo.owner, repo.name, clean_default)
            parent_sha = default_sha

        # Create Git blobs for safe files
        entries: list[dict[str, str | None]] = []
        log(f"Creating Git blobs for {len(safe_files)} safe files (credentials & secrets excluded)...")
        for file in safe_files:
            file_abs = local_dir / file.path
            if file.status == "deleted" or not file_abs.is_file():
                entries.append({"path": file.path, "mode": "100644", "type": "blob", "sha": None})
            else:
                try:
                    content_str = file_abs.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    continue
                blob_sha = await client.create_blob(repo.owner, repo.name, content_str)
                entries.append({"path": file.path, "mode": "100644", "type": "blob", "sha": blob_sha})

        # Resolve base tree
        base_tree_sha: str | None = None
        if parent_sha and parent_sha != "empty":
            try:
                base_commit = await client.commit(repo.owner, repo.name, parent_sha)
                base_tree_sha = str(base_commit["commit"]["tree"]["sha"])
            except Exception:
                base_tree_sha = None

        log("Creating Git tree on remote repository...")
        tree_sha = await client.create_tree(repo.owner, repo.name, base_tree_sha or "", entries)

        log("Creating backup commit...")
        parents = [parent_sha] if (parent_sha and parent_sha != "empty") else []
        new_commit = await client.create_commit(
            owner=repo.owner,
            name=repo.name,
            message=commit_msg,
            tree_sha=tree_sha,
            parent_sha=parent_sha or "",
        )
        new_commit_sha = str(new_commit["sha"])
        log(f"Created commit SHA: {new_commit_sha}")

        # Update or create branch ref
        if remote_sha:
            # Update existing ref via POST
            try:
                await client._request(
                    "PATCH",
                    f"/repos/{repo.owner}/{repo.name}/git/refs/heads/{clean_target}",
                    json={"sha": new_commit_sha, "force": False},
                )
            except Exception:
                # Fallback to create_ref if PATCH not supported
                await client.create_ref(repo.owner, repo.name, clean_target, new_commit_sha)
        else:
            await client.create_ref(repo.owner, repo.name, clean_target, new_commit_sha)

        # Step 8: Verification of remote commit SHA
        log("Verifying remote branch head matches new commit SHA...")
        verified_sha = await client.ref(repo.owner, repo.name, clean_target)
        if verified_sha != new_commit_sha and not client.is_demo:
            raise BackupSafetyError(
                f"Remote verification failed: expected commit {new_commit_sha}, but remote head is {verified_sha}"
            )

        log(f"Remote SHA verified successfully: {verified_sha}")
        commit_url = f"https://github.com/{repo.owner}/{repo.name}/commit/{new_commit_sha}"

        record = BackupRecord(
            user_id=user.id,
            local_project_id=project.id,
            repository_connection_id=repo.id,
            target_branch=clean_target,
            commit_sha=new_commit_sha,
            commit_url=commit_url,
            commit_message=commit_msg,
            files_backed_up=json.dumps(safe_paths),
            files_excluded=json.dumps(excluded_paths),
            status="success",
            log_output="\n".join(logs),
            error_message=None,
            is_dry_run=False,
        )
        db.add(record)
        project.last_backup_at = utc_now()
        project.last_backup_status = "success"
        db.commit()
        db.refresh(record)
        log("Backup completed and persisted successfully.")
        return record

    except (GitHubError, Exception) as exc:
        err = f"Remote backup failed: {exc}"
        log(f"ERROR: {err}")
        record = BackupRecord(
            user_id=user.id,
            local_project_id=project.id,
            repository_connection_id=repo.id,
            target_branch=clean_target,
            commit_message=commit_msg,
            files_backed_up=json.dumps(safe_paths),
            files_excluded=json.dumps(excluded_paths),
            status="failed",
            log_output="\n".join(logs),
            error_message=str(exc),
            is_dry_run=False,
        )
        db.add(record)
        project.last_backup_at = utc_now()
        project.last_backup_status = "failed"
        db.commit()
        db.refresh(record)
        return record

