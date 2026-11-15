"""Small, crash-safe TTL cache for provider quotes.

Cache failures are never fatal: stale or corrupt files are ignored and the
next successful fetch rewrites the cache.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import threading
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from platformdirs import user_cache_dir

from chand.core.models import ProviderQuote
from chand.errors import ChandError

log = logging.getLogger(__name__)
CACHE_VERSION = 1
MAX_ENTRIES = 500


def cache_dir() -> Path:
    """Return Chand's cache directory.

    ``CHAND_CACHE_DIR`` overrides the platform default, which is also useful
    for tests, read-only home directories, and portable installs.
    """

    override = os.environ.get("CHAND_CACHE_DIR")
    if override:
        return Path(override).expanduser()
    return Path(user_cache_dir("chand", "chand"))


def default_cache_path() -> Path:
    return cache_dir() / "quotes.json"


def purge_cache() -> Path:
    """Delete every file Chand has cached for the current user.

    Returns the removed directory. Missing directories are treated as success.
    """

    directory = cache_dir()
    try:
        if directory.exists():
            shutil.rmtree(directory)
    except OSError as exc:
        raise ChandError(
            f"Could not purge cache at {directory}: {exc}",
            hint="Close other Chand processes and check file permissions.",
        ) from exc
    return directory


class PriceCache:
    def __init__(self, ttl: float, path: Path | None = None) -> None:
        self.ttl = max(0.0, ttl)
        self.path = path or default_cache_path()
        self._lock = threading.RLock()
        self._entries: dict[str, dict[str, Any]] = {}
        self._dirty = False
        if self.ttl > 0:
            self._load()

    def get(self, provider: str, symbol: str) -> ProviderQuote | None:
        if self.ttl <= 0:
            return None
        key = self._key(provider, symbol)
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return None
            if float(entry.get("expires_at", 0)) <= time.time():
                self._entries.pop(key, None)
                self._dirty = True
                return None
            try:
                return _decode_quote(entry["quote"])
            except KeyError, TypeError, ValueError, InvalidOperation:
                self._entries.pop(key, None)
                self._dirty = True
                return None

    def set(self, provider: str, symbol: str, quote: ProviderQuote) -> None:
        if self.ttl <= 0:
            return
        with self._lock:
            self._entries[self._key(provider, symbol)] = {
                "expires_at": time.time() + self.ttl,
                "quote": _encode_quote(quote),
            }
            self._dirty = True

    def flush(self) -> None:
        if not self._dirty:
            return
        with self._lock:
            if len(self._entries) > MAX_ENTRIES:
                oldest = sorted(self._entries, key=lambda key: self._entries[key]["expires_at"])
                for key in oldest[: len(self._entries) - MAX_ENTRIES]:
                    self._entries.pop(key, None)
            payload = {"version": CACHE_VERSION, "entries": self._entries}
            self._dirty = False

        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix(self.path.suffix + ".tmp")
            temp.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
            os.replace(temp, self.path)
        except OSError as exc:
            log.debug("could not write cache %s: %s", self.path, exc)
            with self._lock:
                self._dirty = True

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._dirty = True
        try:
            self.path.unlink(missing_ok=True)
        except OSError as exc:
            log.debug("could not remove cache %s: %s", self.path, exc)

    def _load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except OSError, ValueError:
            return
        if not isinstance(raw, dict) or raw.get("version") != CACHE_VERSION:
            return
        entries = raw.get("entries")
        if not isinstance(entries, dict):
            return
        now = time.time()
        with self._lock:
            self._entries = {
                key: value
                for key, value in entries.items()
                if isinstance(value, dict) and float(value.get("expires_at", 0)) > now
            }

    @staticmethod
    def _key(provider: str, symbol: str) -> str:
        return f"{provider}:{symbol}"


def _encode_quote(quote: ProviderQuote) -> dict[str, Any]:
    return {
        "symbol": quote.symbol,
        "price_irr": _encode_decimal(quote.price_irr),
        "price_usd": _encode_decimal(quote.price_usd),
        "change_24h": _encode_decimal(quote.change_24h),
        "source": quote.source,
        "source_url": quote.source_url,
        "fetched_at": quote.fetched_at.isoformat(),
    }


def _decode_quote(payload: dict[str, Any]) -> ProviderQuote:
    return ProviderQuote(
        symbol=str(payload["symbol"]),
        price_irr=_decode_decimal(payload.get("price_irr")),
        price_usd=_decode_decimal(payload.get("price_usd")),
        change_24h=_decode_decimal(payload.get("change_24h")),
        source=str(payload.get("source", "")),
        source_url=str(payload.get("source_url", "")),
        fetched_at=datetime.fromisoformat(str(payload["fetched_at"])),
    )


def _encode_decimal(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _decode_decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    return Decimal(str(value))
