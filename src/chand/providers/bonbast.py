"""Bonbast free-market rates.

Bonbast serves prices through a short-lived token embedded in the HTML; the
provider follows that flow with a real session (cookies + referer). Fiat values
are quoted in Toman and converted to Rial here.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from decimal import Decimal

from chand.core.http import HttpClient
from chand.core.models import Asset, AssetKind, ProviderQuote
from chand.providers._util import html_payload, json_payload, to_decimal
from chand.providers.base import Provider

HOME_URL = "https://bonbast.com/"
JSON_URL = "https://bonbast.com/json"
TOMAN = Decimal("10")

FIAT = {"USD": "usd", "EUR": "eur", "GBP": "gbp", "AED": "aed", "TRY": "try"}
CRYPTO = {"BTC": "bitcoin"}
_PARAM = re.compile(r'param:\s*"([^"]+)"')


class BonbastProvider(Provider):
    name = "Bonbast"
    priority = 30
    homepage = "https://bonbast.com/"

    def supports(self, asset: Asset) -> bool:
        return asset.symbol in FIAT or asset.symbol in CRYPTO

    def fetch(
        self,
        assets: Sequence[Asset],
        client: HttpClient,
    ) -> dict[str, ProviderQuote]:
        page = client.get(HOME_URL)
        html = html_payload(page, self.name)
        match = _PARAM.search(html)
        if match is None:
            raise self._error(
                "Bonbast did not expose a data token.",
                hint="The page layout may have changed, or access is blocked.",
            )

        response = client.post(
            JSON_URL,
            data={"param": match.group(1)},
            headers={
                "Referer": HOME_URL,
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json",
            },
        )
        payload = json_payload(response, self.name)
        if not isinstance(payload, dict):
            raise self._error("Bonbast returned an unexpected payload.")
        if "rest" in payload and "usd1" not in payload:
            raise self._error(
                "Bonbast rate-limited the request.",
                hint="Wait a few seconds and try again.",
            )

        results: dict[str, ProviderQuote] = {}
        for asset in assets:
            if asset.kind is AssetKind.FIAT:
                code = FIAT.get(asset.symbol)
                if code is None:
                    continue
                value = to_decimal(payload.get(f"{code}1"))
                if value is None:
                    value = to_decimal(payload.get(f"{code}2"))
                if value is None or value <= 0:
                    continue
                results[asset.symbol] = ProviderQuote(
                    symbol=asset.symbol,
                    price_irr=value * TOMAN,
                    source=self.name,
                    source_url=f"https://bonbast.com/graph/{code}",
                )
            else:
                code = CRYPTO.get(asset.symbol)
                if code is None:
                    continue
                value = to_decimal(payload.get(code))
                if value is None or value <= 0:
                    continue
                results[asset.symbol] = ProviderQuote(
                    symbol=asset.symbol,
                    price_usd=value,
                    source=self.name,
                    source_url=HOME_URL,
                )

        if not results:
            raise self._error("Bonbast did not return a usable price.")
        return results
