from __future__ import annotations

import json

import pytest
import responses
from typer.testing import CliRunner

from chand.cli.app import app

runner = CliRunner()

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
TGJU_USD_URL = "https://www.tgju.org/profile/price_dollar_rl"

COINGECKO_PAYLOAD = {
    "bitcoin": {"usd": 74500.5, "usd_24h_change": -0.2},
    "ethereum": {"usd": 2080.25, "usd_24h_change": 1.4},
    "tether": {"usd": 0.999, "usd_24h_change": -0.01},
}

TGJU_HTML = """
<html><body>
<li id="l-price_dollar_rl" class=" low">
  <span class="info-value">
    <span class="info-price">2,629,000</span>
    <span class="info-change">(0.38%)</span>
  </span>
</li>
</body></html>
"""


def register_crypto_and_usd() -> None:
    responses.add(responses.GET, COINGECKO_URL, json=COINGECKO_PAYLOAD)
    responses.add(
        responses.GET,
        TGJU_USD_URL,
        body=TGJU_HTML,
        content_type="text/html; charset=utf-8",
    )


def combined_output(result) -> str:
    return result.output + getattr(result, "stderr", "")


def test_list_shows_supported_assets() -> None:
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "Bitcoin" in result.output
    assert "Tether" in result.output
    assert "BTC" in result.output


def test_list_json_is_machine_readable() -> None:
    result = runner.invoke(app, ["list", "--format", "json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0] == {
        "symbol": "BTC",
        "name": "Bitcoin",
        "kind": "crypto",
        "aliases": ["XBT", "BITCOIN"],
    }


def test_list_kind_filter() -> None:
    result = runner.invoke(app, ["list", "--currency", "USD,EUR", "--format", "json"])
    assert result.exit_code == 0
    assert [item["symbol"] for item in json.loads(result.stdout)] == ["USD", "EUR"]


@responses.activate
def test_price_json_with_conversion(monkeypatch) -> None:
    monkeypatch.setenv("CHAND_PROVIDERS", "coingecko,tgju")
    register_crypto_and_usd()

    result = runner.invoke(app, ["price", "BTC", "--format", "json"])

    assert result.exit_code == 0, combined_output(result)
    payload = json.loads(result.stdout)
    assert len(payload) == 1
    entry = payload[0]
    assert entry["symbol"] == "BTC"
    assert entry["unit"] == "toman"
    assert entry["price_usd"] == 74500.5
    assert entry["price_irr"] == 195861814500
    assert entry["price_toman"] == 19586181450
    assert entry["source"] == "CoinGecko"
    assert entry["source_url"] == "https://www.coingecko.com/en/coins/bitcoin"


@responses.activate
def test_price_table_and_rial_unit(monkeypatch) -> None:
    monkeypatch.setenv("CHAND_PROVIDERS", "coingecko,tgju")
    register_crypto_and_usd()

    result = runner.invoke(app, ["price", "BTC", "--unit", "rial"])

    assert result.exit_code == 0, combined_output(result)
    assert "Bitcoin" in result.output
    assert "CoinGecko" in result.output
    assert "195,861,814,500" in result.output


@responses.activate
def test_web_flag_opens_source_page(monkeypatch) -> None:
    monkeypatch.setenv("CHAND_PROVIDERS", "coingecko,tgju")
    register_crypto_and_usd()
    opened: list[str] = []

    def fake_open(url, new=0, autoraise=True):
        opened.append(url)
        return True

    monkeypatch.setattr("chand.formatting.browser.webbrowser.open", fake_open)
    result = runner.invoke(app, ["price", "BTC", "-w"])

    assert result.exit_code == 0, combined_output(result)
    assert opened == ["https://www.coingecko.com/en/coins/bitcoin"]


@responses.activate
def test_web_flag_in_json_mode_prints_urls(monkeypatch) -> None:
    monkeypatch.setenv("CHAND_PROVIDERS", "coingecko,tgju")
    register_crypto_and_usd()
    opened: list[str] = []
    monkeypatch.setattr(
        "chand.formatting.browser.webbrowser.open",
        lambda url, new=0, autoraise=True: opened.append(url) or True,
    )

    result = runner.invoke(app, ["price", "BTC", "-w", "--format", "json"])

    assert result.exit_code == 0, combined_output(result)
    assert opened == []
    assert "https://www.coingecko.com/en/coins/bitcoin" in result.stderr
    json.loads(result.stdout)


def test_unknown_asset_exits_with_usage_code() -> None:
    result = runner.invoke(app, ["price", "BTCC"])
    assert result.exit_code == 2
    assert "Unknown asset" in combined_output(result)


def test_no_provider_for_asset_exits_with_provider_code(monkeypatch) -> None:
    monkeypatch.setenv("CHAND_PROVIDERS", "coingecko")
    result = runner.invoke(app, ["price", "USD"])
    assert result.exit_code == 4
    assert "No prices" in combined_output(result)


def test_json_error_payload_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("CHAND_PROVIDERS", "coingecko")
    monkeypatch.setenv("CHAND_FORMAT", "json")
    result = runner.invoke(app, ["price", "USD"])
    assert result.exit_code == 4
    payload = json.loads(result.stderr)
    assert payload["error"]["kind"] == "provider"
    assert payload["error"]["exit_code"] == 4


@responses.activate
def test_bare_command_shows_quick_prices(monkeypatch) -> None:
    monkeypatch.setenv("CHAND_PROVIDERS", "coingecko,tgju")
    register_crypto_and_usd()

    result = runner.invoke(app, [])

    assert result.exit_code == 0, combined_output(result)
    assert "quick prices" in result.output
    assert "Bitcoin" in result.output


@responses.activate
def test_bare_web_flag_opens_quick_sources(monkeypatch) -> None:
    monkeypatch.setenv("CHAND_PROVIDERS", "coingecko,tgju")
    register_crypto_and_usd()
    opened: list[str] = []
    monkeypatch.setattr(
        "chand.formatting.browser.webbrowser.open",
        lambda url, new=0, autoraise=True: opened.append(url) or True,
    )

    result = runner.invoke(app, ["-w"])

    assert result.exit_code == 0, combined_output(result)
    assert "https://www.coingecko.com/en/coins/bitcoin" in opened
    assert "https://www.tgju.org/profile/price_dollar_rl" in opened


@responses.activate
def test_json_watch_emits_ndjson_and_exits_on_interrupt(monkeypatch) -> None:
    monkeypatch.setenv("CHAND_PROVIDERS", "coingecko,tgju")
    register_crypto_and_usd()
    monkeypatch.setattr(
        "chand.cli.common.time.sleep",
        lambda _seconds: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    result = runner.invoke(app, ["price", "BTC", "--watch", "1", "--format", "json"])

    assert result.exit_code == 130, combined_output(result)
    first_line = result.stdout.strip().splitlines()[0]
    payload = json.loads(first_line)
    assert payload[0]["symbol"] == "BTC"


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.output.startswith("chand ")


def test_cache_commands() -> None:
    path_result = runner.invoke(app, ["cache", "path"])
    assert path_result.exit_code == 0
    assert path_result.output.strip().endswith("quotes.json")

    clear_result = runner.invoke(app, ["cache", "clear"])
    assert clear_result.exit_code == 0
    assert "Cleared" in clear_result.output


@pytest.mark.parametrize("args", [["price", "BTC", "--watch", "0.5"]])
def test_watch_minimum_validation(args: list[str]) -> None:
    result = runner.invoke(app, args)
    assert result.exit_code == 2
