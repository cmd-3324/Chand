from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from chand.core.cache import PriceCache
from chand.core.models import ProviderQuote


def _quote(symbol: str = "BTC", price: str = "19500000000") -> ProviderQuote:
    return ProviderQuote(
        symbol=symbol,
        price_irr=Decimal(price),
        change_24h=Decimal("-1.5"),
        source="test",
        source_url="https://example.test/btc",
        fetched_at=datetime(2026, 11, 10, tzinfo=UTC),
    )


def test_cache_round_trip_and_persistence(tmp_path, monkeypatch) -> None:
    clock = {"now": 1000.0}
    monkeypatch.setattr("chand.core.cache.time.time", lambda: clock["now"])
    path = tmp_path / "quotes.json"

    cache = PriceCache(ttl=30, path=path)
    cache.set("p", "BTC", _quote())
    assert cache.get("p", "BTC") == _quote()
    cache.flush()
    assert path.exists()

    clock["now"] = 1010.0
    reloaded = PriceCache(ttl=30, path=path)
    assert reloaded.get("p", "BTC") == _quote()


def test_cache_expiry(tmp_path, monkeypatch) -> None:
    clock = {"now": 1000.0}
    monkeypatch.setattr("chand.core.cache.time.time", lambda: clock["now"])
    cache = PriceCache(ttl=5, path=tmp_path / "quotes.json")
    cache.set("p", "BTC", _quote())

    clock["now"] = 1004.9
    assert cache.get("p", "BTC") is not None
    clock["now"] = 1005.1
    assert cache.get("p", "BTC") is None


def test_zero_ttl_disables_cache(tmp_path) -> None:
    cache = PriceCache(ttl=0, path=tmp_path / "quotes.json")
    cache.set("p", "BTC", _quote())
    assert cache.get("p", "BTC") is None
    cache.flush()
    assert not cache.path.exists()


def test_corrupt_cache_is_ignored(tmp_path) -> None:
    path = tmp_path / "quotes.json"
    path.write_text("{not json", encoding="utf-8")
    cache = PriceCache(ttl=30, path=path)
    assert cache.get("p", "BTC") is None


def test_bad_entry_is_dropped(tmp_path) -> None:
    path = tmp_path / "quotes.json"
    path.write_text(
        '{"version":1,"entries":{"p:BTC":{"expires_at":9999999999,"quote":{}}}}',
        encoding="utf-8",
    )
    cache = PriceCache(ttl=30, path=path)
    assert cache.get("p", "BTC") is None


def test_clear_removes_file(tmp_path) -> None:
    path = tmp_path / "quotes.json"
    cache = PriceCache(ttl=30, path=path)
    cache.set("p", "BTC", _quote())
    cache.flush()
    assert path.exists()
    cache.clear()
    assert not path.exists()
    assert cache.get("p", "BTC") is None


def test_keys_are_provider_scoped(tmp_path) -> None:
    cache = PriceCache(ttl=30, path=tmp_path / "quotes.json")
    cache.set("nobitex", "BTC", _quote())
    assert cache.get("nobitex", "BTC") is not None
    assert cache.get("tgju", "BTC") is None
