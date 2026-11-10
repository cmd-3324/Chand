from __future__ import annotations

import pytest

from chand.core.models import AssetKind
from chand.core.registry import (
    ASSETS,
    DEFAULT_QUICK,
    filtered_assets,
    resolve,
    select_assets,
)
from chand.errors import AssetNotFoundError, UsageError


def test_resolve_is_case_insensitive_and_uses_aliases() -> None:
    assert resolve(" btc ").symbol == "BTC"
    assert resolve("xbt").symbol == "BTC"
    assert resolve("Dollar").symbol == "USD"
    assert resolve("us$").symbol == "USD"


def test_resolve_unknown_asset_suggests_close_match() -> None:
    with pytest.raises(AssetNotFoundError) as info:
        resolve("BTCC")
    assert "Did you mean BTC" in info.value.message
    assert info.value.exit_code == 2


def test_resolve_empty_symbol_is_usage_error() -> None:
    with pytest.raises(UsageError):
        resolve("   ")


def test_select_assets_preserves_order_and_deduplicates() -> None:
    selected = select_assets(["BTC", "usd", "btc", "ETH"])
    assert [asset.symbol for asset in selected] == ["BTC", "USD", "ETH"]


def test_select_assets_rejects_symbols_with_all() -> None:
    with pytest.raises(UsageError):
        select_assets(["BTC"], all_assets=True)


def test_select_assets_rejects_mixed_selectors() -> None:
    with pytest.raises(UsageError):
        select_assets(["BTC"], currencies="USD")


def test_select_assets_by_kind_filters() -> None:
    fiat = select_assets(currencies="USD,EUR")
    assert [asset.symbol for asset in fiat] == ["USD", "EUR"]
    crypto = select_assets(cryptos=["BTC", "ETH"])
    assert [asset.symbol for asset in crypto] == ["BTC", "ETH"]


def test_select_assets_rejects_wrong_kind_filter() -> None:
    with pytest.raises(UsageError, match="cryptocurrency"):
        select_assets(currencies="BTC")
    with pytest.raises(UsageError, match="currency"):
        select_assets(cryptos="USD")


def test_select_assets_requires_a_selection() -> None:
    with pytest.raises(UsageError, match="No assets"):
        select_assets()


def test_registry_covers_broad_fiat_and_crypto_markets() -> None:
    fiat = {asset.symbol for asset in ASSETS if asset.kind is AssetKind.FIAT}
    crypto = {asset.symbol for asset in ASSETS if asset.kind is AssetKind.CRYPTO}
    assert len(fiat) >= 49
    assert len(crypto) >= 35
    assert {"JOD", "TWD", "BYN", "KZT", "UAH"} <= fiat
    assert {"TON", "SHIB", "PEPE", "RENDER", "POL"} <= crypto


def test_default_quick_assets_are_registered() -> None:
    symbols = {asset.symbol for asset in ASSETS}
    assert set(DEFAULT_QUICK) <= symbols
    assert len(DEFAULT_QUICK) >= 12


def test_filtered_assets_without_filters_returns_registry_order() -> None:
    assert filtered_assets() == list(ASSETS)


def test_every_alias_is_unique_and_normalized() -> None:
    seen: set[str] = set()
    for asset in ASSETS:
        assert asset.symbol not in seen
        seen.add(asset.symbol)
        for alias in asset.aliases:
            assert alias == alias.upper()
            assert resolve(alias) is asset
    assert all(asset.kind in {AssetKind.CRYPTO, AssetKind.FIAT} for asset in ASSETS)
