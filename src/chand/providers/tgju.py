"""TGJU free-market fiat rates (Rial) from bulk and profile pages."""

from __future__ import annotations

import contextlib
import re
from collections.abc import Sequence
from decimal import Decimal

from bs4 import BeautifulSoup

from chand.core.http import HttpClient
from chand.core.models import Asset, ProviderQuote
from chand.errors import ChandError
from chand.providers._util import html_payload, to_decimal
from chand.providers.base import Provider

BULK_URL = "https://www.tgju.org/currency"
PROFILE_URL = "https://www.tgju.org/profile/{key}"
BULK_MIN = 6
CONVERT_UNITS = {"JPY": Decimal("100")}
FIAT = (
    "USD",
    "EUR",
    "GBP",
    "AED",
    "TRY",
    "CNY",
    "JPY",
    "CAD",
    "AUD",
    "CHF",
    "SEK",
    "NOK",
    "DKK",
    "RUB",
    "INR",
    "PKR",
    "IQD",
    "SYP",
    "AFN",
    "LBP",
    "QAR",
    "KWD",
    "BHD",
    "OMR",
    "JOD",
    "ILS",
    "SAR",
    "THB",
    "MYR",
    "SGD",
    "HKD",
    "NZD",
    "ZAR",
    "BRL",
    "MXN",
    "KRW",
    "TWD",
    "AZN",
    "AMD",
    "GEL",
    "KGS",
    "TJS",
    "TMT",
    "UZS",
    "BYN",
    "KZT",
    "MNT",
    "IDR",
    "UAH",
)
PROFILES = {"USD": "price_dollar_rl"} | {
    symbol: f"price_{symbol.lower()}" for symbol in FIAT if symbol != "USD"
}
_SLUGS = {key: symbol for symbol, key in PROFILES.items()}
_PERCENT = re.compile(r"\(([-+]?[0-9.,]*)\s*%\)")


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
        wanted = [asset for asset in assets if asset.symbol in PROFILES]
        results: dict[str, ProviderQuote] = {}

        if len(wanted) >= BULK_MIN:
            with contextlib.suppress(ChandError):
                results.update(self._fetch_bulk(wanted, client))

        for asset in wanted:
            if asset.symbol in results:
                continue
            key = PROFILES[asset.symbol]
            try:
                quote = self._fetch_one(asset, key, client)
            except ChandError:
                continue
            if quote is not None:
                results[asset.symbol] = quote

        if not results:
            raise self._error(
                "TGJU did not return a usable price.",
                hint="TGJU may have changed its pages or blocked the request.",
            )
        return results

    def _fetch_bulk(
        self,
        assets: Sequence[Asset],
        client: HttpClient,
    ) -> dict[str, ProviderQuote]:
        response = client.get(BULK_URL)
        html = html_payload(response, self.name)
        wanted = {asset.symbol for asset in assets}
        soup = BeautifulSoup(html, "html.parser")

        results: dict[str, ProviderQuote] = {}
        for row in soup.select("tr[data-market-nameslug]"):
            symbol = _SLUGS.get(str(row.get("data-market-nameslug") or ""))
            if symbol is None or symbol not in wanted:
                continue
            price = to_decimal(row.get("data-price"))
            cells = row.select("td.nf")
            if price is None and cells:
                price = to_decimal(cells[0].get_text())
            if price is None or price <= 0:
                continue

            change = None
            classes: list[str] = []
            if len(cells) > 1:
                change_span = cells[1].select_one("span")
                if change_span is not None:
                    classes = change_span.get("class", [])
                    match = _PERCENT.search(change_span.get_text(" ", strip=True))
                    if match:
                        change = to_decimal(match.group(1))
            if change is not None:
                if "low" in classes:
                    change = -abs(change)
                elif "high" in classes:
                    change = abs(change)

            price /= CONVERT_UNITS.get(symbol, Decimal(1))
            results[symbol] = ProviderQuote(
                symbol=symbol,
                price_irr=price,
                change_24h=change,
                source=self.name,
                source_url=PROFILE_URL.format(key=PROFILES[symbol]),
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
        soup = BeautifulSoup(html, "html.parser")

        price: Decimal | None = None
        change: Decimal | None = None
        classes: list[str] = []

        container = soup.find(id=f"l-{key}")
        if container is not None:
            price_span = container.select_one(".info-price")
            price = to_decimal(price_span.get_text() if price_span else None)
            change_span = container.select_one(".info-change")
            change_text = change_span.get_text().strip("() ") if change_span else None
            change = to_decimal(change_text)
            classes = container.get("class", [])
        else:
            price_node = soup.select_one('span.value [data-col="info.last_trade.PDrCotVal"]')
            price = to_decimal(price_node.get_text() if price_node else None)
            change_node = soup.select_one(
                'span.value [data-col="info.last_trade.last_change_percentage"]'
            )
            if change_node is not None:
                change = to_decimal(change_node.get_text())
                marker = change_node.select_one(".change")
                if marker is not None:
                    classes = marker.get("class", [])

        if price is None or price <= 0:
            return None
        if change is not None:
            if "low" in classes or "change-down" in classes:
                change = -abs(change)
            elif "high" in classes or "change-up" in classes:
                change = abs(change)

        price /= CONVERT_UNITS.get(asset.symbol, Decimal(1))
        return ProviderQuote(
            symbol=asset.symbol,
            price_irr=price,
            change_24h=change,
            source=self.name,
            source_url=PROFILE_URL.format(key=key),
        )
