"""Nobitex public market statistics (crypto priced directly in Rial)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from chand.core.http import HttpClient
from chand.core.models import Asset, ProviderQuote
from chand.errors import NetworkError
from chand.providers._util import json_payload, to_decimal
from chand.providers.base import Provider

BASE_URLS = ("https://apiv2.nobitex.ir", "https://api.nobitex.ir")
SYMBOLS: dict[str, tuple[str, Decimal]] = {
    "BTC": ("btc", Decimal(1)),
    "ETH": ("eth", Decimal(1)),
    "USDT": ("usdt", Decimal(1)),
    "USDC": ("usdc", Decimal(1)),
    "XRP": ("xrp", Decimal(1)),
    "BNB": ("bnb", Decimal(1)),
    "SOL": ("sol", Decimal(1)),
    "DOGE": ("doge", Decimal(1)),
    "TRX": ("trx", Decimal(1)),
    "ADA": ("ada", Decimal(1)),
    "TON": ("gram", Decimal(1)),
    "LINK": ("link", Decimal(1)),
    "DOT": ("dot", Decimal(1)),
    "POL": ("pol", Decimal(1)),
    "SHIB": ("1k_shib", Decimal("0.001")),
    "LTC": ("ltc", Decimal(1)),
    "BCH": ("bch", Decimal(1)),
    "XLM": ("xlm", Decimal(1)),
    "AVAX": ("avax", Decimal(1)),
    "ATOM": ("atom", Decimal(1)),
    "NEAR": ("near", Decimal(1)),
    "PEPE": ("1m_pepe", Decimal("0.000001")),
    "UNI": ("uni", Decimal(1)),
    "ETC": ("etc", Decimal(1)),
    "FIL": ("fil", Decimal(1)),
    "APT": ("apt", Decimal(1)),
    "ARB": ("arb", Decimal(1)),
    "SUI": ("sui", Decimal(1)),
    "SEI": ("sei", Decimal(1)),
    "AAVE": ("aave", Decimal(1)),
    "XMR": ("xmr", Decimal(1)),
    "ZEC": ("zec", Decimal(1)),
    "HBAR": ("hbar", Decimal(1)),
    "ALGO": ("algo", Decimal(1)),
    "RENDER": ("render", Decimal(1)),
}


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
        payload = None
        last_error: NetworkError | None = None
        for base_url in BASE_URLS:
            try:
                response = client.get(f"{base_url}/market/stats")
            except NetworkError as exc:
                last_error = exc
                continue
            payload = json_payload(response, self.name)
            break

        if payload is None:
            if last_error is not None:
                raise last_error
            raise self._error("Nobitex did not return a payload.")
        if not isinstance(payload, dict):
            raise self._error("Nobitex returned an unexpected payload.")
        if payload.get("status") not in (None, "ok"):
            detail = payload.get("message") or payload.get("code") or "unknown error"
            raise self._error(f"Nobitex rejected the request: {detail}.")

        stats = payload.get("stats")
        if not isinstance(stats, dict):
            raise self._error("Nobitex response is missing market statistics.")

        results: dict[str, ProviderQuote] = {}
        for symbol, (source, multiplier) in source_symbols.items():
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
                price_irr=price * multiplier,
                change_24h=to_decimal(row.get("dayChange")),
                source=self.name,
                source_url=f"https://nobitex.ir/markets/view/{source}-rls",
            )

        if not results:
            raise self._error("Nobitex did not return a usable price.")
        return results
