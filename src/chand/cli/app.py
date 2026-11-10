"""Chand Typer application and command registration."""

from __future__ import annotations

from typing import Annotated

import typer

from chand import __version__
from chand.cli.commands.cache_cmd import cache_app
from chand.cli.commands.list_cmd import list_assets
from chand.cli.commands.price import price
from chand.cli.common import run_once
from chand.core.config import Settings
from chand.core.models import OutputFormat
from chand.core.registry import DEFAULT_QUICK, resolve_all
from chand.errors import ChandError
from chand.formatting.errors import print_error
from chand.formatting.table import make_console

app = typer.Typer(
    name="chand",
    help=(
        "Live currency and cryptocurrency prices in Iranian Rial and Toman.\n\n"
        "Run `chand price BTC` for a quote, `chand list` for supported assets, "
        "and `chand price BTC --watch 5` to keep refreshing."
    ),
    no_args_is_help=False,
    add_completion=True,
    rich_markup_mode="rich",
)

app.command("price", help="Quote assets as a table or JSON.")(price)
app.command("list", help="List supported assets and aliases.")(list_assets)
app.add_typer(cache_app, name="cache")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"chand {__version__}")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def root(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-V",
            callback=_version_callback,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
    web: Annotated[
        bool,
        typer.Option("--web", "-w", help="Open source pages for the quick table."),
    ] = False,
) -> None:
    if ctx.invoked_subcommand is None:
        _quick(web=web)


def _quick(*, web: bool) -> None:
    fallback = OutputFormat.TABLE
    error_console = None
    try:
        settings = Settings.from_env()
        fallback = settings.output_format
        assets = resolve_all(DEFAULT_QUICK)
        console = make_console(no_color=settings.no_color)
        error_console = make_console(stderr=True, no_color=settings.no_color)
        run_once(
            assets,
            settings,
            console=console,
            error_console=error_console,
            title="Chand - quick prices",
            web=web,
        )
    except ChandError as exc:
        print_error(exc, fallback, console=error_console)
        raise typer.Exit(exc.exit_code) from None
    except KeyboardInterrupt:
        raise typer.Exit(130) from None


def main() -> None:
    try:
        app(prog_name="chand")
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except BrokenPipeError:
        raise SystemExit(0) from None


if __name__ == "__main__":
    main()
