"""Rich terminal rendering for price and asset tables."""

from __future__ import annotations

from collections.abc import Iterable

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from chand.core.models import Asset, PricingResult, Unit
from chand.formatting.units import format_amount, format_change, in_unit, unit_label


def make_console(*, stderr: bool = False, no_color: bool = False) -> Console:
    return Console(
        stderr=stderr,
        no_color=no_color,
        highlight=False,
        soft_wrap=False,
    )


def build_price_table(
    result: PricingResult,
    unit: Unit,
    *,
    title: str = "Chand - live prices",
) -> Table:
    table = Table(
        title=Text(title, style="bold"),
        title_justify="left",
        box=box.SIMPLE_HEAD,
        padding=(0, 1),
        expand=False,
    )
    table.add_column("Asset", style="bold cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column(f"Price ({unit_label(unit)})", justify="right", style="bold")
    table.add_column("24h", justify="right")
    table.add_column("Source", style="dim")

    for quote in result.quotes:
        change = quote.change_24h
        if change is None:
            change_text = Text("-", style="dim")
        else:
            style = "green" if change > 0 else "red" if change < 0 else "dim"
            change_text = Text(format_change(change), style=style)

        table.add_row(
            quote.asset.symbol,
            quote.asset.name,
            format_amount(quote.price_irr, unit),
            change_text,
            quote.source,
        )

    table.caption = _caption(result, unit)
    return table


def build_asset_table(assets: Iterable[Asset]) -> Table:
    table = Table(
        title=Text("Chand - supported assets", style="bold"),
        title_justify="left",
        box=box.SIMPLE_HEAD,
        padding=(0, 1),
    )
    table.add_column("Symbol", style="bold cyan", no_wrap=True)
    table.add_column("Name")
    table.add_column("Kind")
    table.add_column("Aliases", style="dim")
    for asset in assets:
        table.add_row(
            asset.symbol,
            asset.name,
            asset.kind.value,
            ", ".join(asset.aliases) or "-",
        )
    return table


def print_failures(result: PricingResult, console: Console) -> None:
    for failure in result.failures:
        text = Text.assemble(
            ("warning: ", "bold yellow"),
            (failure.symbol, "yellow"),
            (f" - {failure.message}", ""),
        )
        console.print(text)


def _caption(result: PricingResult, unit: Unit) -> Text:
    if not result.quotes:
        return Text("No prices available.", style="dim")

    updated = max(quote.fetched_at for quote in result.quotes).astimezone()
    sources = ", ".join(sorted({quote.source for quote in result.quotes}))
    parts: list[tuple[str, str]] = [
        ("Updated ", "dim"),
        (updated.strftime("%Y-%m-%d %H:%M:%S"), "dim"),
    ]
    if result.usd_irr is not None:
        parts.extend(
            [
                ("  |  1 USD = ", "dim"),
                (f"{in_unit(result.usd_irr, unit):,.0f} {unit_label(unit)}", "dim"),
            ]
        )
    if sources:
        parts.extend([("  |  ", "dim"), (sources, "dim")])
    return Text.assemble(*parts)
