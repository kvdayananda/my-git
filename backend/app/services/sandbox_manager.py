import asyncio
import shutil
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.db.base import utc_now
from app.services.sandbox_policy import command_for_profile


class SandboxUnavailable(Exception):
    pass


def _sync_docker_ready() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        res = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
        )
        return res.returncode == 0
    except (OSError, FileNotFoundError, subprocess.SubprocessError):
        return False


async def docker_ready(settings: Settings) -> bool:
    return await asyncio.to_thread(_sync_docker_ready)


async def run_in_sandbox(workspace: Path, profile: str, settings: Settings) -> dict[str, object]:
    if not await docker_ready(settings):
        raise SandboxUnavailable("Docker daemon is unavailable; test execution is disabled.")
    executable, args = command_for_profile(profile)
    if not shutil.which("docker") or executable != "pytest":
        raise SandboxUnavailable("The trusted sandbox execution profile is unavailable.")
    snapshot = Path(tempfile.mkdtemp(prefix="test-run-", dir=workspace.parent))
    try:
        for path in workspace.rglob("*"):
            if path.is_symlink() or not path.is_file() and not path.is_dir():
                raise SandboxUnavailable("Workspace contains an unsafe filesystem entry.")
        shutil.copytree(workspace, snapshot, dirs_exist_ok=True, symlinks=False)
    except Exception:
        shutil.rmtree(snapshot, ignore_errors=True)
        raise

    container_name = f"gitauto-test-{uuid4().hex}"
    start = utc_now()
    command = [
        "docker", "run", "--rm", "--name", container_name, "--network", "none", "--read-only",
        "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--pids-limit", str(settings.sandbox_pids_limit),
        "--memory", settings.sandbox_memory_limit, "--cpus", str(settings.sandbox_cpu_limit),
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
        "--mount", f"type=bind,source={snapshot.resolve()},target=/workspace",
        "--workdir", "/workspace", "--user", "1000:1000", settings.sandbox_image, *args,
    ]

    def _execute() -> dict[str, object]:
        timed_out = False
        stdout, stderr = b"", b""
        returncode = None
        try:
            proc = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=settings.sandbox_timeout_seconds,
            )
            returncode = proc.returncode
            stdout = proc.stdout
            stderr = proc.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
            subprocess.run(["docker", "rm", "--force", container_name], capture_output=True)
        except OSError:
            raise

        end = utc_now()
        return {
            "status": "timed_out" if timed_out else ("passed" if returncode == 0 else "failed"),
            "exit_code": None if timed_out else returncode,
            "started_at": start,
            "ended_at": end,
            "duration_ms": int((end - start).total_seconds() * 1000),
            "timed_out": timed_out,
            "stdout": stdout[: settings.sandbox_output_limit_bytes].decode("utf-8", errors="replace"),
            "stderr": stderr[: settings.sandbox_output_limit_bytes].decode("utf-8", errors="replace"),
            "summary": "Tests passed." if returncode == 0 and not timed_out else "Tests did not pass.",
        }

    try:
        return await asyncio.to_thread(_execute)
    finally:
        shutil.rmtree(snapshot, ignore_errors=True)
