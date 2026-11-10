"""Provider contract used by the pricing service."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence

from chand.core.http import HttpClient
from chand.core.models import Asset, ProviderQuote
from chand.errors import ProviderError


class Provider(ABC):
    """A source of one or more asset prices.

    Providers are batched: the service calls ``fetch`` once with every asset the
    provider supports, which keeps request counts low and respects rate limits.
    Implementations must either return quotes with a usable price or raise
    ``ProviderError``; partial results are allowed.
    """

    name: str
    priority: int
    homepage: str

    @abstractmethod
    def supports(self, asset: Asset) -> bool:
        """Return True when this provider can quote ``asset``."""

    @abstractmethod
    def fetch(
        self,
        assets: Sequence[Asset],
        client: HttpClient,
    ) -> dict[str, ProviderQuote]:
        """Fetch prices for ``assets`` keyed by canonical symbol."""

    def _error(self, message: str, *, hint: str | None = None) -> ProviderError:
        return ProviderError(message, provider=self.name, hint=hint)
