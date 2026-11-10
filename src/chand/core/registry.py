"""Static asset registry, alias resolution, and selector parsing."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from difflib import get_close_matches

from chand.core.models import Asset, AssetKind
from chand.errors import AssetNotFoundError, UsageError

ASSETS: tuple[Asset, ...] = (
    Asset("BTC", "Bitcoin", AssetKind.CRYPTO, ("XBT", "BITCOIN")),
    Asset("ETH", "Ethereum", AssetKind.CRYPTO, ("ETHER", "ETHEREUM")),
    Asset("USDT", "Tether", AssetKind.CRYPTO, ("TETHER", "USD TETHER")),
    Asset("USD", "US Dollar", AssetKind.FIAT, ("DOLLAR", "US$", "USD$")),
    Asset("EUR", "Euro", AssetKind.FIAT, ("EURO",)),
    Asset("GBP", "British Pound", AssetKind.FIAT, ("POUND", "STERLING")),
    Asset("AED", "UAE Dirham", AssetKind.FIAT, ("DIRHAM",)),
    Asset("TRY", "Turkish Lira", AssetKind.FIAT, ("LIRA",)),
)

DEFAULT_QUICK: tuple[str, ...] = ("BTC", "ETH", "USDT", "USD")

_BY_SYMBOL: dict[str, Asset] = {asset.symbol: asset for asset in ASSETS}
_ALIASES: dict[str, Asset] = {asset.symbol: asset for asset in ASSETS}
for _asset in ASSETS:
    for _alias in _asset.aliases:
        _ALIASES[_alias.upper()] = _asset


def normalize(value: str) -> str:
    return " ".join(value.strip().upper().split())


def resolve(symbol: str) -> Asset:
    """Resolve a user-supplied symbol or alias, with typo suggestions."""

    key = normalize(symbol)
    if not key:
        raise UsageError("Asset symbol cannot be empty.")
    asset = _ALIASES.get(key)
    if asset is not None:
        return asset

    candidates = get_close_matches(key, list(_ALIASES), n=3, cutoff=0.55)
    suggestion = f" Did you mean {', '.join(candidates)}?" if candidates else ""
    raise AssetNotFoundError(
        f"Unknown asset {symbol!r}.{suggestion}",
        hint="Run `chand list` to see supported assets.",
    )


def resolve_all(symbols: Iterable[str]) -> list[Asset]:
    """Resolve symbols in order, de-duplicating while preserving order."""

    seen: set[str] = set()
    result: list[Asset] = []
    for symbol in symbols:
        asset = resolve(symbol)
        if asset.symbol not in seen:
            seen.add(asset.symbol)
            result.append(asset)
    return result


def _split_filter(values: Sequence[str] | str | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = (values,)
    parts: list[str] = []
    for value in values:
        parts.extend(chunk.strip() for chunk in value.split(",") if chunk.strip())
    return parts


def filtered_assets(
    *,
    currencies: Sequence[str] | str | None = None,
    cryptos: Sequence[str] | str | None = None,
) -> list[Asset]:
    """Return assets matching the kind-specific selector flags."""

    selected: set[str] = set()
    if currencies:
        for symbol in _split_filter(currencies):
            asset = resolve(symbol)
            if asset.kind is not AssetKind.FIAT:
                raise UsageError(
                    f"{asset.symbol} is a cryptocurrency; use `--crypto {asset.symbol}` instead."
                )
            selected.add(asset.symbol)
    if cryptos:
        for symbol in _split_filter(cryptos):
            asset = resolve(symbol)
            if asset.kind is not AssetKind.CRYPTO:
                raise UsageError(
                    f"{asset.symbol} is a currency; use `--currency {asset.symbol}` instead."
                )
            selected.add(asset.symbol)

    if not currencies and not cryptos:
        return list(ASSETS)
    return [asset for asset in ASSETS if asset.symbol in selected]


def select_assets(
    symbols: Sequence[str] | None = None,
    *,
    all_assets: bool = False,
    currencies: Sequence[str] | str | None = None,
    cryptos: Sequence[str] | str | None = None,
) -> list[Asset]:
    """Combine positional symbols and selector flags into a final asset list."""

    explicit = list(symbols or ())
    has_filters = bool(_split_filter(currencies) or _split_filter(cryptos))

    if all_assets and explicit:
        raise UsageError("Pass either asset symbols or `--all`, not both.")
    if explicit and has_filters:
        raise UsageError("Pass either asset symbols or `--currency`/`--crypto`, not both.")

    if explicit:
        return resolve_all(explicit)
    if has_filters:
        return filtered_assets(currencies=currencies, cryptos=cryptos)
    if all_assets:
        return list(ASSETS)
    raise UsageError(
        "No assets selected.",
        hint="Pass symbols (for example `chand price BTC USD`) or use `--all`.",
    )
