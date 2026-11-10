"""Stable machine-readable output."""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from typing import Any

from chand.core.models import RIAL_PER_TOMAN, Asset, PricingResult, Quote, Unit
from chand.formatting.units import to_json_number


def quote_payload(quote: Quote, unit: Unit) -> dict[str, Any]:
    return {
        "symbol": quote.asset.symbol,
        "name": quote.asset.name,
        "kind": quote.asset.kind.value,
        "unit": unit.value,
        "price": to_json_number(quote.price(unit)),
        "price_irr": to_json_number(quote.price_irr),
        "price_toman": to_json_number(quote.price_irr / RIAL_PER_TOMAN),
        "price_usd": to_json_number(quote.price_usd, places=8),
        "change_24h": to_json_number(quote.change_24h, places=4),
        "source": quote.source,
        "source_url": quote.source_url,
        "fetched_at": quote.fetched_at.isoformat(),
    }


def pricing_payload(result: PricingResult, unit: Unit) -> list[dict[str, Any]]:
    return [quote_payload(quote, unit) for quote in result.quotes]


def assets_payload(assets: Iterable[Asset]) -> list[dict[str, Any]]:
    return [
        {
            "symbol": asset.symbol,
            "name": asset.name,
            "kind": asset.kind.value,
            "aliases": list(asset.aliases),
        }
        for asset in assets
    ]


def write_json(payload: Any, *, stream=None) -> None:
    target = stream or sys.stdout
    target.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    target.flush()


def write_json_line(payload: Any, *, stream=None) -> None:
    """Newline-delimited JSON, used by ``--watch --format json``."""

    target = stream or sys.stdout
    target.write(json.dumps(payload, ensure_ascii=False) + "\n")
    target.flush()
