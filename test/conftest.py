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
)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("CHAND_CACHE_TTL", "0")
    monkeypatch.setenv("COLUMNS", "120")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "localappdata"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "xdg-cache"))
    for name in _ENV_VARS:
        if name != "CHAND_CACHE_TTL":
            monkeypatch.delenv(name, raising=False)
