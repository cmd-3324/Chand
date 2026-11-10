"""Static asset registry, alias resolution, and selector parsing."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from difflib import get_close_matches

from chand.core.models import Asset, AssetKind
from chand.errors import AssetNotFoundError, UsageError

ASSETS: tuple[Asset, ...] = (
    Asset("BTC", "Bitcoin", AssetKind.CRYPTO, ("XBT", "BITCOIN", "بیتکوین", "بیت کوین")),
    Asset("ETH", "Ethereum", AssetKind.CRYPTO, ("ETHER", "ETHEREUM", "اتریوم")),
    Asset("USDT", "Tether", AssetKind.CRYPTO, ("TETHER", "USD TETHER", "تتر")),
    Asset("USDC", "USD Coin", AssetKind.CRYPTO, ("USD COIN",)),
    Asset("XRP", "XRP", AssetKind.CRYPTO, ("RIPPLE", "ریپل")),
    Asset("BNB", "BNB", AssetKind.CRYPTO, ("BINANCE COIN", "بیانبی")),
    Asset("SOL", "Solana", AssetKind.CRYPTO, ("SOLANA", "سولانا")),
    Asset("DOGE", "Dogecoin", AssetKind.CRYPTO, ("DOGECOIN", "دوجکوین")),
    Asset("TRX", "TRON", AssetKind.CRYPTO, ("TRON", "ترون")),
    Asset("ADA", "Cardano", AssetKind.CRYPTO, ("CARDANO", "کاردانو")),
    Asset("TON", "Toncoin", AssetKind.CRYPTO, ("TONCOIN", "GRAM", "تون")),
    Asset("LINK", "Chainlink", AssetKind.CRYPTO, ("CHAINLINK", "لینک")),
    Asset("DOT", "Polkadot", AssetKind.CRYPTO, ("POLKADOT", "پولکادات", "دات")),
    Asset("POL", "Polygon", AssetKind.CRYPTO, ("MATIC", "POLYGON", "پالیگان", "ماتیک")),
    Asset("SHIB", "Shiba Inu", AssetKind.CRYPTO, ("SHIBA INU", "شیبا")),
    Asset("LTC", "Litecoin", AssetKind.CRYPTO, ("LITECOIN", "لایتکوین")),
    Asset("BCH", "Bitcoin Cash", AssetKind.CRYPTO, ("BITCOIN CASH", "بیتکوین کش")),
    Asset("XLM", "Stellar", AssetKind.CRYPTO, ("STELLAR", "استلار")),
    Asset("AVAX", "Avalanche", AssetKind.CRYPTO, ("AVALANCHE", "آوالانچ")),
    Asset("ATOM", "Cosmos", AssetKind.CRYPTO, ("COSMOS", "اتم")),
    Asset("NEAR", "NEAR Protocol", AssetKind.CRYPTO, ("NEAR PROTOCOL", "نیر")),
    Asset("PEPE", "Pepe", AssetKind.CRYPTO, ("PEPE", "پپه")),
    Asset("UNI", "Uniswap", AssetKind.CRYPTO, ("UNISWAP", "یونی")),
    Asset("ETC", "Ethereum Classic", AssetKind.CRYPTO, ("ETHEREUM CLASSIC",)),
    Asset("FIL", "Filecoin", AssetKind.CRYPTO, ("FILECOIN", "فایل")),
    Asset("APT", "Aptos", AssetKind.CRYPTO, ("APTOS", "آپتوس")),
    Asset("ARB", "Arbitrum", AssetKind.CRYPTO, ("ARBITRUM", "آربیتروم")),
    Asset("SUI", "Sui", AssetKind.CRYPTO, ("SUI NETWORK", "سویی")),
    Asset("SEI", "Sei", AssetKind.CRYPTO, ("SEI NETWORK", "سی")),
    Asset("AAVE", "Aave", AssetKind.CRYPTO, ("AAVE",)),
    Asset("XMR", "Monero", AssetKind.CRYPTO, ("MONERO", "مونرو")),
    Asset("ZEC", "Zcash", AssetKind.CRYPTO, ("ZCASH", "زی کش")),
    Asset("HBAR", "Hedera", AssetKind.CRYPTO, ("HEDERA", "هدرا")),
    Asset("ALGO", "Algorand", AssetKind.CRYPTO, ("ALGORAND", "الگورند")),
    Asset("RENDER", "Render", AssetKind.CRYPTO, ("RNDR", "رندر")),
    Asset("USD", "US Dollar", AssetKind.FIAT, ("DOLLAR", "US$", "USD$", "دلار")),
    Asset("EUR", "Euro", AssetKind.FIAT, ("EURO", "یورو")),
    Asset("GBP", "British Pound", AssetKind.FIAT, ("POUND", "STERLING", "پوند")),
    Asset("AED", "UAE Dirham", AssetKind.FIAT, ("DIRHAM", "درهم")),
    Asset("TRY", "Turkish Lira", AssetKind.FIAT, ("LIRA", "لیر")),
    Asset("CNY", "Chinese Yuan", AssetKind.FIAT, ("YUAN", "RMB", "یوان", "یوآن")),
    Asset("JPY", "Japanese Yen", AssetKind.FIAT, ("YEN", "ین")),
    Asset("CAD", "Canadian Dollar", AssetKind.FIAT, ("CANADIAN DOLLAR", "دلار کانادا")),
    Asset(
        "AUD",
        "Australian Dollar",
        AssetKind.FIAT,
        ("AUSTRALIAN DOLLAR", "دلار استرالیا"),
    ),
    Asset("CHF", "Swiss Franc", AssetKind.FIAT, ("SWISS FRANC", "فرانک")),
    Asset("SEK", "Swedish Krona", AssetKind.FIAT, ("SWEDISH KRONA", "کرون سوئد")),
    Asset(
        "NOK",
        "Norwegian Krone",
        AssetKind.FIAT,
        ("NORWEGIAN KRONE", "کرون نروژ"),
    ),
    Asset("DKK", "Danish Krone", AssetKind.FIAT, ("DANISH KRONE", "کرون دانمارک")),
    Asset("RUB", "Russian Ruble", AssetKind.FIAT, ("ROUBLE", "روبل")),
    Asset("INR", "Indian Rupee", AssetKind.FIAT, ("INDIAN RUPEE", "روپیه")),
    Asset(
        "PKR",
        "Pakistani Rupee",
        AssetKind.FIAT,
        ("PAKISTANI RUPEE", "روپیه پاکستان"),
    ),
    Asset("IQD", "Iraqi Dinar", AssetKind.FIAT, ("IRAQI DINAR", "دینار")),
    Asset("SYP", "Syrian Pound", AssetKind.FIAT, ("SYRIAN POUND", "پوند سوریه")),
    Asset("AFN", "Afghan Afghani", AssetKind.FIAT, ("AFGHANI", "افغانی")),
    Asset("LBP", "Lebanese Pound", AssetKind.FIAT, ("LEBANESE POUND", "پوند لبنان")),
    Asset("QAR", "Qatari Riyal", AssetKind.FIAT, ("QATARI RIYAL", "ریال قطر")),
    Asset("KWD", "Kuwaiti Dinar", AssetKind.FIAT, ("KUWAITI DINAR", "دینار کویت")),
    Asset("BHD", "Bahraini Dinar", AssetKind.FIAT, ("BAHRAINI DINAR", "دینار بحرین")),
    Asset("OMR", "Omani Rial", AssetKind.FIAT, ("OMANI RIAL", "ریال عمان")),
    Asset("JOD", "Jordanian Dinar", AssetKind.FIAT, ("JORDANIAN DINAR", "دینار اردن")),
    Asset("ILS", "Israeli Shekel", AssetKind.FIAT, ("SHEKEL", "شیکل")),
    Asset("SAR", "Saudi Riyal", AssetKind.FIAT, ("SAUDI RIYAL", "ریال سعودی")),
    Asset("THB", "Thai Baht", AssetKind.FIAT, ("THAI BAHT", "بات")),
    Asset(
        "MYR",
        "Malaysian Ringgit",
        AssetKind.FIAT,
        ("MALAYSIAN RINGGIT", "رینگیت"),
    ),
    Asset(
        "SGD",
        "Singapore Dollar",
        AssetKind.FIAT,
        ("SINGAPORE DOLLAR", "دلار سنگاپور"),
    ),
    Asset("HKD", "Hong Kong Dollar", AssetKind.FIAT, ("HONG KONG DOLLAR", "دلار هنگ کنگ")),
    Asset(
        "NZD",
        "New Zealand Dollar",
        AssetKind.FIAT,
        ("NEW ZEALAND DOLLAR", "دلار نیوزیلند"),
    ),
    Asset("ZAR", "South African Rand", AssetKind.FIAT, ("RAND", "رند")),
    Asset("BRL", "Brazilian Real", AssetKind.FIAT, ("BRAZILIAN REAL", "رئال")),
    Asset("MXN", "Mexican Peso", AssetKind.FIAT, ("MEXICAN PESO", "پزو")),
    Asset("KRW", "South Korean Won", AssetKind.FIAT, ("WON", "وون")),
    Asset("TWD", "New Taiwan Dollar", AssetKind.FIAT, ("TAIWAN DOLLAR", "دلار تایوان")),
    Asset("AZN", "Azerbaijani Manat", AssetKind.FIAT, ("AZERBAIJANI MANAT", "منات")),
    Asset("AMD", "Armenian Dram", AssetKind.FIAT, ("ARMENIAN DRAM", "درام")),
    Asset("GEL", "Georgian Lari", AssetKind.FIAT, ("GEORGIAN LARI", "لاری")),
    Asset("KGS", "Kyrgyzstani Som", AssetKind.FIAT, ("KYRGYZ SOM", "سوم")),
    Asset("TJS", "Tajikistani Somoni", AssetKind.FIAT, ("TAJIK SOMONI", "سامانی")),
    Asset("TMT", "Turkmenistani Manat", AssetKind.FIAT, ("TURKMEN MANAT", "منات ترکمنستان")),
    Asset("UZS", "Uzbekistani Som", AssetKind.FIAT, ("UZBEK SOM", "سوم ازبکستان")),
    Asset("BYN", "Belarusian Ruble", AssetKind.FIAT, ("BELARUSIAN RUBLE", "روبل بلاروس")),
    Asset("KZT", "Kazakhstani Tenge", AssetKind.FIAT, ("KAZAKH TENGE", "تنگه")),
    Asset("MNT", "Mongolian Tugrik", AssetKind.FIAT, ("MONGOLIAN TUGRIK", "توگریک")),
    Asset("IDR", "Indonesian Rupiah", AssetKind.FIAT, ("INDONESIAN RUPIAH", "روپیه اندونزی")),
    Asset("UAH", "Ukrainian Hryvnia", AssetKind.FIAT, ("UKRAINIAN HRYVNIA", "هریونیا")),
)

DEFAULT_QUICK: tuple[str, ...] = (
    "BTC",
    "ETH",
    "USDT",
    "USD",
    "EUR",
    "GBP",
    "AED",
    "TRY",
    "CNY",
    "JPY",
    "CAD",
    "XRP",
)

_BY_SYMBOL: dict[str, Asset] = {asset.symbol: asset for asset in ASSETS}
_ALIASES: dict[str, Asset] = {asset.symbol: asset for asset in ASSETS}
for _asset in ASSETS:
    for _alias in _asset.aliases:
        _ALIASES[_alias.upper()] = _asset


def normalize(value: str) -> str:
    return " ".join(value.strip().upper().split())


def resolve(symbol: str) -> Asset:
    """Resolve a user-supplied symbol or alias, with typo suggestions."""

    key = normalize(symbol)
    if not key:
        raise UsageError("Asset symbol cannot be empty.")
    asset = _ALIASES.get(key)
    if asset is not None:
        return asset

    candidates = get_close_matches(key, list(_ALIASES), n=3, cutoff=0.55)
    suggestion = f" Did you mean {', '.join(candidates)}?" if candidates else ""
    raise AssetNotFoundError(
        f"Unknown asset {symbol!r}.{suggestion}",
        hint="Run `chand list` to see supported assets.",
    )


def resolve_all(symbols: Iterable[str]) -> list[Asset]:
    """Resolve symbols in order, de-duplicating while preserving order."""

    seen: set[str] = set()
    result: list[Asset] = []
    for symbol in symbols:
        asset = resolve(symbol)
        if asset.symbol not in seen:
            seen.add(asset.symbol)
            result.append(asset)
    return result


def _split_filter(values: Sequence[str] | str | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = (values,)
    parts: list[str] = []
    for value in values:
        parts.extend(chunk.strip() for chunk in value.split(",") if chunk.strip())
    return parts


def filtered_assets(
    *,
    currencies: Sequence[str] | str | None = None,
    cryptos: Sequence[str] | str | None = None,
) -> list[Asset]:
    """Return assets matching the kind-specific selector flags."""

    selected: set[str] = set()
    if currencies:
        for symbol in _split_filter(currencies):
            asset = resolve(symbol)
            if asset.kind is not AssetKind.FIAT:
                raise UsageError(
                    f"{asset.symbol} is a cryptocurrency; use `--crypto {asset.symbol}` instead."
                )
            selected.add(asset.symbol)
    if cryptos:
        for symbol in _split_filter(cryptos):
            asset = resolve(symbol)
            if asset.kind is not AssetKind.CRYPTO:
                raise UsageError(
                    f"{asset.symbol} is a currency; use `--currency {asset.symbol}` instead."
                )
            selected.add(asset.symbol)

    if not currencies and not cryptos:
        return list(ASSETS)
    return [asset for asset in ASSETS if asset.symbol in selected]


def select_assets(
    symbols: Sequence[str] | None = None,
    *,
    all_assets: bool = False,
    currencies: Sequence[str] | str | None = None,
    cryptos: Sequence[str] | str | None = None,
) -> list[Asset]:
    """Combine positional symbols and selector flags into a final asset list."""

    explicit = list(symbols or ())
    has_filters = bool(_split_filter(currencies) or _split_filter(cryptos))

    if all_assets and explicit:
        raise UsageError("Pass either asset symbols or `--all`, not both.")
    if explicit and has_filters:
        raise UsageError("Pass either asset symbols or `--currency`/`--crypto`, not both.")

    if explicit:
        return resolve_all(explicit)
    if has_filters:
        return filtered_assets(currencies=currencies, cryptos=cryptos)
    if all_assets:
        return list(ASSETS)
    raise UsageError(
        "No assets selected.",
        hint="Pass symbols (for example `chand price BTC USD`) or use `--all`.",
    )
