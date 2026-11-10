from __future__ import annotations

from decimal import Decimal

import pytest
import responses

from chand.core.http import HttpClient
from chand.core.models import Asset
from chand.core.registry import resolve
from chand.errors import ProviderError
from chand.providers.bonbast import BonbastProvider
from chand.providers.coingecko import CoinGeckoProvider
from chand.providers.erapi import ErApiProvider
from chand.providers.nobitex import NobitexProvider
from chand.providers.tgju import TgjuProvider

BTC = resolve("BTC")
ETH = resolve("ETH")
USD = resolve("USD")
EUR = resolve("EUR")

NOBITEX_PAYLOAD = {
    "status": "ok",
    "stats": {
        "btc-rls": {"latest": "19500000000", "dayChange": "-1.2"},
        "eth-rls": {"latest": "540000000", "dayChange": "0.5"},
        "usdt-rls": {"latest": "2595000", "dayChange": "0.1"},
    },
}

COINGECKO_PAYLOAD = {
    "bitcoin": {"usd": 74500.5, "usd_24h_change": -0.2},
    "ethereum": {"usd": 2080.25, "usd_24h_change": 1.4},
    "tether": {"usd": 0.999, "usd_24h_change": -0.01},
}

BONBAST_HTML = """
<html><body><script>
$.post('/json', {param: "TOKEN,ABC,2026-11-10-15-09-35"}, function(json) {});
</script></body></html>
"""

BONBAST_PAYLOAD = {
    "usd1": "259400",
    "usd2": "259200",
    "eur1": "290900",
    "bitcoin": "74497.4",
}

TGJU_HTML = """
<html><body>
<li id="l-price_dollar_rl" style="" class=" low" onclick="x">
  <strong>USD</strong>
  <span class="info-value">
    <span class="info-price">2,629,000</span>
    <span class="info-change">(0.38%)</span>
  </span>
</li>
</body></html>
"""

ERAPI_PAYLOAD = {
    "result": "success",
    "rates": {"USD": 1, "EUR": 0.9, "GBP": 0.8, "AED": 3.6725, "TRY": 35.0},
}


@responses.activate
def test_nobitex_parses_rial_prices() -> None:
    responses.add(responses.GET, "https://api.nobitex.ir/market/stats", json=NOBITEX_PAYLOAD)
    with HttpClient(timeout=1) as client:
        quotes = NobitexProvider().fetch([BTC, ETH, USD], client)

    assert quotes["BTC"].price_irr == Decimal("19500000000")
    assert quotes["BTC"].change_24h == Decimal("-1.2")
    assert quotes["ETH"].price_irr == Decimal("540000000")
    assert quotes["BTC"].source == "Nobitex"
    assert quotes["BTC"].source_url.endswith("/btc-rls")


@responses.activate
def test_coingecko_parses_usd_prices_and_sends_api_key() -> None:
    responses.add(
        responses.GET, "https://api.coingecko.com/api/v3/simple/price", json=COINGECKO_PAYLOAD
    )
    with HttpClient(timeout=1) as client:
        quotes = CoinGeckoProvider(api_key="secret").fetch([BTC, ETH], client)

    assert quotes["BTC"].price_usd == Decimal("74500.5")
    assert quotes["BTC"].change_24h == Decimal("-0.2")
    assert quotes["ETH"].price_usd == Decimal("2080.25")
    assert responses.calls[0].request.headers["x-cg-demo-api-key"] == "secret"


@responses.activate
def test_bonbast_uses_token_and_converts_toman_to_rial() -> None:
    responses.add(
        responses.GET,
        "https://bonbast.com/",
        body=BONBAST_HTML,
        content_type="text/html; charset=utf-8",
    )
    responses.add(responses.POST, "https://bonbast.com/json", json=BONBAST_PAYLOAD)
    with HttpClient(timeout=1) as client:
        quotes = BonbastProvider().fetch([USD, BTC], client)

    assert quotes["USD"].price_irr == Decimal("2594000")
    assert quotes["BTC"].price_usd == Decimal("74497.4")
    assert quotes["USD"].source_url.endswith("/graph/usd")
    assert responses.calls[1].request.headers["Referer"] == "https://bonbast.com/"


@responses.activate
def test_bonbast_reports_missing_token() -> None:
    responses.add(
        responses.GET, "https://bonbast.com/", body="<html>changed</html>", content_type="text/html"
    )
    with HttpClient(timeout=1) as client, pytest.raises(ProviderError, match="token"):
        BonbastProvider().fetch([USD], client)


@responses.activate
def test_tgju_isolates_a_failing_profile() -> None:
    responses.add(responses.GET, "https://www.tgju.org/profile/price_dollar_rl", status=404)
    responses.add(
        responses.GET,
        "https://www.tgju.org/profile/price_eur",
        body=TGJU_HTML.replace("price_dollar_rl", "price_eur").replace("2,629,000", "2,950,200"),
        content_type="text/html; charset=utf-8",
    )
    with HttpClient(timeout=1) as client:
        quotes = TgjuProvider().fetch([USD, EUR], client)

    assert list(quotes) == ["EUR"]
    assert quotes["EUR"].price_irr == Decimal("2950200")


@responses.activate
def test_tgju_parses_profile_and_negative_change() -> None:
    responses.add(
        responses.GET,
        "https://www.tgju.org/profile/price_dollar_rl",
        body=TGJU_HTML,
        content_type="text/html; charset=utf-8",
    )
    with HttpClient(timeout=1) as client:
        quotes = TgjuProvider().fetch([USD], client)

    assert quotes["USD"].price_irr == Decimal("2629000")
    assert quotes["USD"].change_24h == Decimal("-0.38")
    assert quotes["USD"].source_url.endswith("price_dollar_rl")


@responses.activate
def test_erapi_returns_usd_cross_rates() -> None:
    responses.add(responses.GET, "https://open.er-api.com/v6/latest/USD", json=ERAPI_PAYLOAD)
    with HttpClient(timeout=1) as client:
        quotes = ErApiProvider().fetch([USD, EUR], client)

    assert quotes["USD"].price_usd == Decimal(1)
    assert quotes["EUR"].price_usd == Decimal(1) / Decimal("0.9")


@responses.activate
def test_non_json_payload_is_provider_error() -> None:
    responses.add(
        responses.GET,
        "https://api.nobitex.ir/market/stats",
        body="<html>blocked</html>",
        content_type="text/html",
    )
    with HttpClient(timeout=1) as client, pytest.raises(ProviderError, match="non-JSON"):
        NobitexProvider().fetch([BTC], client)


def test_supports_rejects_unknown_assets() -> None:
    assert NobitexProvider().supports(BTC)
    assert not NobitexProvider().supports(Asset("DOGE", "Dogecoin", resolve("BTC").kind))
    assert TgjuProvider().supports(USD)
    assert not TgjuProvider().supports(BTC)
    assert CoinGeckoProvider().supports(ETH)
