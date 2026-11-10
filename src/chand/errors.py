"""Typed errors and stable process exit codes for Chand."""

from __future__ import annotations


class ChandError(Exception):
    """Base class for all user-facing Chand errors.

    ``exit_code`` is part of the CLI contract and must stay stable.
    """

    exit_code: int = 1
    kind: str = "error"

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint

    def __str__(self) -> str:
        return self.message


class UsageError(ChandError):
    """Invalid command usage or asset selection."""

    exit_code = 2
    kind = "usage"


class AssetNotFoundError(UsageError):
    """A requested symbol is not in the registry."""

    kind = "asset"


class ConfigError(ChandError):
    """Invalid environment variable or configuration value."""

    exit_code = 5
    kind = "config"


class NetworkError(ChandError):
    """The network request could not be completed."""

    exit_code = 3
    kind = "network"


class ProviderError(ChandError):
    """A data provider failed, returned no data, or changed its format."""

    exit_code = 4
    kind = "provider"

    def __init__(
        self,
        message: str,
        *,
        provider: str | None = None,
        hint: str | None = None,
    ) -> None:
        super().__init__(message, hint=hint)
        self.provider = provider


class BrowserError(ChandError):
    """No usable browser could be launched."""

    exit_code = 6
    kind = "browser"
