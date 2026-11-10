"""CoinGecko spot prices in USD (wide coverage, optional demo API key)."""

from __future__ import annotations

from collections.abc import Sequence

from chand.core.http import HttpClient
from chand.core.models import Asset, ProviderQuote
from chand.providers._util import json_payload, to_decimal
from chand.providers.base import Provider

API_URL = "https://api.coingecko.com/api/v3/simple/price"
COINS = {"BTC": "bitcoin", "ETH": "ethereum", "USDT": "tether"}


class CoinGeckoProvider(Provider):
    name = "CoinGecko"
    priority = 15
    homepage = "https://www.coingecko.com/"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key

    def supports(self, asset: Asset) -> bool:
        return asset.symbol in COINS

    def fetch(
        self,
        assets: Sequence[Asset],
        client: HttpClient,
    ) -> dict[str, ProviderQuote]:
        ids = {asset.symbol: COINS[asset.symbol] for asset in assets if asset.symbol in COINS}
        headers = {"x-cg-demo-api-key": self.api_key} if self.api_key else None
        response = client.get(
            API_URL,
            params={
                "ids": ",".join(ids.values()),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
            },
            headers=headers,
        )
        payload = json_payload(response, self.name)
        if not isinstance(payload, dict):
            raise self._error("CoinGecko returned an unexpected payload.")
        if payload.get("status", {}).get("error_message"):
            raise self._error(str(payload["status"]["error_message"]))

        results: dict[str, ProviderQuote] = {}
        for symbol, coin_id in ids.items():
            row = payload.get(coin_id)
            if not isinstance(row, dict):
                continue
            price = to_decimal(row.get("usd"))
            if price is None or price <= 0:
                continue
            results[symbol] = ProviderQuote(
                symbol=symbol,
                price_usd=price,
                change_24h=to_decimal(row.get("usd_24h_change")),
                source=self.name,
                source_url=f"https://www.coingecko.com/en/coins/{coin_id}",
            )

        if not results:
            raise self._error(
                "CoinGecko did not return a usable price.",
                hint="The public API may be rate-limited; set CHAND_COINGECKO_API_KEY.",
            )
        return results
