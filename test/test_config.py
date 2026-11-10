from __future__ import annotations

import pytest

from chand.core.config import Settings
from chand.core.models import OutputFormat, Unit
from chand.errors import ConfigError
from chand.providers import build_providers


def test_defaults() -> None:
    settings = Settings.from_env({})
    assert settings.unit is Unit.TOMAN
    assert settings.output_format is OutputFormat.TABLE
    assert settings.timeout == 10.0
    assert settings.cache_ttl == 30.0
    assert settings.providers == ()
    assert settings.no_color is False


def test_environment_overrides() -> None:
    settings = Settings.from_env(
        {
            "CHAND_UNIT": "RIAL",
            "CHAND_FORMAT": "JSON",
            "CHAND_TIMEOUT": "4.5",
            "CHAND_CACHE_TTL": "0",
            "CHAND_WATCH": "7",
            "CHAND_PROVIDERS": "tgju, Bonbast ",
            "NO_COLOR": "1",
            "CHAND_COINGECKO_API_KEY": " demo ",
        }
    )
    assert settings.unit is Unit.RIAL
    assert settings.output_format is OutputFormat.JSON
    assert settings.timeout == 4.5
    assert settings.cache_ttl == 0
    assert settings.watch_interval == 7
    assert settings.providers == ("tgju", "bonbast")
    assert settings.no_color is True
    assert settings.coingecko_api_key == "demo"


def test_apply_ignores_none_overrides() -> None:
    base = Settings(unit=Unit.RIAL, no_color=True)
    result = base.apply(unit=None, output_format=OutputFormat.JSON)
    assert result.unit is Unit.RIAL
    assert result.output_format is OutputFormat.JSON
    assert result.no_color is True


@pytest.mark.parametrize(
    ("env", "message"),
    [
        ({"CHAND_UNIT": "dollar"}, "CHAND_UNIT"),
        ({"CHAND_FORMAT": "xml"}, "CHAND_FORMAT"),
        ({"CHAND_TIMEOUT": "soon"}, "CHAND_TIMEOUT"),
        ({"CHAND_TIMEOUT": "0.1"}, "at least"),
        ({"CHAND_WATCH": "0"}, "at least"),
        ({"CHAND_CACHE_TTL": "-1"}, "at least"),
    ],
)
def test_invalid_environment_values(env: dict[str, str], message: str) -> None:
    with pytest.raises(ConfigError, match=message):
        Settings.from_env(env)


def test_provider_factory_respects_explicit_order() -> None:
    providers = build_providers(Settings(providers=("bonbast", "tgju")))
    assert [provider.name for provider in providers] == ["Bonbast", "TGJU"]


def test_provider_factory_rejects_unknown_names() -> None:
    with pytest.raises(ConfigError, match="Unknown provider"):
        build_providers(Settings(providers=("nope",)))
