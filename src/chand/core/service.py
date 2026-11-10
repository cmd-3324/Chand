"""Pricing orchestration: provider fallback, caching, and unit conversion."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from decimal import Decimal

from chand.core.cache import PriceCache
from chand.core.http import HttpClient
from chand.core.models import Asset, Failure, PricingResult, ProviderQuote, Quote
from chand.core.registry import resolve
from chand.errors import ChandError
from chand.providers.base import Provider

log = logging.getLogger(__name__)
USD = "USD"
_USD_ASSET = resolve(USD)


class PricingService:
    """Resolve asset prices with provider priority and cached fallback."""

    def __init__(
        self,
        providers: Sequence[Provider],
        cache: PriceCache,
        http: HttpClient | None = None,
        *,
        timeout: float = 10.0,
    ) -> None:
        self.providers = list(providers)
        self.cache = cache
        self._owns_http = http is None
        self.http = http or HttpClient(timeout)

    def fetch(self, assets: Iterable[Asset]) -> PricingResult:
        requested = _dedupe(assets)
        if not requested:
            return PricingResult(quotes=[], failures=[], usd_irr=None)

        usd_requested = any(asset.symbol == USD for asset in requested)
        errors: dict[str, Failure] = {}
        usd_irr: Decimal | None = None

        if usd_requested:
            raw, raw_errors = self._resolve(requested)
            errors.update(raw_errors)
            usd_quote = raw.get(USD)
            if usd_quote is not None:
                usd_irr = usd_quote.price_irr
        else:
            usd_raw, _ = self._resolve([_USD_ASSET])
            usd_quote = usd_raw.get(USD)
            if usd_quote is not None:
                usd_irr = usd_quote.price_irr
            others = [asset for asset in requested if asset.symbol != USD]
            raw, raw_errors = self._resolve(others)
            errors.update(raw_errors)

        quotes: list[Quote] = []
        failures: list[Failure] = []
        try:
            for asset in requested:
                provider_quote = raw.get(asset.symbol)
                if provider_quote is None:
                    failures.append(errors.get(asset.symbol) or _missing(asset))
                    continue

                price_irr = provider_quote.price_irr
                price_usd = provider_quote.price_usd

                if price_irr is None and price_usd is not None:
                    if usd_irr is None:
                        failures.append(
                            Failure(
                                asset.symbol,
                                "USD/IRR market rate is unavailable, cannot convert.",
                                provider_quote.source,
                            )
                        )
                        continue
                    price_irr = price_usd * usd_irr

                if price_irr is None:
                    failures.append(_missing(asset))
                    continue

                if asset.symbol == USD:
                    price_usd = Decimal(1)
                elif price_usd is None and usd_irr:
                    price_usd = price_irr / usd_irr

                quotes.append(
                    Quote(
                        asset=asset,
                        price_irr=price_irr,
                        price_usd=price_usd,
                        change_24h=provider_quote.change_24h,
                        source=provider_quote.source,
                        source_url=provider_quote.source_url,
                        fetched_at=provider_quote.fetched_at,
                    )
                )
        finally:
            self.cache.flush()

        return PricingResult(quotes=quotes, failures=failures, usd_irr=usd_irr)

    def _resolve(
        self,
        assets: Sequence[Asset],
    ) -> tuple[dict[str, ProviderQuote], dict[str, Failure]]:
        """Walk providers in priority order, filling symbols until all are quoted."""

        remaining = {asset.symbol: asset for asset in assets}
        found: dict[str, ProviderQuote] = {}
        errors: dict[str, Failure] = {}

        for provider in self.providers:
            candidates = [asset for asset in remaining.values() if provider.supports(asset)]
            if not candidates:
                continue

            pending: list[Asset] = []
            for asset in candidates:
                cached = self.cache.get(provider.name, asset.symbol)
                if cached is not None and _usable(cached):
                    found[asset.symbol] = cached
                    remaining.pop(asset.symbol, None)
                else:
                    pending.append(asset)

            if not pending:
                continue

            try:
                fetched = provider.fetch(pending, self.http)
            except ChandError as exc:
                for asset in pending:
                    errors[asset.symbol] = Failure(asset.symbol, exc.message, provider.name)
                log.debug("%s failed: %s", provider.name, exc)
                continue
            except Exception as exc:  # defensive: one bad provider must not stop fallback
                for asset in pending:
                    errors[asset.symbol] = Failure(
                        asset.symbol,
                        f"{provider.name} failed unexpectedly: {exc}",
                        provider.name,
                    )
                log.debug("%s crashed", provider.name, exc_info=True)
                continue

            for asset in pending:
                quote = fetched.get(asset.symbol)
                if quote is None or not _usable(quote):
                    errors.setdefault(
                        asset.symbol,
                        Failure(asset.symbol, f"{provider.name} returned no price.", provider.name),
                    )
                    continue
                found[asset.symbol] = quote
                remaining.pop(asset.symbol, None)
                self.cache.set(provider.name, asset.symbol, quote)

        return found, errors

    def close(self) -> None:
        if self._owns_http:
            self.http.close()

    def __enter__(self) -> PricingService:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


def _usable(quote: ProviderQuote) -> bool:
    values = [quote.price_irr, quote.price_usd]
    return any(value is not None and value > 0 for value in values)


def _dedupe(assets: Iterable[Asset]) -> list[Asset]:
    seen: set[str] = set()
    result: list[Asset] = []
    for asset in assets:
        if asset.symbol not in seen:
            seen.add(asset.symbol)
            result.append(asset)
    return result


def _missing(asset: Asset) -> Failure:
    return Failure(
        asset.symbol,
        f"No provider returned a usable price for {asset.symbol}.",
    )
