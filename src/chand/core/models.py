"""Domain models shared by providers, services, and output renderers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum


class AssetKind(StrEnum):
    CRYPTO = "crypto"
    FIAT = "fiat"


class Unit(StrEnum):
    RIAL = "rial"
    TOMAN = "toman"


class OutputFormat(StrEnum):
    TABLE = "table"
    JSON = "json"


RIAL_PER_TOMAN = Decimal("10")


def utc_now() -> datetime:
    return datetime.now(UTC)


@dataclass(frozen=True, slots=True)
class Asset:
    """A tradable asset Chand can quote."""

    symbol: str
    name: str
    kind: AssetKind
    aliases: tuple[str, ...] = ()

    @property
    def is_crypto(self) -> bool:
        return self.kind is AssetKind.CRYPTO


@dataclass(frozen=True, slots=True)
class ProviderQuote:
    """A raw quote returned by a provider.

    At least one of ``price_irr`` or ``price_usd`` must be set. The service
    fills in the missing side using the USD/IRR market rate.
    """

    symbol: str
    price_irr: Decimal | None = None
    price_usd: Decimal | None = None
    change_24h: Decimal | None = None
    source: str = ""
    source_url: str = ""
    fetched_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class Quote:
    """A fully resolved price for one asset."""

    asset: Asset
    price_irr: Decimal
    price_usd: Decimal | None
    change_24h: Decimal | None
    source: str
    source_url: str
    fetched_at: datetime

    def price(self, unit: Unit) -> Decimal:
        if unit is Unit.RIAL:
            return self.price_irr
        return self.price_irr / RIAL_PER_TOMAN


@dataclass(frozen=True, slots=True)
class Failure:
    symbol: str
    message: str
    provider: str | None = None


@dataclass(slots=True)
class PricingResult:
    quotes: list[Quote]
    failures: list[Failure]
    usd_irr: Decimal | None

    @property
    def ok(self) -> bool:
        return bool(self.quotes)
