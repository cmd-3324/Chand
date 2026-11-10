from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from chand.core.cache import PriceCache
from chand.core.http import HttpClient
from chand.core.models import Asset, ProviderQuote, Unit
from chand.core.registry import resolve
from chand.core.service import PricingService
from chand.errors import ProviderError
from chand.providers.base import Provider

BTC = resolve("BTC")
ETH = resolve("ETH")
USD = resolve("USD")
FIXED_TIME = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)


class FakeHttp:
    def close(self) -> None:
        pass


class FakeProvider(Provider):
    homepage = "https://example.test"

    def __init__(
        self,
        name: str,
        priority: int,
        supported: set[str],
        quotes: dict[str, ProviderQuote] | None = None,
        *,
        fail: bool = False,
    ) -> None:
        self.name = name
        self.priority = priority
        self.supported = supported
        self.quotes = quotes or {}
        self.fail = fail
        self.calls = 0

    def supports(self, asset: Asset) -> bool:
        return asset.symbol in self.supported

    def fetch(
        self,
        assets: Sequence[Asset],
        client: HttpClient,
    ) -> dict[str, ProviderQuote]:
        self.calls += 1
        if self.fail:
            raise ProviderError(f"{self.name} is down", provider=self.name)
        return {
            asset.symbol: self.quotes[asset.symbol]
            for asset in assets
            if asset.symbol in self.quotes
        }


def quote(
    symbol: str, *, irr: str | None = None, usd: str | None = None, change: str | None = None
):
    return ProviderQuote(
        symbol=symbol,
        price_irr=Decimal(irr) if irr is not None else None,
        price_usd=Decimal(usd) if usd is not None else None,
        change_24h=Decimal(change) if change is not None else None,
        source="fake",
        source_url="https://example.test/source",
        fetched_at=FIXED_TIME,
    )


def make_service(*providers: Provider, ttl: float = 0) -> PricingService:
    return PricingService(list(providers), PriceCache(ttl=ttl), http=FakeHttp())


def test_quiet_fiat_provider_and_crypto_provider() -> None:
    fiat = FakeProvider("fiat", 10, {"USD"}, {"USD": quote("USD", irr="2600000")})
    crypto = FakeProvider("crypto", 20, {"BTC"}, {"BTC": quote("BTC", irr="19500000000")})
    result = make_service(fiat, crypto).fetch([BTC, USD])

    assert [item.asset.symbol for item in result.quotes] == ["BTC", "USD"]
    assert result.usd_irr == Decimal("2600000")
    assert result.quotes[0].price_usd == Decimal("19500000000") / Decimal("2600000")
    assert result.quotes[1].price_usd == Decimal(1)
    assert result.quotes[0].price(Unit.TOMAN) == Decimal("1950000000")


def test_usd_only_provider_converts_crypto_price_to_rial() -> None:
    fiat = FakeProvider("fiat", 10, {"USD"}, {"USD": quote("USD", irr="2600000")})
    crypto = FakeProvider("crypto", 20, {"BTC"}, {"BTC": quote("BTC", usd="74500")})
    result = make_service(fiat, crypto).fetch([BTC])

    assert result.usd_irr == Decimal("2600000")
    assert result.quotes[0].price_irr == Decimal("74500") * Decimal("2600000")
    assert result.quotes[0].price_usd == Decimal("74500")


def test_provider_fallback_on_failure() -> None:
    broken = FakeProvider("broken", 10, {"BTC"}, fail=True)
    good = FakeProvider("good", 20, {"BTC"}, {"BTC": quote("BTC", irr="100")})
    result = make_service(broken, good).fetch([BTC])

    assert result.quotes[0].price_irr == Decimal("100")
    assert result.quotes[0].source == "fake"
    assert broken.calls == 1
    assert good.calls == 1


def test_partial_failure_keeps_successful_quotes() -> None:
    fiat = FakeProvider("fiat", 10, {"USD"}, {"USD": quote("USD", irr="2600000")})
    crypto = FakeProvider("crypto", 20, {"BTC"}, {"BTC": quote("BTC", irr="19500000000")})
    result = make_service(fiat, crypto).fetch([BTC, ETH])

    assert [item.asset.symbol for item in result.quotes] == ["BTC"]
    assert [failure.symbol for failure in result.failures] == ["ETH"]


def test_missing_usd_rate_blocks_usd_only_quotes() -> None:
    broken_fiat = FakeProvider("fiat", 10, {"USD"}, fail=True)
    crypto = FakeProvider("crypto", 20, {"BTC"}, {"BTC": quote("BTC", usd="74500")})
    result = make_service(broken_fiat, crypto).fetch([BTC])

    assert result.quotes == []
    assert "USD/IRR" in result.failures[0].message


def test_cache_avoids_repeated_provider_calls(tmp_path) -> None:
    fiat = FakeProvider("fiat", 10, {"USD"}, {"USD": quote("USD", irr="2600000")})
    crypto = FakeProvider("crypto", 20, {"BTC"}, {"BTC": quote("BTC", irr="19500000000")})
    path = tmp_path / "quotes.json"

    first = PricingService([fiat, crypto], PriceCache(ttl=60, path=path), http=FakeHttp())
    first.fetch([BTC, USD])
    calls_after_first = (fiat.calls, crypto.calls)

    second = PricingService([fiat, crypto], PriceCache(ttl=60, path=path), http=FakeHttp())
    second.fetch([BTC, USD])

    assert (fiat.calls, crypto.calls) == calls_after_first


def test_empty_selection_returns_empty_result() -> None:
    result = make_service().fetch([])
    assert result.quotes == []
    assert result.failures == []
