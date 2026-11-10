"""Shared CLI plumbing: settings, service lifecycle, rendering, and watch mode."""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import replace

from rich.console import Console
from rich.live import Live
from rich.text import Text

from chand.core.cache import PriceCache
from chand.core.config import Settings
from chand.core.models import Asset, Failure, OutputFormat, PricingResult, Unit
from chand.core.service import PricingService
from chand.errors import BrowserError, ChandError, ProviderError, UsageError
from chand.formatting.browser import collect_quote_urls, open_urls, print_urls
from chand.formatting.json_out import pricing_payload, write_json, write_json_line
from chand.formatting.table import build_price_table, print_failures
from chand.providers import build_providers


def resolve_settings(
    *,
    unit: Unit | None = None,
    output_format: OutputFormat | None = None,
    watch: float | None = None,
    no_cache: bool = False,
    timeout: float | None = None,
    no_color: bool = False,
) -> Settings:
    settings = Settings.from_env()
    if watch is not None and watch < 1:
        raise UsageError("--watch must be at least 1 second.")
    cache_ttl = 0.0 if no_cache or watch is not None else settings.cache_ttl
    return settings.apply(
        unit=unit,
        output_format=output_format,
        watch_interval=watch,
        cache_ttl=cache_ttl,
        timeout=timeout,
        no_color=True if no_color else None,
    )


def build_service(settings: Settings) -> PricingService:
    return PricingService(
        build_providers(settings),
        PriceCache(settings.cache_ttl),
        timeout=settings.timeout,
    )


def run_once(
    assets: Sequence[Asset],
    settings: Settings,
    *,
    console: Console,
    error_console: Console,
    title: str,
    web: bool,
) -> None:
    with build_service(settings) as service:
        result = service.fetch(assets)

    if not result.quotes:
        raise aggregate_error(result)
    if result.failures:
        print_failures(result, error_console)

    if settings.output_format is OutputFormat.JSON:
        if web:
            _announce_urls(result, error_console)
        write_json(pricing_payload(result, settings.unit))
        return

    console.print(build_price_table(result, settings.unit, title=title))
    if web:
        _open_quote_pages(result, error_console)


def run_watch(
    assets: Sequence[Asset],
    settings: Settings,
    *,
    console: Console,
    error_console: Console,
    title: str,
    web: bool,
) -> None:
    interval = settings.watch_interval
    with build_service(settings) as service:
        result = service.fetch(assets)
        if not result.quotes:
            raise aggregate_error(result)
        if result.failures:
            print_failures(result, error_console)

        error_console.print(
            Text(
                f"Watching {len(assets)} asset(s) every {interval:g}s. Press Ctrl+C to stop.",
                style="dim",
            )
        )
        opened = False

        if settings.output_format is OutputFormat.JSON:
            _watch_json(
                service,
                assets,
                settings,
                result,
                error_console=error_console,
                web=web,
            )
            return

        if web:
            _open_quote_pages(result, error_console)
            opened = True

        last_good = result
        with Live(
            build_price_table(result, settings.unit, title=title),
            console=console,
            refresh_per_second=4,
        ) as live:
            while True:
                time.sleep(interval)
                try:
                    result = service.fetch(assets)
                except ChandError as exc:
                    _report_watch_error(exc, error_console)
                    if last_good is not None:
                        live.update(
                            build_price_table(
                                replace(
                                    last_good,
                                    failures=[Failure("*", exc.message)],
                                ),
                                settings.unit,
                                title=title,
                            )
                        )
                    continue

                if result.quotes:
                    last_good = result
                    display = result
                else:
                    display = replace(last_good, failures=result.failures)
                live.update(build_price_table(display, settings.unit, title=title))
                if web and not opened:
                    _open_quote_pages(result, error_console)
                    opened = True


def _watch_json(
    service: PricingService,
    assets: Sequence[Asset],
    settings: Settings,
    result: PricingResult,
    *,
    error_console: Console,
    web: bool,
) -> None:
    write_json_line(pricing_payload(result, settings.unit))
    if web:
        _announce_urls(result, error_console)
    while True:
        time.sleep(settings.watch_interval)
        try:
            result = service.fetch(assets)
        except ChandError as exc:
            _report_watch_error(exc, error_console)
            continue
        write_json_line(pricing_payload(result, settings.unit))
        if result.failures:
            print_failures(result, error_console)


def aggregate_error(result: PricingResult) -> ProviderError:
    detail = "; ".join(f"{failure.symbol}: {failure.message}" for failure in result.failures)
    return ProviderError(
        "No prices could be retrieved.",
        hint=detail or "All configured providers failed.",
    )


def announce_provider_homepages(settings: Settings, *, console: Console) -> None:
    providers = build_providers(settings)
    print_urls((provider.homepage for provider in providers), console=console)


def open_provider_homepages(settings: Settings, *, console: Console) -> None:
    providers = build_providers(settings)
    try:
        open_urls((provider.homepage for provider in providers), console=console)
    except BrowserError as exc:
        console.print(Text(f"warning: {exc.message}", style="yellow"))


def _announce_urls(result: PricingResult, console: Console) -> None:
    print_urls(collect_quote_urls(result), console=console)


def _open_quote_pages(result: PricingResult, console: Console) -> None:
    try:
        open_urls(collect_quote_urls(result), console=console)
    except BrowserError as exc:
        console.print(Text(f"warning: {exc.message}", style="yellow"))


def _report_watch_error(exc: ChandError, console: Console) -> None:
    console.print(Text(f"warning: {exc.message}", style="yellow"))
