"""Nobitex public market statistics (crypto priced directly in Rial)."""

from __future__ import annotations

from collections.abc import Sequence

from chand.core.http import HttpClient
from chand.core.models import Asset, ProviderQuote
from chand.providers._util import json_payload, to_decimal
from chand.providers.base import Provider

API_URL = "https://api.nobitex.ir/market/stats"
SYMBOLS = {"BTC": "btc", "ETH": "eth", "USDT": "usdt"}


class NobitexProvider(Provider):
    name = "Nobitex"
    priority = 10
    homepage = "https://nobitex.ir/"

    def supports(self, asset: Asset) -> bool:
        return asset.symbol in SYMBOLS

    def fetch(
        self,
        assets: Sequence[Asset],
        client: HttpClient,
    ) -> dict[str, ProviderQuote]:
        source_symbols = {
            asset.symbol: SYMBOLS[asset.symbol] for asset in assets if asset.symbol in SYMBOLS
        }
        response = client.get(
            API_URL,
            params={
                "srcCurrency": ",".join(source_symbols.values()),
                "dstCurrency": "rls",
            },
        )
        payload = json_payload(response, self.name)
        if not isinstance(payload, dict):
            raise self._error("Nobitex returned an unexpected payload.")
        if payload.get("status") not in (None, "ok"):
            detail = payload.get("message") or payload.get("code") or "unknown error"
            raise self._error(f"Nobitex rejected the request: {detail}.")

        stats = payload.get("stats")
        if not isinstance(stats, dict):
            raise self._error("Nobitex response is missing market statistics.")

        results: dict[str, ProviderQuote] = {}
        for symbol, source in source_symbols.items():
            row = stats.get(f"{source}-rls")
            if not isinstance(row, dict):
                row = stats.get(f"{source}-IRT")
            if not isinstance(row, dict):
                continue
            price = None
            for key in ("latest", "lastTradePrice", "bestSell", "bestBuy"):
                price = to_decimal(row.get(key))
                if price is not None and price > 0:
                    break
            if price is None or price <= 0:
                continue
            results[symbol] = ProviderQuote(
                symbol=symbol,
                price_irr=price,
                change_24h=to_decimal(row.get("dayChange")),
                source=self.name,
                source_url=f"https://nobitex.ir/markets/view/{source}-rls",
            )

        if not results:
            raise self._error("Nobitex did not return a usable price.")
        return results
