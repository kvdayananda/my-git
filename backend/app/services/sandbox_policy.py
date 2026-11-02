from pathlib import Path

from app.core.config import Settings


def available_profiles(workspace: Path, settings: Settings) -> list[dict[str, str | bool]]:
    has_python_metadata = any((workspace / name).is_file() for name in ("pyproject.toml", "pytest.ini", "setup.cfg"))
    if not has_python_metadata:
        return [{"name": "python-pytest", "command_classification": "pytest", "available": False,
                 "reason": "No trusted Python test configuration was found."}]
    return [{"name": "python-pytest", "command_classification": "pytest", "available": bool(settings.sandbox_image),
             "reason": "Requires the configured prebuilt sandbox image and Docker daemon."}]


def command_for_profile(profile: str) -> tuple[str, list[str]]:
    if profile == "python-pytest":
        return "pytest", ["-q"]
    raise ValueError("Unsupported execution profile.")
