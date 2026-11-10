"""Consistent error rendering for table and JSON modes."""

from __future__ import annotations

import json
import sys

from rich.console import Console

from chand.core.models import OutputFormat
from chand.errors import ChandError


def print_error(
    error: ChandError,
    output_format: OutputFormat,
    *,
    console: Console | None = None,
) -> None:
    if output_format is OutputFormat.JSON:
        payload = {
            "error": {
                "kind": error.kind,
                "message": error.message,
                "hint": error.hint,
                "exit_code": error.exit_code,
            }
        }
        sys.stderr.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return

    target = console or Console(stderr=True, highlight=False)
    target.print(f"[bold red]error:[/] {error.message}")
    if error.hint:
        target.print(f"[dim]hint: {error.hint}[/]")
