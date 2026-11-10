# Chand

A fast, elegant CLI for live currency and cryptocurrency prices in Iranian Rial
and Toman.

Chand fetches free-market rates and crypto prices, falls back between providers
when one is blocked or rate-limited, and renders a clean terminal table or
stable JSON for scripts. It is built for the Iranian market context: the USD
rate is the cash/free-market rate, and every price can be shown in Rial or
Toman.

## Features

- Broad coverage: 49 fiat currencies and 35 cryptocurrencies, including
  Gulf, Central Asian, Caucasus, and major global markets
- Iranian-first fallback: Nobitex, Wallex, NerkhAra, TGJU, Bonbast, CoinGecko,
  and ExchangeRate-API
- Nobitex `apiv2` support with a legacy-domain mirror; TGJU bulk and profile
  parsing; Wallex and NerkhAra Toman rates
- Rial and Toman output with correct market conversion (`1 Toman = 10 Rial`)
- Rich colorized tables with 24-hour change and the source used for each price
- `--watch` live refresh and `-w` source-page opening in your browser
- Machine-readable JSON and newline-delimited JSON for scripts
- Short-lived disk cache with `--no-cache`; cache is bypassed during watch
- Shell completion, typed exit codes, and friendly typo suggestions
- No API keys required; an optional CoinGecko demo key raises rate limits

## Requirements

- Python 3.14+
- Internet access for live data
- [uv](https://docs.astral.sh/uv/) (recommended)

## Installation

```bash
git clone https://github.com/cmd-3324/Chand.git
cd Chand
uv sync
uv run chand --help
```

Install it as a global command:

```bash
uv tool install .
chand --version
```

`pip` works too:

```bash
python -m pip install -e .
chand --help
```

## Usage

```bash
# Quick table: BTC, ETH, USDT, USD, EUR, GBP, AED, TRY, CNY, JPY, CAD, XRP
chand

# Open the quick table's source pages
chand -w

# Supported assets, names, and aliases
chand list

# Quote one asset in Rial
chand price BTC --unit rial

# Quote several assets in Toman (default)
chand price BTC ETH USD EUR

# Select by kind, or quote everything
chand price --currency USD,EUR
chand price --crypto BTC,ETH
chand price --all

# Refresh every 5 seconds until Ctrl+C
chand price BTC --watch 5

# Open the source page for each result in your default browser
chand price BTC -w
chand price BTC ETH -w

# Machine-readable output
chand price BTC --format json
chand list --format json

# Cache maintenance
chand cache path
chand cache clear       # remove the quotes file only
chand cache purge       # confirm y/N, then remove the whole cache directory
chand cache purge --yes # skip the prompt for scripts
```

### Price options

| Flag | Meaning |
| --- | --- |
| `--unit, -u rial\|toman` | Output unit (default Toman) |
| `--format, -f table\|json` | Human table or machine JSON |
| `--watch N` | Refresh every N seconds (minimum 1) |
| `--all, -a` | Quote every supported asset |
| `--currency USD,EUR` | Select fiat currencies |
| `--crypto BTC,ETH` | Select cryptocurrencies |
| `--web, -w` | Open the source page for each result |
| `--no-cache` | Ignore and do not write cached quotes |
| `--timeout SECONDS` | Override the HTTP timeout |
| `--no-color` | Disable ANSI colors |

`list` accepts `--currency`, `--crypto`, `--format`, `--web`, and
`--no-color`.

### Selecting assets

- Positional symbols accept case-insensitive names and aliases: `btc`, `xbt`,
  `Dollar`, `us$`.
- Use either positional symbols, `--all`, or `--currency`/`--crypto`; mixing
  them is rejected so intent stays unambiguous.
- `--currency` and `--crypto` accept comma-separated values and validate the
  asset kind (`--currency BTC` fails with a helpful hint).

### Watch mode

`--watch N` re-fetches every `N` seconds (minimum 1), bypasses the cache, and
stops cleanly on Ctrl+C with exit code `130`.

With `--format json`, watch mode emits one compact JSON array per line
(NDJSON), which is easy to pipe into `jq` or another process.

### Opening source pages

`-w` / `--web` opens the page where the displayed value came from. Notes:

- One tab per selected asset, at most 10 at a time.
- `--watch -w` opens pages once, not on every refresh.
- In JSON mode Chand prints the URLs to stderr instead of opening tabs, keeping
  stdout clean for scripts.
- If no browser can be launched, Chand warns and still prints the prices.

## Output

### Table

```text
Chand - live prices
 Asset | Name      |  Price (Toman) |    24h | Source
-------+-----------+----------------+--------+-----------
 BTC   | Bitcoin   | 19,048,850,700 | -1.79% | CoinGecko
 USD   | US Dollar |        259,900 | -1.54% | TGJU
```

The caption shows the local update time, the USD/IRR rate used for conversion,
and the providers that answered.

### JSON

```json
[
  {
    "symbol": "BTC",
    "name": "Bitcoin",
    "kind": "crypto",
    "unit": "toman",
    "price": 19048850700,
    "price_irr": 190488507000,
    "price_toman": 19048850700,
    "price_usd": 73293.0,
    "change_24h": -1.7947,
    "source": "CoinGecko",
    "source_url": "https://www.coingecko.com/en/coins/bitcoin",
    "fetched_at": "2026-11-10T19:24:52.375127+00:00"
  }
]
```

- `price` follows `--unit`; `price_irr` and `price_toman` are always present.
- Large Rial/Toman values are JSON integers; small values such as SHIB or PEPE
  retain meaningful decimal precision. USD and percentage values are rounded
  JSON numbers.
- Fatal errors in JSON mode are written to stderr as
  `{"error": {"kind", "message", "hint", "exit_code"}}`.

## Configuration

Environment variables are optional; CLI flags win over environment values.

| Variable | Values | Default | Purpose |
| --- | --- | --- | --- |
| `CHAND_UNIT` | `rial`, `toman` | `toman` | Default output unit |
| `CHAND_FORMAT` | `table`, `json` | `table` | Default output format |
| `CHAND_TIMEOUT` | seconds | `10` | HTTP timeout |
| `CHAND_CACHE_TTL` | seconds | `30` | Quote cache lifetime; `0` disables |
| `CHAND_CACHE_DIR` | path | platform cache dir | Override the cache directory |
| `CHAND_WATCH` | seconds | `5` | Default interval used by `--watch` |
| `CHAND_PROVIDERS` | comma list | all | Provider order/enablement |
| `CHAND_COINGECKO_API_KEY` | string | unset | CoinGecko demo API key |
| `CHAND_NO_COLOR` | `1`, `true` | unset | Disable colors |
| `NO_COLOR` | any | unset | Standard no-color convention |

Available provider names: `nobitex`, `wallex`, `nerkhara`, `tgju`, `bonbast`,
`coingecko`, `erapi`. For example,
`CHAND_PROVIDERS=wallex,tgju,bonbast` restricts Chand to Iranian sources.

## Data sources and fallback

Default order:

1. **Nobitex** — crypto and USDT priced directly in Rial; uses `apiv2` first
   with the legacy API domain as a mirror.
2. **Wallex** — crypto markets priced directly in Toman, normalized to Rial.
3. **NerkhAra** — 44 fiat currencies and USDT in Toman from a compact JSON API.
4. **TGJU** — 49 fiat profiles in Rial; one bulk request for large selections,
   with per-profile fallback for currencies outside the bulk table.
5. **Bonbast** — 28 fiat currencies in Toman and Bitcoin in USD.
6. **CoinGecko** — broad crypto coverage in USD; converted with the market
   USD/IRR rate.
7. **ExchangeRate-API** — USD cross-rates as a final fiat fallback, including
   currencies not covered by Iranian sources.

TGJU quotes Japanese yen per 100 yen, Bonbast quotes it per 10 yen, and
NerkhAra quotes it per yen; providers normalize all of them to a single-yen
price. Toman sources are multiplied by 10 to store Rial internally.

Providers are queried in batches, failures are isolated, and each successful
quote records its source and source URL. Partial results are shown with
warnings on stderr. The cache avoids hammering public endpoints; `--watch`
intentionally bypasses it.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success (partial provider failures may still exit 0) |
| `2` | Usage error, unknown asset, invalid selection |
| `3` | Network failure |
| `4` | Provider/data failure, no usable prices |
| `5` | Invalid configuration |
| `6` | Browser failure (reserved; browser errors normally warn) |
| `130` | Interrupted with Ctrl+C |

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Project layout:

```text
src/chand/
  cli/         Typer app, commands, watch/live rendering
  core/        models, registry, config, HTTP, cache, pricing service
  providers/   one adapter per data source
  formatting/  units, Rich tables, JSON, browser helper
test/          offline provider, service, cache, browser, and CLI tests
```

All tests are offline: HTTP is mocked with recorded payloads, and the browser is
stubbed.

## Disclaimer

This project is for informational use only. Exchange rates and cryptocurrency
prices change rapidly and may differ between sources. Verify data with trusted
sources before making financial decisions.

## License

Under active development; no license has been finalized yet.
