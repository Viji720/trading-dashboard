"""Refresh two years of daily NSE equity candles for the current stock F&O universe."""

import csv
import gzip
import json
from datetime import datetime
from math import isfinite
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen
from zoneinfo import ZoneInfo

import yfinance as yf

from scanner import DATA, valid_symbol

MASTER_URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
COLUMNS = ("Open", "High", "Low", "Close", "Volume")
INDIA = ZoneInfo("Asia/Kolkata")


def stock_universe():
    with urlopen(MASTER_URL, timeout=30) as response:
        instruments = json.loads(gzip.decompress(response.read()))

    now_ms = datetime.now(INDIA).timestamp() * 1000
    symbols = {
        item["underlying_symbol"]
        for item in instruments
        if item.get("segment") == "NSE_FO"
        and item.get("underlying_type") == "EQUITY"
        and item.get("instrument_type") in {"FUT", "CE", "PE"}
        and item["expiry"] >= now_ms
    }
    if not symbols or not all(valid_symbol(symbol) for symbol in symbols):
        raise ValueError("Instrument master returned an empty or invalid stock universe")
    return sorted(symbols)


def download_stock(symbol):
    history = yf.Ticker(f"{symbol}.NS").history(
        period="2y", interval="1d", auto_adjust=False, timeout=20
    )
    today = datetime.now(INDIA).date()
    rows = {}
    for timestamp, values in history.loc[:, list(COLUMNS)].iterrows():
        day = timestamp.date()
        if day >= today:
            continue
        opening, high, low, close, volume = map(float, values)
        if not all(isfinite(value) and value > 0 for value in (opening, high, low, close, volume)):
            continue
        if not low <= min(opening, close) <= max(opening, close) <= high:
            continue
        rows[day] = (opening, high, low, close, volume)
    if not rows:
        raise ValueError("No completed daily candles returned")

    path = DATA / f"{symbol}.csv"
    with NamedTemporaryFile(
        mode="w", dir=DATA, suffix=".tmp", newline="", encoding="utf-8", delete=False
    ) as handle:
        temporary = Path(handle.name)
        try:
            writer = csv.writer(handle)
            writer.writerow(("date", *(column.lower() for column in COLUMNS)))
            writer.writerows((day.isoformat(), *rows[day]) for day in sorted(rows))
            handle.close()
            temporary.replace(path)
        finally:
            handle.close()
            temporary.unlink(missing_ok=True)
    return len(rows)


def main():
    symbols = stock_universe()
    DATA.mkdir(exist_ok=True)
    print(f"Found {len(symbols)} eligible NSE F&O stocks", flush=True)
    failed = []
    for index, symbol in enumerate(symbols, start=1):
        try:
            print(f"[{index}/{len(symbols)}] {symbol}: {download_stock(symbol)} candles", flush=True)
        except Exception as error:
            failed.append(symbol)
            print(f"[{index}/{len(symbols)}] {symbol}: {error}", flush=True)
    print(f"Downloaded {len(symbols) - len(failed)}/{len(symbols)} stocks", flush=True)
    if failed:
        print("Failed: " + ", ".join(failed), flush=True)
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
