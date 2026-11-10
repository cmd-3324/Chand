from __future__ import annotations

from decimal import Decimal

import pytest
import responses

from chand.core.http import HttpClient
from chand.core.registry import resolve
from chand.errors import ProviderError
from chand.providers.bonbast import BonbastProvider
from chand.providers.coingecko import CoinGeckoProvider
from chand.providers.erapi import ErApiProvider
from chand.providers.nerkhara import NerkhAraProvider
from chand.providers.nobitex import NobitexProvider
from chand.providers.tgju import TgjuProvider
from chand.providers.wallex import WallexProvider

BTC = resolve("BTC")
ETH = resolve("ETH")
USD = resolve("USD")
EUR = resolve("EUR")
CNY = resolve("CNY")
JPY = resolve("JPY")
JOD = resolve("JOD")
SHIB = resolve("SHIB")
PEPE = resolve("PEPE")
NOBITEX_URL = "https://apiv2.nobitex.ir/market/stats"
NOBITEX_MIRROR = "https://api.nobitex.ir/market/stats"

NOBITEX_PAYLOAD = {
    "status": "ok",
    "stats": {
        "btc-rls": {"latest": "19500000000", "dayChange": "-1.2"},
        "eth-rls": {"latest": "540000000", "dayChange": "0.5"},
        "usdt-rls": {"latest": "2595000", "dayChange": "0.1"},
        "1k_shib-rls": {"latest": "11261", "dayChange": "-2.0"},
        "1m_pepe-rls": {"latest": "13500000", "dayChange": "1.0"},
        "gram-rls": {"latest": "2882000", "dayChange": "0.4"},
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
    "jpy1": "16250",
    "jpy2": "16150",
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

TGJU_PROFILE_HTML = """
<html><body><h3 class="line clearfix">
  <span class="label">نرخ فعلی:</span>
  <span class="value">
    <span data-col="info.last_trade.PDrCotVal">78,800</span>
    <span data-col="info.last_trade.last_change_percentage">
      <span class="change change-no change-percentage">-</span>
    </span>
  </span>
</h3></body></html>
"""

TGJU_BULK_HTML = """
<html><body><table><tbody>
<tr data-market-nameslug="price_dollar_rl" data-price="2,599,000">
  <th>دلار</th><td class="nf">2,599,000</td>
  <td class="nf"><span class="low">(1.54%) 40,000</span></td>
</tr>
<tr data-market-nameslug="price_eur" data-price="2,906,500">
  <th>یورو</th><td class="nf">2,906,500</td>
  <td class="nf"><span class="high">(1.89%) 54,900</span></td>
</tr>
<tr data-market-nameslug="price_gbp" data-price="3,466,900">
  <th>پوند</th><td class="nf">3,466,900</td>
  <td class="nf"><span class="">(0%) 0</span></td>
</tr>
<tr data-market-nameslug="price_aed" data-price="711,730">
  <th>درهم</th><td class="nf">711,730</td>
  <td class="nf"><span class="">(0%) 0</span></td>
</tr>
<tr data-market-nameslug="price_try" data-price="51,800">
  <th>لیر</th><td class="nf">51,800</td>
  <td class="nf"><span class="">(0%) 0</span></td>
</tr>
<tr data-market-nameslug="price_jpy" data-price="1,640,410">
  <th>ین</th><td class="nf">1,640,410</td>
  <td class="nf"><span class="low">(1.0%) 16,000</span></td>
</tr>
</tbody></table></body></html>
"""

WALLEX_PAYLOAD = {
    "success": True,
    "result": {
        "symbols": {
            "BTCTMN": {"stats": {"lastPrice": "18500001000", "24h_ch": -1.1}},
            "ETHTMN": {"stats": {"lastPrice": "520292003", "24h_ch": 0.7}},
            "TONTMN": {"stats": {"lastPrice": "-", "24h_ch": 0}},
        }
    },
}

NERKHARA_PAYLOAD = {
    "items": [
        {
            "id": "usd",
            "family": "currency",
            "unit": "IRT",
            "price": 258950.0,
            "change_pct": -1.93,
            "page": {"fa": "https://nerkhara.com/dollar/"},
        },
        {
            "id": "jpy",
            "family": "currency",
            "unit": "IRT",
            "price": 1638.7,
            "change_pct": 0.4,
            "page": {"fa": "https://nerkhara.com/yen/"},
        },
    ]
}

ERAPI_PAYLOAD = {
    "result": "success",
    "rates": {
        "USD": 1,
        "EUR": 0.9,
        "GBP": 0.8,
        "AED": 3.6725,
        "TRY": 35.0,
        "JPY": 150.0,
        "JOD": 0.71,
        "BYN": 3.27,
    },
}


@responses.activate
def test_nobitex_parses_rial_prices() -> None:
    responses.add(responses.GET, NOBITEX_URL, json=NOBITEX_PAYLOAD)
    with HttpClient(timeout=1) as client:
        quotes = NobitexProvider().fetch([BTC, ETH, USD, SHIB, PEPE], client)

    assert quotes["BTC"].price_irr == Decimal("19500000000")
    assert quotes["BTC"].change_24h == Decimal("-1.2")
    assert quotes["ETH"].price_irr == Decimal("540000000")
    assert quotes["SHIB"].price_irr == Decimal("11.261")
    assert quotes["PEPE"].price_irr == Decimal("13.5")
    assert quotes["BTC"].source == "Nobitex"
    assert quotes["BTC"].source_url.endswith("/btc-rls")


@responses.activate
@responses.activate
def test_nobitex_falls_back_to_legacy_mirror() -> None:
    responses.add(responses.GET, NOBITEX_URL, body=responses.ConnectionError("no dns"))
    responses.add(responses.GET, NOBITEX_MIRROR, json=NOBITEX_PAYLOAD)
    with HttpClient(timeout=1) as client:
        quotes = NobitexProvider().fetch([BTC], client)

    assert quotes["BTC"].price_irr == Decimal("19500000000")
    assert responses.calls[0].request.url.startswith(NOBITEX_URL)
    assert responses.calls[-1].request.url.startswith(NOBITEX_MIRROR)


@responses.activate
def test_wallex_parses_toman_prices_and_skips_empty_markets() -> None:
    responses.add(responses.GET, "https://api.wallex.ir/v1/markets", json=WALLEX_PAYLOAD)
    with HttpClient(timeout=1) as client:
        quotes = WallexProvider().fetch([BTC, ETH, resolve("TON")], client)

    assert quotes["BTC"].price_irr == Decimal("185000010000")
    assert quotes["ETH"].change_24h == Decimal("0.7")
    assert "TON" not in quotes
    assert quotes["BTC"].source_url.endswith("/BTCTMN")


@responses.activate
def test_nerkhara_converts_toman_and_keeps_source_page() -> None:
    responses.add(responses.GET, "https://nerkhara.com/api/v1/latest.json", json=NERKHARA_PAYLOAD)
    with HttpClient(timeout=1) as client:
        quotes = NerkhAraProvider().fetch([USD, JPY], client)

    assert quotes["USD"].price_irr == Decimal("2589500")
    assert quotes["JPY"].price_irr == Decimal("16387.0")
    assert quotes["USD"].source_url == "https://nerkhara.com/dollar/"


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
        quotes = BonbastProvider().fetch([USD, BTC, JPY], client)

    assert quotes["USD"].price_irr == Decimal("2594000")
    assert quotes["JPY"].price_irr == Decimal("16250")
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
def test_tgju_uses_bulk_page_for_many_fiat_assets() -> None:
    responses.add(
        responses.GET,
        "https://www.tgju.org/currency",
        body=TGJU_BULK_HTML,
        content_type="text/html; charset=utf-8",
    )
    with HttpClient(timeout=1) as client:
        quotes = TgjuProvider().fetch(
            [USD, EUR, resolve("GBP"), resolve("AED"), resolve("TRY"), JPY], client
        )

    assert quotes["USD"].price_irr == Decimal("2599000")
    assert quotes["EUR"].change_24h == Decimal("1.89")
    assert quotes["JPY"].price_irr == Decimal("16404.1")
    assert len(quotes) == 6


@responses.activate
def test_tgju_parses_current_profile_layout_for_jod() -> None:
    responses.add(
        responses.GET,
        "https://www.tgju.org/profile/price_jod",
        body=TGJU_PROFILE_HTML.replace("78,800", "3,674,800"),
        content_type="text/html; charset=utf-8",
    )
    with HttpClient(timeout=1) as client:
        quotes = TgjuProvider().fetch([JOD], client)

    assert quotes["JOD"].price_irr == Decimal("3674800")
    assert quotes["JOD"].change_24h is None


@responses.activate
def test_erapi_returns_usd_cross_rates() -> None:
    responses.add(responses.GET, "https://open.er-api.com/v6/latest/USD", json=ERAPI_PAYLOAD)
    with HttpClient(timeout=1) as client:
        quotes = ErApiProvider().fetch([USD, EUR, JPY, JOD, resolve("BYN")], client)

    assert quotes["USD"].price_usd == Decimal(1)
    assert quotes["EUR"].price_usd == Decimal(1) / Decimal("0.9")
    assert quotes["JPY"].price_usd == Decimal(1) / Decimal("150.0")
    assert quotes["JOD"].price_usd == Decimal(1) / Decimal("0.71")


@responses.activate
def test_non_json_payload_is_provider_error() -> None:
    responses.add(
        responses.GET,
        NOBITEX_URL,
        body="<html>blocked</html>",
        content_type="text/html",
    )
    with HttpClient(timeout=1) as client, pytest.raises(ProviderError, match="non-JSON"):
        NobitexProvider().fetch([BTC], client)


def test_provider_support_matches_wide_registry() -> None:
    assert NobitexProvider().supports(resolve("DOGE"))
    assert not NobitexProvider().supports(EUR)
    assert WallexProvider().supports(SHIB)
    assert NerkhAraProvider().supports(CNY)
    assert not NerkhAraProvider().supports(JOD)
    assert TgjuProvider().supports(JOD)
    assert not TgjuProvider().supports(BTC)
    assert CoinGeckoProvider().supports(ETH)
    assert ErApiProvider().supports(resolve("BYN"))
