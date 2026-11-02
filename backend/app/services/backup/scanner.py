import os
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

# Sensitive filename patterns that must NEVER be staged
SENSITIVE_FILENAME_PATTERNS = [
    re.compile(r"^\.env(\..+)?$", re.IGNORECASE),
    re.compile(r"^.*\.env$", re.IGNORECASE),
    re.compile(r"^id_(rsa|dsa|ecdsa|ed25519)(\.pub)?$", re.IGNORECASE),
    re.compile(r"^.*\.(pem|key|pkcs12|pfx|p12|kdbx)$", re.IGNORECASE),
    re.compile(r"^(credentials|secrets|service[-_]?account|client[-_]?secret).*\.json$", re.IGNORECASE),
    re.compile(r"^.*(token|secret|password|private_key).*\.(json|txt|ya?ml)$", re.IGNORECASE),
]

# Sensitive content patterns that must NEVER be pushed
SENSITIVE_CONTENT_PATTERNS = [
    (re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"), "Private cryptographic key"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID"),
    (re.compile(r"ghp_[0-9a-zA-Z]{36}"), "GitHub Personal Access Token"),
    (re.compile(r"github_pat_[0-9a-zA-Z_]{30,}"), "GitHub Fine-Grained Personal Access Token"),
    (re.compile(r"sk-[0-9a-zA-Z]{20,}"), "OpenAI Secret Key"),
    (re.compile(r"(password|passwd|api[_-]?key|secret[_-]?key)\s*[:=]\s*['\"][^'\"]{6,}['\"]", re.IGNORECASE), "Plaintext credential or secret assignment"),
]

# Standard directories and files to always ignore
ALWAYS_IGNORED_DIRS = {
    ".git",
    ".next",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "dist",
    "build",
    "target",
    "out",
    ".turbo",
    ".coverage",
}


@dataclass
class ScannedFile:
    path: str
    status: str  # modified, added, deleted
    size: int
    is_secret: bool
    exclusion_reason: str | None = None
    content: str | None = None


def parse_gitignore(gitignore_path: Path) -> list[str]:
    patterns: list[str] = []
    if not gitignore_path.is_file():
        return patterns
    try:
        lines = gitignore_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
    except Exception:
        pass
    return patterns


def is_path_ignored(relative_path: str, gitignore_patterns: list[str]) -> bool:
    parts = relative_path.split("/")
    # Check if any parent dir is in ALWAYS_IGNORED_DIRS
    if any(part in ALWAYS_IGNORED_DIRS for part in parts[:-1]):
        return True
    filename = parts[-1]
    if filename in ALWAYS_IGNORED_DIRS:
        return True

    for pattern in gitignore_patterns:
        clean = pattern.rstrip("/")
        if clean in parts or relative_path == clean or relative_path.startswith(clean + "/"):
            return True
        if pattern.startswith("*.") and filename.endswith(pattern[1:]):
            return True
    return False


def is_sensitive_filename(path: str) -> tuple[bool, str | None]:
    name = PurePosixPath(path).name
    for pattern in SENSITIVE_FILENAME_PATTERNS:
        if pattern.match(name):
            return True, f"Filename matches sensitive pattern: '{name}'"
    return False, None


def is_sensitive_content(file_path: Path) -> tuple[bool, str | None]:
    try:
        # Only inspect files up to 1 MB for content secrets
        if file_path.stat().st_size > 1024 * 1024:
            return False, None
        content = file_path.read_text(encoding="utf-8", errors="replace")
        for pattern, reason in SENSITIVE_CONTENT_PATTERNS:
            if pattern.search(content):
                return True, f"Content contains {reason}"
    except Exception:
        pass
    return False, None


def scan_local_project(local_path: Path) -> tuple[list[ScannedFile], list[ScannedFile]]:
    """
    Scans a local project directory.
    Returns:
      safe_files: list[ScannedFile]
      excluded_secrets: list[ScannedFile]
    """
    if not local_path.is_dir():
        raise ValueError(f"Specified local path is not a valid directory: {local_path}")

    gitignore_patterns = parse_gitignore(local_path / ".gitignore")
    safe_files: list[ScannedFile] = []
    excluded_secrets: list[ScannedFile] = []

    # Check if this is a git repository
    git_dir = local_path / ".git"
    is_git_repo = git_dir.is_dir()

    # If git repo, use git status --porcelain to accurately find changes
    git_changed_files: dict[str, str] = {}
    if is_git_repo:
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain", "-uall"],
                cwd=str(local_path),
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if len(line) >= 4:
                        status_code = line[:2].strip()
                        raw_path = line[3:].strip().strip('"').replace("\\", "/")
                        if "->" in raw_path:
                            raw_path = raw_path.split("->")[-1].strip()
                        op = "deleted" if "D" in status_code else ("added" if status_code == "??" or "A" in status_code else "modified")
                        git_changed_files[raw_path] = op
        except Exception:
            pass

    # If git status gave us exact changed files, process those
    if git_changed_files:
        for rel_path, op in git_changed_files.items():
            if is_path_ignored(rel_path, gitignore_patterns):
                continue

            full_file = local_path / rel_path
            is_secret, reason = is_sensitive_filename(rel_path)

            if not is_secret and op != "deleted" and full_file.is_file():
                is_secret, reason = is_sensitive_content(full_file)

            size = full_file.stat().st_size if full_file.is_file() else 0
            scanned = ScannedFile(
                path=rel_path,
                status=op,
                size=size,
                is_secret=is_secret,
                exclusion_reason=reason,
            )
            if is_secret:
                excluded_secrets.append(scanned)
            else:
                safe_files.append(scanned)
        return safe_files, excluded_secrets

    # Fallback for non-git directory or when git status is empty: walk files
    for root, dirs, files in os.walk(local_path):
        dirs[:] = [d for d in dirs if d not in ALWAYS_IGNORED_DIRS]
        for f in files:
            full_file = Path(root) / f
            rel_path = full_file.relative_to(local_path).as_posix()

            if is_path_ignored(rel_path, gitignore_patterns):
                continue

            is_secret, reason = is_sensitive_filename(rel_path)
            if not is_secret and full_file.is_file():
                is_secret, reason = is_sensitive_content(full_file)

            size = full_file.stat().st_size if full_file.is_file() else 0
            scanned = ScannedFile(
                path=rel_path,
                status="added",
                size=size,
                is_secret=is_secret,
                exclusion_reason=reason,
            )
            if is_secret:
                excluded_secrets.append(scanned)
            else:
                safe_files.append(scanned)

    return safe_files, excluded_secrets

