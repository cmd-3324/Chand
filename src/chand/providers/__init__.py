"""Provider registry and factory."""

from __future__ import annotations

from chand.core.config import Settings
from chand.errors import ConfigError
from chand.providers.base import Provider
from chand.providers.bonbast import BonbastProvider
from chand.providers.coingecko import CoinGeckoProvider
from chand.providers.erapi import ErApiProvider
from chand.providers.nerkhara import NerkhAraProvider
from chand.providers.nobitex import NobitexProvider
from chand.providers.tgju import TgjuProvider
from chand.providers.wallex import WallexProvider

__all__ = [
    "Provider",
    "available_providers",
    "build_providers",
]

_FACTORIES = {
    "nobitex": NobitexProvider,
    "wallex": WallexProvider,
    "nerkhara": NerkhAraProvider,
    "tgju": TgjuProvider,
    "bonbast": BonbastProvider,
    "coingecko": CoinGeckoProvider,
    "erapi": ErApiProvider,
}

_DEFAULT_ORDER = ("nobitex", "wallex", "nerkhara", "tgju", "bonbast", "coingecko", "erapi")


def available_providers() -> tuple[str, ...]:
    return _DEFAULT_ORDER


def build_providers(settings: Settings) -> list[Provider]:
    requested = settings.providers or _DEFAULT_ORDER
    unknown = [name for name in requested if name not in _FACTORIES]
    if unknown:
        allowed = ", ".join(_DEFAULT_ORDER)
        raise ConfigError(f"Unknown provider(s): {', '.join(unknown)}. Allowed values: {allowed}.")

    providers: list[Provider] = []
    seen: set[str] = set()
    for name in requested:
        if name in seen:
            continue
        seen.add(name)
        if name == "coingecko":
            providers.append(CoinGeckoProvider(settings.coingecko_api_key))
        else:
            providers.append(_FACTORIES[name]())

    if not settings.providers:
        providers.sort(key=lambda provider: provider.priority)
    return providers
