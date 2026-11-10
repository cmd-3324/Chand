"""``chand list`` command."""

from __future__ import annotations

from typing import Annotated

import typer

from chand.cli.common import (
    announce_provider_homepages,
    open_provider_homepages,
    resolve_settings,
)
from chand.core.models import OutputFormat
from chand.core.registry import filtered_assets
from chand.errors import ChandError
from chand.formatting.errors import print_error
from chand.formatting.json_out import assets_payload, write_json
from chand.formatting.table import build_asset_table, make_console


def list_assets(
    currencies: Annotated[
        str | None,
        typer.Option("--currency", help="Only fiat currencies, comma-separated (USD,EUR)."),
    ] = None,
    cryptos: Annotated[
        str | None,
        typer.Option("--crypto", help="Only cryptocurrencies, comma-separated (BTC,ETH)."),
    ] = None,
    output_format: Annotated[
        OutputFormat | None,
        typer.Option("--format", "-f", help="Output format: table or json."),
    ] = None,
    web: Annotated[
        bool,
        typer.Option("--web", "-w", help="Open provider source pages in your browser."),
    ] = False,
    no_color: Annotated[
        bool,
        typer.Option("--no-color", help="Disable colors (NO_COLOR is also honored)."),
    ] = False,
) -> None:
    """List supported assets and accepted aliases.

    Examples:
      chand list
      chand list --crypto BTC,ETH
      chand list --currency USD,EUR --format json
      chand list -w
    """

    fallback = output_format or OutputFormat.TABLE
    error_console = None
    try:
        settings = resolve_settings(output_format=output_format, no_color=no_color)
        fallback = settings.output_format
        assets = filtered_assets(currencies=currencies, cryptos=cryptos)
        error_console = make_console(stderr=True, no_color=settings.no_color)

        if settings.output_format is OutputFormat.JSON:
            if web:
                announce_provider_homepages(settings, console=error_console)
            write_json(assets_payload(assets))
            return

        console = make_console(no_color=settings.no_color)
        console.print(build_asset_table(assets))
        if web:
            open_provider_homepages(settings, console=error_console)
    except ChandError as exc:
        print_error(exc, fallback, console=error_console)
        raise typer.Exit(exc.exit_code) from None
    except KeyboardInterrupt:
        raise typer.Exit(130) from None
