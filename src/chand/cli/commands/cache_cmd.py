"""``chand cache`` maintenance commands."""

from __future__ import annotations

import typer

from chand.core.cache import PriceCache, default_cache_path

cache_app = typer.Typer(
    name="cache",
    help="Inspect or clear the local quote cache.",
    no_args_is_help=True,
)


@cache_app.command("clear")
def clear_cache() -> None:
    """Delete cached provider quotes."""

    path = default_cache_path()
    PriceCache(ttl=0, path=path).clear()
    typer.echo(f"Cleared {path}")


@cache_app.command("path")
def cache_path() -> None:
    """Print the cache file location."""

    typer.echo(str(default_cache_path()))
