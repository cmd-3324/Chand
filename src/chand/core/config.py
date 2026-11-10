"""Runtime settings loaded from environment variables and CLI overrides."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, replace
from typing import Any

from chand.core.models import OutputFormat, Unit
from chand.errors import ConfigError

DEFAULT_TIMEOUT = 10.0
DEFAULT_CACHE_TTL = 30.0
DEFAULT_WATCH_INTERVAL = 5.0


@dataclass(frozen=True, slots=True)
class Settings:
    unit: Unit = Unit.TOMAN
    output_format: OutputFormat = OutputFormat.TABLE
    timeout: float = DEFAULT_TIMEOUT
    cache_ttl: float = DEFAULT_CACHE_TTL
    watch_interval: float = DEFAULT_WATCH_INTERVAL
    no_color: bool = False
    providers: tuple[str, ...] = ()
    coingecko_api_key: str | None = None

    def apply(self, **overrides: Any) -> Settings:
        """Return a copy with non-None overrides applied."""

        clean = {key: value for key, value in overrides.items() if value is not None}
        return replace(self, **clean)

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        source = os.environ if env is None else env

        unit = _enum(Unit, source.get("CHAND_UNIT"), "CHAND_UNIT")
        output_format = _enum(OutputFormat, source.get("CHAND_FORMAT"), "CHAND_FORMAT")
        timeout = _float(source.get("CHAND_TIMEOUT"), "CHAND_TIMEOUT", minimum=0.5)
        cache_ttl = _float(source.get("CHAND_CACHE_TTL"), "CHAND_CACHE_TTL", minimum=0.0)
        watch = _float(source.get("CHAND_WATCH"), "CHAND_WATCH", minimum=1.0)
        providers = _providers(source.get("CHAND_PROVIDERS"))
        no_color = "NO_COLOR" in source or _truthy(source.get("CHAND_NO_COLOR"))
        api_key = (source.get("CHAND_COINGECKO_API_KEY") or "").strip() or None

        return cls(
            unit=unit or Unit.TOMAN,
            output_format=output_format or OutputFormat.TABLE,
            timeout=timeout if timeout is not None else DEFAULT_TIMEOUT,
            cache_ttl=cache_ttl if cache_ttl is not None else DEFAULT_CACHE_TTL,
            watch_interval=watch if watch is not None else DEFAULT_WATCH_INTERVAL,
            no_color=no_color,
            providers=providers,
            coingecko_api_key=api_key,
        )


def _enum(enum_type: type[Unit] | type[OutputFormat], raw: str | None, name: str):
    if raw is None or not raw.strip():
        return None
    value = raw.strip().lower()
    try:
        return enum_type(value)
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_type)
        raise ConfigError(f"Invalid {name}={raw!r}. Allowed values: {allowed}.") from exc


def _float(raw: str | None, name: str, *, minimum: float) -> float | None:
    if raw is None or not raw.strip():
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number, got {raw!r}.") from exc
    if value < minimum:
        raise ConfigError(f"{name} must be at least {minimum}, got {value}.")
    return value


def _providers(raw: str | None) -> tuple[str, ...]:
    if raw is None or not raw.strip():
        return ()
    names = tuple(part.strip().lower() for part in raw.split(",") if part.strip())
    return names


def _truthy(raw: str | None) -> bool:
    if raw is None:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}
