"""Open source pages in the user's default browser, safely and at most once."""

from __future__ import annotations

import webbrowser
from collections.abc import Iterable
from urllib.parse import urlsplit

from rich.console import Console
from rich.text import Text

from chand.core.models import PricingResult
from chand.errors import BrowserError

MAX_URLS = 10


def collect_quote_urls(result: PricingResult) -> list[str]:
    return _unique([quote.source_url for quote in result.quotes])


def open_urls(urls: Iterable[str], *, console: Console) -> int:
    """Open http(s) URLs in the default browser.

    Returns the number of pages opened. Raises ``BrowserError`` only when every
    attempt fails, so a partially working browser setup still reports URLs.
    """

    valid = _unique(url for url in urls if is_safe_url(url))
    if not valid:
        return 0
    if len(valid) > MAX_URLS:
        console.print(
            Text(
                f"warning: opening only the first {MAX_URLS} of {len(valid)} source pages.",
                style="yellow",
            )
        )
        valid = valid[:MAX_URLS]

    opened: list[str] = []
    failed: list[str] = []
    for url in valid:
        try:
            if webbrowser.open(url, new=2, autoraise=False):
                opened.append(url)
            else:
                failed.append(url)
        except Exception:
            failed.append(url)

    if opened:
        console.print(Text(f"Opened {len(opened)} source page(s) in your browser.", style="dim"))
    if failed:
        print_urls(failed, console=console)
        if not opened:
            raise BrowserError(
                "Could not open a browser.",
                hint="Open one of the URLs above manually.",
            )
    return len(opened)


def print_urls(urls: Iterable[str], *, console: Console) -> None:
    for url in _unique(urls):
        console.print(Text(url, style="dim"))


def is_safe_url(url: str) -> bool:
    if not url:
        return False
    parts = urlsplit(url)
    return parts.scheme in {"http", "https"} and bool(parts.netloc)


def _unique(urls: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for url in urls:
        if url and url not in seen:
            seen.add(url)
            result.append(url)
    return result
