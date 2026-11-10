"""``chand price`` command."""

from __future__ import annotations

from typing import Annotated

import typer

from chand.cli.common import resolve_settings, run_once, run_watch
from chand.core.models import OutputFormat, Unit
from chand.core.registry import select_assets
from chand.errors import ChandError
from chand.formatting.errors import print_error
from chand.formatting.table import make_console

TITLE = "Chand - live prices"


def price(
    assets: Annotated[
        list[str] | None,
        typer.Argument(
            help="Assets to quote (BTC, ETH, USDT, USD, EUR, GBP, AED, TRY).",
            show_default=False,
        ),
    ] = None,
    unit: Annotated[
        Unit | None,
        typer.Option("--unit", "-u", help="Output unit: rial or toman."),
    ] = None,
    output_format: Annotated[
        OutputFormat | None,
        typer.Option("--format", "-f", help="Output format: table or json."),
    ] = None,
    watch: Annotated[
        float | None,
        typer.Option(
            "--watch",
            min=1.0,
            help="Refresh every N seconds until Ctrl+C (disables the cache).",
            show_default=False,
        ),
    ] = None,
    all_assets: Annotated[
        bool,
        typer.Option("--all", "-a", help="Quote every supported asset."),
    ] = False,
    currencies: Annotated[
        str | None,
        typer.Option("--currency", help="Select fiat currencies, comma-separated (USD,EUR)."),
    ] = None,
    cryptos: Annotated[
        str | None,
        typer.Option("--crypto", help="Select cryptocurrencies, comma-separated (BTC,ETH)."),
    ] = None,
    web: Annotated[
        bool,
        typer.Option("--web", "-w", help="Open each result's source page in your browser."),
    ] = False,
    no_cache: Annotated[
        bool,
        typer.Option("--no-cache", help="Ignore and do not write the local quote cache."),
    ] = False,
    timeout: Annotated[
        float | None,
        typer.Option("--timeout", min=0.5, help="HTTP timeout in seconds."),
    ] = None,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", help="Disable colors (NO_COLOR is also honored)."),
    ] = False,
) -> None:
    """Quote one or more assets as a table or JSON.

    Examples:
      chand price BTC
      chand price BTC ETH USD --unit rial
      chand price --currency USD,EUR --unit toman
      chand price --all --format json
      chand price BTC --watch 5
      chand price BTC -w
    """

    fallback = output_format or OutputFormat.TABLE
    error_console = None
    try:
        settings = resolve_settings(
            unit=unit,
            output_format=output_format,
            watch=watch,
            no_cache=no_cache,
            timeout=timeout,
            no_color=no_color,
        )
        fallback = settings.output_format
        selected = select_assets(
            assets,
            all_assets=all_assets,
            currencies=currencies,
            cryptos=cryptos,
        )
        console = make_console(no_color=settings.no_color)
        error_console = make_console(stderr=True, no_color=settings.no_color)

        if watch is not None:
            run_watch(
                selected,
                settings,
                console=console,
                error_console=error_console,
                title=TITLE,
                web=web,
            )
        else:
            run_once(
                selected,
                settings,
                console=console,
                error_console=error_console,
                title=TITLE,
                web=web,
            )
    except ChandError as exc:
        print_error(exc, fallback, console=error_console)
        raise typer.Exit(exc.exit_code) from None
    except KeyboardInterrupt:
        raise typer.Exit(130) from None
