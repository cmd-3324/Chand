# Chand

**Live currency and cryptocurrency prices, right from your terminal.**

Chand is a Python command-line tool in development for checking online market prices in Iranian Rial (IRR) and Toman. Its goal is to make exchange rates and crypto prices quick to look up, easy to compare, and pleasant to read—with clean, color-rich terminal output.

> **Status:** Chand is currently an early-stage project. The market-data commands and options shown below describe the intended interface and are not implemented yet. Prices and data sources will be documented here once available.

## Planned features

- Look up currency exchange rates and cryptocurrency prices online.
- Display amounts in Iranian Rial or Toman, with clear unit labels.
- Present results in readable, colorized terminal tables.
- Filter by asset, choose a display unit, and request machine-readable output.
- Show when quotes were retrieved so you can judge their freshness.

## Planned command-line interface

The following examples illustrate the intended interface; they are not yet functional:

```console
# Show available currencies and cryptocurrencies
chand list

# Look up selected assets, displayed in toman
chand price USD BTC --unit toman

# Request JSON output for scripts
chand price BTC --format json

# Refresh quotes periodically
chand price BTC --watch 5
```

The planned options include:

| Option | Purpose |
| --- | --- |
| `--unit rial\|toman` | Choose the display unit for Iranian currency values. |
| `--format table\|json` | Choose human-friendly or machine-readable output. |
| `--watch SECONDS` | Refresh the displayed quote at an interval. |
| `--help` | Show help for a command. |

Exact command names and flags may change as the project develops. Chand is intended for informational use; market quotes can change quickly and should not be treated as financial advice.

## Getting started

Chand requires Python 3.13 or newer. To run the current development scaffold from a clone:

```console
uv sync
uv run chand
```

At this stage, the command only prints a greeting; price lookup is not available yet.

## Development

Install dependencies and run the test suite with [uv](https://docs.astral.sh/uv/):

```console
uv sync
uv run pytest
```

## Contributing

Issues and pull requests are welcome. As the project takes shape, contributions around reliable data sources, clear Rial/Toman conversions, and accessible terminal output will be especially useful.

## Disclaimer

Exchange rates and cryptocurrency prices are volatile. Verify important figures with a trusted source before making financial decisions.
