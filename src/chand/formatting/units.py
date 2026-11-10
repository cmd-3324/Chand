"""Money formatting and Rial/Toman conversion.

Values stay as Decimal until the final render. Displayed fiat amounts are
rounded half-up to whole units, matching common Iranian market notation.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from chand.core.models import RIAL_PER_TOMAN, Unit

_ONE = Decimal("1")
_TEN_THOUSAND = Decimal("10000")


def in_unit(price_irr: Decimal, unit: Unit) -> Decimal:
    return price_irr if unit is Unit.RIAL else price_irr / RIAL_PER_TOMAN


def round_whole(value: Decimal) -> int:
    return int(value.quantize(_ONE, rounding=ROUND_HALF_UP))


def format_amount(price_irr: Decimal, unit: Unit) -> str:
    return f"{round_whole(in_unit(price_irr, unit)):,}"


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
        return round_whole(value)
    return float(round(value, places))
