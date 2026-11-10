"""Wallex public markets (crypto priced directly in Toman)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from chand.core.http import HttpClient
from chand.core.models import Asset, ProviderQuote
from chand.providers._util import json_payload, to_decimal
from chand.providers.base import Provider

API_URL = "https://api.wallex.ir/v1/markets"
TOMAN = Decimal("10")
SYMBOLS = {
    "BTC",
    "ETH",
    "USDT",
    "USDC",
    "XRP",
    "BNB",
    "SOL",
    "DOGE",
    "TRX",
    "ADA",
    "TON",
    "LINK",
    "DOT",
    "POL",
    "SHIB",
    "LTC",
    "BCH",
    "XLM",
    "AVAX",
    "ATOM",
    "NEAR",
    "PEPE",
    "UNI",
    "ETC",
    "FIL",
    "APT",
    "ARB",
    "SUI",
    "SEI",
    "AAVE",
    "XMR",
    "ZEC",
    "HBAR",
    "ALGO",
    "RENDER",
}


class WallexProvider(Provider):
    name = "Wallex"
    priority = 12
    homepage = "https://wallex.ir/"

    def supports(self, asset: Asset) -> bool:
        return asset.symbol in SYMBOLS

    def fetch(
        self,
        assets: Sequence[Asset],
        client: HttpClient,
    ) -> dict[str, ProviderQuote]:
        wanted = {asset.symbol for asset in assets if asset.symbol in SYMBOLS}
        response = client.get(API_URL)
        payload = json_payload(response, self.name)
        if not isinstance(payload, dict) or payload.get("success") is False:
            raise self._error("Wallex returned an unsuccessful payload.")

        result = payload.get("result")
        symbols = result.get("symbols") if isinstance(result, dict) else None
        if not isinstance(symbols, dict):
            raise self._error("Wallex response is missing market data.")

        results: dict[str, ProviderQuote] = {}
        for symbol in wanted:
            market = f"{symbol}TMN"
            row = symbols.get(market)
            stats = row.get("stats") if isinstance(row, dict) else None
            if not isinstance(stats, dict):
                continue
            price = to_decimal(stats.get("lastPrice"))
            if price is None or price <= 0:
                price = to_decimal(stats.get("bidPrice"))
            if price is None or price <= 0:
                continue
            results[symbol] = ProviderQuote(
                symbol=symbol,
                price_irr=price * TOMAN,
                change_24h=to_decimal(stats.get("24h_ch")),
                source=self.name,
                source_url=f"https://wallex.ir/app/trade/{market}",
            )

        if not results:
            raise self._error("Wallex did not return a usable price.")
        return results
