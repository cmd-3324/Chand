"""Parsing helpers shared by providers."""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from typing import Any

import requests

from chand.errors import ProviderError

_DIGITS = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)
_NUMBER = re.compile(r"[^0-9+\-.]")


def to_decimal(value: Any) -> Decimal | None:
    """Convert API values (ints, floats, formatted strings, Persian digits) to Decimal."""

    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return Decimal(str(value))

    text = str(value).translate(_DIGITS).strip()
    if not text or text in {"-", "—", "N/A", "null"}:
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = text.strip("()").replace(",", "").replace("٬", "").replace(" ", "")
    text = _NUMBER.sub("", text)
    if not text or text in {"+", "-", ".", "+.", "-."}:
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    return -number if negative else number


def json_payload(response: requests.Response, provider: str) -> Any:
    if response.status_code >= 400:
        raise ProviderError(
            f"{provider} returned HTTP {response.status_code}.",
            provider=provider,
        )
    try:
        return response.json()
    except ValueError as exc:
        raise ProviderError(
            f"{provider} returned a non-JSON response.",
            provider=provider,
        ) from exc


def html_payload(response: requests.Response, provider: str) -> str:
    if response.status_code >= 400:
        raise ProviderError(
            f"{provider} returned HTTP {response.status_code}.",
            provider=provider,
        )
    content_type = response.headers.get("content-type", "").lower()
    if "html" not in content_type and "<html" not in response.text[:500].lower():
        raise ProviderError(
            f"{provider} returned an unexpected response (not HTML).",
            provider=provider,
        )
    return response.text
