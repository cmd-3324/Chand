"""TGJU free-market fiat rates (Rial) with daily change where available."""

from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from bs4 import BeautifulSoup

from chand.core.http import HttpClient
from chand.core.models import Asset, ProviderQuote
from chand.errors import ChandError
from chand.providers._util import html_payload, to_decimal
from chand.providers.base import Provider

PROFILE_URL = "https://www.tgju.org/profile/{key}"
PROFILES = {
    "USD": "price_dollar_rl",
    "EUR": "price_eur",
    "GBP": "price_gbp",
    "AED": "price_aed",
    "TRY": "price_try",
}
CONTEXT_CHARS = 1600


class TgjuProvider(Provider):
    name = "TGJU"
    priority = 20
    homepage = "https://www.tgju.org/"

    def supports(self, asset: Asset) -> bool:
        return asset.symbol in PROFILES

    def fetch(
        self,
        assets: Sequence[Asset],
        client: HttpClient,
    ) -> dict[str, ProviderQuote]:
        results: dict[str, ProviderQuote] = {}
        for asset in assets:
            key = PROFILES.get(asset.symbol)
            if key is None:
                continue
            try:
                quote = self._fetch_one(asset, key, client)
            except ChandError:
                continue
            if quote is not None:
                results[asset.symbol] = quote

        if not results:
            raise self._error(
                "TGJU did not return a usable price.",
                hint="TGJU may have changed its profile pages or blocked the request.",
            )
        return results

    def _fetch_one(
        self,
        asset: Asset,
        key: str,
        client: HttpClient,
    ) -> ProviderQuote | None:
        response = client.get(PROFILE_URL.format(key=key))
        html = html_payload(response, self.name)

        marker = html.find(f'id="l-{key}"')
        if marker < 0:
            return None
        start = html.rfind("<li", 0, marker)
        chunk = html[max(0, start) : marker + CONTEXT_CHARS]
        soup = BeautifulSoup(chunk, "html.parser")
        container = soup.find(id=f"l-{key}")
        if container is None:
            return None

        price_span = container.select_one(".info-price")
        price = to_decimal(price_span.get_text() if price_span else None)
        if price is None or price <= 0:
            return None

        change_span = container.select_one(".info-change")
        change_text = change_span.get_text().strip("() ") if change_span else None
        change = to_decimal(change_text)
        classes = container.get("class", [])
        if change is not None:
            if "low" in classes:
                change = -abs(change)
            elif "high" in classes:
                change = abs(change)

        return ProviderQuote(
            symbol=asset.symbol,
            price_irr=Decimal(price),
            change_24h=change,
            source=self.name,
            source_url=PROFILE_URL.format(key=key),
        )
