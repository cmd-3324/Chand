# Chand

A fast and elegant CLI for live currency and cryptocurrency prices in Iranian Rial and Toman.

Chand is a Python command-line tool designed for checking online exchange rates and crypto prices in real time, with a focus on Iranian market values. It aims to make currency data easy to read in the terminal using rich tables, colorized output, and simple flags for quick queries.

## Features

- Real-time currency and crypto price checks
- Support for Iranian Rial (IRR) and Toman display formats
- Clean, rich terminal output with readable tables and colors
- Simple command-line interface with useful flags
- Fast monitoring of price changes in a terminal-friendly layout
- Suitable for checking crypto and fiat prices in an Iranian context

## Example usage

```bash
# Show supported currencies and crypto assets
chand list

# Check a specific asset in rial
chand price BTC --unit rial

# Check a currency in toman
chand price USD --unit toman

# Show multiple assets at once
chand price BTC ETH USD EUR --unit toman

# Refresh prices automatically every few seconds
chand price BTC --watch 5

# Show output in JSON for scripts
chand price BTC --format json
```

## Planned flags

```bash
chand --help
chand price --help
```

Common options may include:

- `--unit rial|toman` — choose the output currency unit
- `--format table|json` — choose human-readable or machine-readable output
- `--watch <seconds>` — continuously refresh prices
- `--all` — show all supported markets
- `--currency <code>` — search or filter by currency
- `--crypto <symbol>` — search or filter by cryptocurrency
- `--help` — view available commands and usage

## Why Chand?

Many price-checking tools are web-based or cluttered with unnecessary interfaces. Chand focuses on a straightforward terminal experience for users who want quick, readable, and informative market values in the Iranian context.

## Requirements

- Python 3.13+
- Internet access for fetching live market data

## Installation

```bash
git clone https://github.com/cmd-3324/Chand.git
cd Chand
pip install -e .
```

## Run

```bash
chand
```

## Disclaimer

This project is intended for informational use only. Exchange rates and cryptocurrency prices can change rapidly, and the data should be verified through trusted sources before making financial decisions.

## License

This project is currently under active development.
