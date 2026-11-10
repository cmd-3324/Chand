"""Chand: live currency and crypto prices in Iranian Rial and Toman."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("chand")
except PackageNotFoundError:  # pragma: no cover - source tree without install
    __version__ = "0.1.0"


def main() -> None:
    """Compatibility entry point; prefer ``chand.cli.app:main``."""

    from chand.cli.app import main as cli_main

    cli_main()


__all__ = ["__version__", "main"]
