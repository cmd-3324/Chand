from __future__ import annotations

import pytest

_ENV_VARS = (
    "CHAND_UNIT",
    "CHAND_FORMAT",
    "CHAND_TIMEOUT",
    "CHAND_WATCH",
    "CHAND_CACHE_TTL",
    "CHAND_PROVIDERS",
    "CHAND_COINGECKO_API_KEY",
    "CHAND_NO_COLOR",
    "CHAND_CACHE_DIR",
)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    for name in _ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("CHAND_CACHE_TTL", "0")
    monkeypatch.setenv("CHAND_CACHE_DIR", str(tmp_path / "chand-cache"))
    monkeypatch.setenv("COLUMNS", "120")
