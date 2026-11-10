"""Daily candle strategy rules for NSE equity history."""

from datetime import datetime
from statistics import mean
from typing import Literal
from zoneinfo import ZoneInfo

from fastapi import APIRouter

import scanner

Strategy = Literal[
    "rounding-bottom", "rounding-top", "doji-downtrend", "doji-uptrend",
    "consolidation-top", "consolidation-bottom", "dma-test", "breakouts",
]
router = APIRouter(prefix="/api/strategies")
INDIA = ZoneInfo("Asia/Kolkata")


def evaluate(strategy, rows):
    if not rows:
        return []
    latest = rows[-1]
    close = latest["close"]
    history = rows[:-1]

    if strategy in ("rounding-bottom", "rounding-top"):
        if strategy == "rounding-bottom":
            candidate = scanner.detect(rows)
            if candidate:
                return [f"{candidate['status']} · {candidate['lookback']} sessions"]
        elif len(history) >= 60:
            curve = scanner.smooth([row["close"] for row in history[-60:]])
            peak = max(range(len(curve)), key=curve.__getitem__)
            left, right = mean(curve[:8]), mean(curve[-8:])
            if 12 <= peak < 48 and curve[peak] >= 1.05 * max(left, right) and abs(left - right) <= 0.05 * max(left, right):
                neckline = min(left, right)
                status = "Below neckline" if close < neckline else "Rounded top forming"
                return [f"{status} · neckline ₹{neckline:.2f}"]
        return []

    if strategy.startswith("doji"):
        if len(history) < 20:
            return []
        span = latest["high"] - latest["low"]
        move = history[-1]["close"] / history[-20]["close"] - 1
        baseline = mean(row["close"] for row in history[-20:])
        prior_close = history[-1]["close"]
        trending = (move <= -0.05 and prior_close < baseline) if strategy == "doji-downtrend" else (move >= 0.05 and prior_close > baseline)
        if trending and span > 0 and abs(close - latest["open"]) <= 0.10 * span:
            return [f"Doji after {move:+.1%} prior 20-session move"]
        return []

    if strategy.startswith("consolidation"):
        if len(rows) < 60:
            return []
        recent, context = rows[-10:], rows[-60:-10]
        low, high = min(r["low"] for r in recent), max(r["high"] for r in recent)
        floor, ceiling = min(r["low"] for r in context), max(r["high"] for r in context)
        if ceiling <= floor or high / low - 1 > 0.05:
            return []
        edge = (low - floor) / (ceiling - floor) if strategy == "consolidation-top" else (high - floor) / (ceiling - floor)
        if (strategy == "consolidation-top" and edge >= 0.75) or (strategy == "consolidation-bottom" and edge <= 0.25):
            return [f"10-session range ₹{low:.2f}–₹{high:.2f} near prior range edge"]
        return []

    if strategy == "dma-test":
        hits = []
        for period in (50, 200):
            if len(history) >= period:
                average = mean(row["close"] for row in history[-period:])
                if latest["low"] <= average <= latest["high"] or abs(close / average - 1) <= 0.01:
                    hits.append(f"{period} DMA ₹{average:.2f} · close {close / average - 1:+.1%}")
        return hits

    hits = []
    if len(history) >= 252:
        year_high = max(row["high"] for row in history[-252:])
        if close > year_high:
            hits.append(f"52-week breakout · prior high ₹{year_high:.2f}")
        recorded_high = max(row["high"] for row in history)
        if close > recorded_high:
            hits.append(f"Available-history breakout · prior high ₹{recorded_high:.2f} since {history[0]['date']}")
    return hits


@router.get("/{strategy}")
def scan(strategy: Strategy):
    today = datetime.now(INDIA).date().isoformat()
    matches, errors, scanned = [], [], set()
    for file in sorted(scanner.DATA.glob("*.csv")):
        try:
            symbol = scanner.file_symbol(file)
            if symbol in scanned:
                continue
            rows = [row for row in scanner.load_csv(symbol) if row["date"] < today and row["complete"]]
            scanned.add(symbol)
            for finding in evaluate(strategy, rows):
                matches.append({"symbol": symbol, "date": rows[-1]["date"], "close": rows[-1]["close"], "finding": finding})
        except (OSError, ValueError, TypeError, KeyError) as error:
            errors.append({"file": file.name, "error": str(error)})
    return {"scanned": len(scanned), "matches": matches, "errors": errors}
