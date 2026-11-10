"""``chand cache`` maintenance commands."""

from __future__ import annotations

from typing import Annotated

import typer

from chand.core.cache import (
    PriceCache,
    cache_dir,
    default_cache_path,
)
from chand.core.cache import (
    purge_cache as purge_cache_data,
)
from chand.errors import ChandError

cache_app = typer.Typer(
    name="cache",
    help="Inspect, clear, or purge the local quote cache.",
    no_args_is_help=True,
)


@cache_app.command("clear")
def clear_cache() -> None:
    """Delete the cached provider quotes file only."""

    path = default_cache_path()
    PriceCache(ttl=0, path=path).clear()
    typer.echo(f"Cleared {path}")


@cache_app.command("purge")
def purge_cache(
    yes: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip the confirmation prompt."),
    ] = False,
) -> None:
    """Delete all Chand cache data for the current user.

    Shows the cache directory and asks for confirmation unless ``--yes`` is used.
    """

    directory = cache_dir()
    if not directory.exists():
        typer.echo(f"No cache data found at {directory}.")
        return

    if not yes:
        typer.echo(f"This removes all Chand cache data in:\n  {directory}")
        if not typer.confirm("Delete all cached quotes?", default=False):
            typer.echo("Aborted.")
            raise typer.Exit(1)

    try:
        purge_cache_data()
    except ChandError as exc:
        typer.echo(f"error: {exc.message}", err=True)
        if exc.hint:
            typer.echo(f"hint: {exc.hint}", err=True)
        raise typer.Exit(exc.exit_code) from None

    typer.echo(f"Purged {directory}")


@cache_app.command("path")
def cache_path() -> None:
    """Print the cache file location."""

    typer.echo(str(default_cache_path()))
