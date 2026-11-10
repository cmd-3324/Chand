from __future__ import annotations

from decimal import Decimal

from chand.core.models import Unit
from chand.formatting.units import (
    format_amount,
    format_change,
    format_usd,
    in_unit,
    round_whole,
    to_json_number,
)


def test_rial_to_toman_conversion() -> None:
    assert in_unit(Decimal("2629000"), Unit.TOMAN) == Decimal("262900")
    assert in_unit(Decimal("2629000"), Unit.RIAL) == Decimal("2629000")


def test_amounts_round_half_up_and_use_thousands_separators() -> None:
    assert round_whole(Decimal("1234.5")) == 1235
    assert format_amount(Decimal("12345"), Unit.TOMAN) == "1,235"
    assert format_amount(Decimal("12345"), Unit.RIAL) == "12,345"


def test_small_amounts_keep_meaningful_precision() -> None:
    assert format_amount(Decimal("11.261"), Unit.TOMAN) == "1.1261"
    assert format_amount(Decimal("715"), Unit.TOMAN) == "71.5"
    assert format_amount(Decimal("715"), Unit.RIAL) == "715"


def test_usd_formatting_is_adaptive() -> None:
    assert format_usd(None) == "-"
    assert format_usd(Decimal("74506.125")) == "74,506.12"
    assert format_usd(Decimal("1.23456")) == "1.23"
    assert format_usd(Decimal("0.123456")) == "0.1235"
    assert format_usd(Decimal("0.00123456")) == "0.00123456"


def test_change_formatting_handles_signs_and_missing_values() -> None:
    assert format_change(None) == "-"
    assert format_change(Decimal("1.234")) == "+1.23%"
    assert format_change(Decimal("-0.5")) == "-0.50%"
    assert format_change(Decimal("0")) == "0.00%"


def test_json_numbers_avoid_floats_for_whole_values() -> None:
    assert to_json_number(Decimal("2629000.4")) == 2629000
    assert to_json_number(Decimal("11.261")) == 11.261
    assert to_json_number(Decimal("0.123456789"), places=8) == 0.12345679
    assert to_json_number(None) is None
