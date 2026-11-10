"""NerkhAra free-market rates (fiat and USDT quoted in Toman)."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from chand.core.http import HttpClient
from chand.core.models import Asset, ProviderQuote
from chand.providers._util import json_payload, to_decimal
from chand.providers.base import Provider

API_URL = "https://nerkhara.com/api/v1/latest.json"
TOMAN = Decimal("10")
FIAT = {
    "USD",
    "EUR",
    "GBP",
    "CNY",
    "AED",
    "QAR",
    "SAR",
    "KWD",
    "OMR",
    "BHD",
    "IQD",
    "TRY",
    "LBP",
    "SYP",
    "AFN",
    "JPY",
    "CHF",
    "DKK",
    "SEK",
    "NOK",
    "AUD",
    "CAD",
    "NZD",
    "RUB",
    "INR",
    "PKR",
    "MYR",
    "SGD",
    "HKD",
    "THB",
    "IDR",
    "KRW",
    "AZN",
    "AMD",
    "GEL",
    "KGS",
    "UZS",
    "TJS",
    "TMT",
    "KZT",
    "BRL",
    "MXN",
    "ZAR",
    "UAH",
}
CRYPTO = {"USDT"}


class NerkhAraProvider(Provider):
    name = "NerkhAra"
    priority = 15
    homepage = "https://nerkhara.com/"

    def supports(self, asset: Asset) -> bool:
        return asset.symbol in FIAT or asset.symbol in CRYPTO

    def fetch(
        self,
        assets: Sequence[Asset],
        client: HttpClient,
    ) -> dict[str, ProviderQuote]:
        wanted = {asset.symbol for asset in assets if self.supports(asset)}
        response = client.get(API_URL)
        payload = json_payload(response, self.name)
        items = payload.get("items") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            raise self._error("NerkhAra response is missing rates.")

        results: dict[str, ProviderQuote] = {}
        for item in items:
            if not isinstance(item, dict) or item.get("family") != "currency":
                continue
            symbol = str(item.get("id") or "").upper()
            if symbol not in wanted:
                continue

            price = to_decimal(item.get("price"))
            unit = str(item.get("unit") or "IRT").upper()
            if price is None:
                price = to_decimal(item.get("price_irt"))
                unit = "IRR"
            if price is None or price <= 0:
                continue
            if unit == "IRT":
                price *= TOMAN
            elif unit != "IRR":
                continue

            page = item.get("page")
            source_url = page.get("fa") if isinstance(page, dict) else None
            results[symbol] = ProviderQuote(
                symbol=symbol,
                price_irr=price,
                change_24h=to_decimal(item.get("change_pct")),
                source=self.name,
                source_url=source_url or self.homepage,
            )

        if not results:
            raise self._error("NerkhAra did not return a usable price.")
        return results
