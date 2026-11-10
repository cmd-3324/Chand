"""Money formatting and Rial/Toman conversion.

Values stay as Decimal until the final render. Displayed amounts are rounded
half-up to whole units for large values, while small values keep up to four
decimals so low-priced crypto remains meaningful.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from chand.core.models import RIAL_PER_TOMAN, Unit

_ONE = Decimal("1")
_THOUSAND = Decimal("1000")
_TEN_THOUSAND = Decimal("10000")
_FOUR_PLACES = Decimal("0.0001")


def in_unit(price_irr: Decimal, unit: Unit) -> Decimal:
    return price_irr if unit is Unit.RIAL else price_irr / RIAL_PER_TOMAN


def round_whole(value: Decimal) -> int:
    return int(value.quantize(_ONE, rounding=ROUND_HALF_UP))


def format_amount(price_irr: Decimal, unit: Unit) -> str:
    value = in_unit(price_irr, unit)
    if abs(value) >= _THOUSAND:
        return f"{round_whole(value):,}"
    text = f"{value.quantize(_FOUR_PLACES, rounding=ROUND_HALF_UP):,f}"
    return text.rstrip("0").rstrip(".")


def format_usd(value: Decimal | None) -> str:
    if value is None:
        return "-"
    absolute = abs(value)
    if absolute >= _TEN_THOUSAND:
        return f"{value:,.2f}"
    if absolute >= _ONE:
        return f"{value:,.2f}"
    if absolute >= Decimal("0.01"):
        return f"{value:,.4f}"
    return f"{value:,.8f}"


def format_change(change: Decimal | None) -> str:
    if change is None:
        return "-"
    sign = "+" if change > 0 else ""
    return f"{sign}{change:.2f}%"


def unit_label(unit: Unit) -> str:
    return "Rial" if unit is Unit.RIAL else "Toman"


def to_json_number(value: Decimal | None, *, places: int | None = None) -> int | float | None:
    """Convert Decimal to a JSON-safe number without binary float noise."""

    if value is None:
        return None
    if places is None:
        if abs(value) >= _THOUSAND:
            return round_whole(value)
        return float(round(value, 8))
    return float(round(value, places))
