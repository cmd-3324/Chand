from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from io import StringIO

import pytest
from rich.console import Console

from chand.core.models import PricingResult, Quote
from chand.core.registry import resolve
from chand.errors import BrowserError
from chand.formatting.browser import (
    collect_quote_urls,
    is_safe_url,
    open_urls,
)


def _console() -> Console:
    return Console(file=StringIO(), no_color=True)


def _quote(symbol: str, url: str) -> Quote:
    asset = resolve(symbol)
    return Quote(
        asset=asset,
        price_irr=Decimal(1),
        price_usd=Decimal(1),
        change_24h=None,
        source="test",
        source_url=url,
        fetched_at=datetime(2026, 11, 10, tzinfo=UTC),
    )


def test_safe_urls_only_allow_http_and_hosts() -> None:
    assert is_safe_url("https://example.com/page")
    assert is_safe_url("http://example.com")
    assert not is_safe_url("javascript:alert(1)")
    assert not is_safe_url("file:///etc/passwd")
    assert not is_safe_url("")
    assert not is_safe_url("https://")


def test_collect_quote_urls_deduplicates_and_skips_empty() -> None:
    result = PricingResult(
        quotes=[
            _quote("BTC", "https://example.com/btc"),
            _quote("ETH", "https://example.com/btc"),
            _quote("USD", ""),
        ],
        failures=[],
        usd_irr=Decimal(1),
    )
    assert collect_quote_urls(result) == ["https://example.com/btc"]


def test_open_urls_opens_each_page(monkeypatch) -> None:
    opened: list[str] = []

    def fake_open(url, new=0, autoraise=True):
        opened.append(url)
        return True

    monkeypatch.setattr("chand.formatting.browser.webbrowser.open", fake_open)
    count = open_urls(["https://a.test", "https://b.test", "https://a.test"], console=_console())

    assert count == 2
    assert opened == ["https://a.test", "https://b.test"]


def test_open_urls_is_capped(monkeypatch) -> None:
    monkeypatch.setattr("chand.formatting.browser.webbrowser.open", lambda *a, **k: True)
    urls = [f"https://example.test/{index}" for index in range(12)]
    out = StringIO()
    count = open_urls(urls, console=Console(file=out, no_color=True))

    assert count == 10
    assert "first 10" in out.getvalue()


def test_open_urls_raises_when_every_page_fails(monkeypatch) -> None:
    monkeypatch.setattr("chand.formatting.browser.webbrowser.open", lambda *a, **k: False)
    out = StringIO()

    with pytest.raises(BrowserError):
        open_urls(["https://example.test"], console=Console(file=out, no_color=True))
    assert "https://example.test" in out.getvalue()
