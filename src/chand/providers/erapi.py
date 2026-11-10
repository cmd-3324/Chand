"""USD cross-rates from ExchangeRate-API as a last-resort fiat fallback."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from chand.core.http import HttpClient
from chand.core.models import Asset, ProviderQuote
from chand.providers._util import json_payload, to_decimal
from chand.providers.base import Provider

API_URL = "https://open.er-api.com/v6/latest/USD"
SUPPORTED = {"USD", "EUR", "GBP", "AED", "TRY"}


class ErApiProvider(Provider):
    name = "ExchangeRate-API"
    priority = 40
    homepage = "https://www.exchangerate-api.com/"

    def supports(self, asset: Asset) -> bool:
        return asset.symbol in SUPPORTED

    def fetch(
        self,
        assets: Sequence[Asset],
        client: HttpClient,
    ) -> dict[str, ProviderQuote]:
        response = client.get(API_URL)
        payload = json_payload(response, self.name)
        if not isinstance(payload, dict) or payload.get("result") != "success":
            raise self._error("ExchangeRate-API returned an unsuccessful payload.")
        rates = payload.get("rates")
        if not isinstance(rates, dict):
            raise self._error("ExchangeRate-API response is missing rates.")

        results: dict[str, ProviderQuote] = {}
        for asset in assets:
            if asset.symbol == "USD":
                price_usd = Decimal(1)
            else:
                rate = to_decimal(rates.get(asset.symbol))
                if rate is None or rate <= 0:
                    continue
                price_usd = Decimal(1) / rate
            results[asset.symbol] = ProviderQuote(
                symbol=asset.symbol,
                price_usd=price_usd,
                source=self.name,
                source_url=self.homepage,
            )

        if not results:
            raise self._error("ExchangeRate-API did not return a usable rate.")
        return results
