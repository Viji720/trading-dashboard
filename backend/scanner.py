
"""TradeEdge rounding-bottom research scanner."""

import csv
from pathlib import Path
from datetime import datetime
from statistics import mean
from math import isfinite

from sessions import volume_context

DATA = Path(__file__).parent / "data"


def load_csv(symbol):
    if not symbol.isalnum() or len(symbol) > 20:
        raise ValueError("Invalid symbol")

    path = DATA / f"{symbol.upper()}.csv"
    if not path.exists():
        raise FileNotFoundError(path.name)

    rows = []
    seen = set()

    with path.open(newline="", encoding="utf-8-sig") as f:
        for raw in csv.DictReader(f):
            day = datetime.strptime(
                raw["date"].strip(), "%Y-%m-%d"
            ).date()

            if day in seen:
                raise ValueError("Duplicate dates")
            seen.add(day)

            v = {
                k: float(raw[k])
                for k in ("open", "high", "low", "close", "volume")
            }

            if not all(isfinite(x) for x in v.values()):
                raise ValueError(f"Non-finite candle {day}")

            if v["volume"] == 0:
                continue  # provider placeholder, never a trading candle
            if (
                min(v["open"], v["high"], v["low"], v["close"]) <= 0
                or v["volume"] <= 0
                or v["low"] > min(v["open"], v["close"])
                or v["high"] < max(v["open"], v["close"])
                or v["high"] < v["low"]
            ):
                raise ValueError(f"Invalid candle {day}")

            rows.append({"date": day.isoformat(), **v, "complete": raw.get("complete", "true").strip().lower() not in ("false", "0", "no")})

    rows.sort(key=lambda x: x["date"])

    if len({r["date"] for r in rows}) != len(rows):
        raise ValueError("Duplicate dates")

    return rows


def smooth(values, width=5):
    radius = width // 2
    return [
        mean(values[max(0, i-radius):i+radius+1])
        for i in range(len(values))
    ]


def evaluate_window(rows, volume_ratio, breakout_pct):
    n = len(rows)
    closes = [r["close"] for r in rows]
    curve = smooth(closes[:-1])
    last = rows[-1]

    # Exclude the signal candle from pattern fitting.
    previous = curve
    m = len(previous)

    # Bottom should lie within the central 20%-80%.
    start = int(m * 0.20)
    end = int(m * 0.80)

    bottom_index = min(
        range(start, end),
        key=lambda i: previous[i]
    )

    shoulder_size = max(5, int(m * 0.12))

    left = mean(previous[:shoulder_size])
    right = mean(previous[-shoulder_size:])

    bottom = previous[bottom_index]

    reference = min(left, right)
    depth = (reference - bottom) / reference

    symmetry = abs(left - right) / max(left, right)

    # The left shoulder must decline into the bottom.
    left_section = previous[:bottom_index+1]

    # The right side must recover from the bottom.
    right_section = previous[bottom_index:]

    left_decline = (
        left_section[0] - left_section[-1]
    ) / left_section[0]

    right_recovery = (
        right_section[-1] - right_section[0]
    ) / right_section[0]

    # Broad-bottom test: number of observations
    # within 3% of the smoothed minimum.
    bottom_zone = sum(
        x <= bottom * 1.03 for x in previous
    )

    bottom_width = bottom_zone / m

    # Calculate the fraction of smoothed steps
    # following the expected trend on each side.
    left_steps = [
        left_section[i+1] <= left_section[i]
        for i in range(len(left_section)-1)
    ]

    right_steps = [
        right_section[i+1] >= right_section[i]
        for i in range(len(right_section)-1)
    ]

    left_consistency = mean(left_steps)
    right_consistency = mean(right_steps)

    # Structural requirements.
    reasons = []

    if depth < 0.05:
        reasons.append("Insufficient pattern depth")

    if symmetry > 0.25:
        reasons.append("Shoulders too asymmetric")

    if bottom_width < 0.08:
        reasons.append("Bottom too narrow")

    if bottom_width > 0.50:
        reasons.append("Bottom too flat or extended")

    if left_decline < 0.04:
        reasons.append("Weak left-side decline")

    if right_recovery < 0.04:
        reasons.append("Weak right-side recovery")

    if left_consistency < 0.50:
        reasons.append("Irregular left-side decline")

    if right_consistency < 0.50:
        reasons.append("Irregular right-side recovery")

    # Neckline is fixed from historical left-shoulder highs, before recovery.
    resistance = max(r["high"] for r in rows[:shoulder_size])
    volume = volume_context(rows, volume_ratio)
    threshold = resistance * (1 + breakout_pct / 100)
    crossings = [i for i in range(bottom_index + 1, n)
                 if rows[i]["close"] >= threshold and rows[i-1]["close"] < threshold]
    breakout_index = crossings[-1] if crossings else None
    recent = breakout_index is not None and n - 1 - breakout_index <= 5

    distance = (
        last["close"] / resistance - 1
    ) * 100

    # Structural quality score independent of volume.
    score = 100.0
    score -= min(30, symmetry * 100)
    score -= max(0, 10 - depth * 100) * 2
    score -= max(0, 0.65-left_consistency) * 25
    score -= max(0, 0.65-right_consistency) * 25

    if bottom_width < 0.12:
        score -= 10

    score = round(max(0, min(100, score)))

    valid = len(reasons) == 0

    confirmed = (
        valid
        and distance >= breakout_pct
        and recent
        and volume["volume_confirmed"]
        and volume_context(rows[:breakout_index+1], volume_ratio)["volume_confirmed"]
    )

    if not valid:
        status = "Rejected"

    elif confirmed:
        status = "Confirmed breakout"

    elif distance >= breakout_pct and not recent:
        status = "Above resistance - breakout not recent"

    elif distance >= breakout_pct:
        status = "Breakout - volume unconfirmed"

    elif distance >= 0:
        status = "Above resistance - unconfirmed"

    elif -3 <= distance < 0:
        status = "Near breakout"

    else:
        status = "Forming"

    return {
        "status": status,
        "score": score,
        "resistance": round(resistance, 2),
        "close": round(last["close"], 2),
        **volume,
        "pattern_valid": valid,
        "price_breakout": distance >= breakout_pct,
        "breakout_recent": recent,
        "breakout_date": rows[breakout_index]["date"] if breakout_index is not None else None,
        "right_shoulder": rows[-2]["date"],
        "distance_pct": round(distance, 2),
        "depth_pct": round(depth * 100, 2),
        "shoulder_difference_pct": round(symmetry * 100, 2),
        "bottom_width_pct": round(bottom_width * 100, 2),
        "date": last["date"],
        "lookback": n,
        "pattern_start": rows[0]["date"],
        "pattern_bottom": rows[bottom_index]["date"],
        "pattern_end": rows[-2]["date"],
        "rejection_reasons": reasons,
    }


def detect(rows, lookback=120,
           volume_ratio=1.5, breakout_pct=1.0):

    if not 60 <= lookback <= 250:
        raise ValueError("lookback must be 60-250")

    if volume_ratio <= 0:
        raise ValueError("volume_ratio must be positive")

    if not 0 <= breakout_pct <= 10:
        raise ValueError("breakout_pct must be 0-10")

    if len(rows) < lookback + 20:
        return None

    # Evaluate multiple durations up to the chosen maximum.
    durations = sorted(set([
        60, 80, 100, 120, 160, 200, lookback
    ]))

    candidates = []

    for duration in durations:
        if duration > lookback:
            continue

        candidate = evaluate_window(
            rows[-duration:],
            volume_ratio,
            breakout_pct
        )

        candidates.append(candidate)

    valid = [
        c for c in candidates
        if c["status"] != "Rejected"
    ]

    if not valid:
        return None

    # Prefer a confirmed breakout, then structural score.
    priority = {
        "Confirmed breakout": 5,
        "Breakout - volume unconfirmed": 4,
        "Above resistance - unconfirmed": 3,
        "Above resistance - breakout not recent": 3,
        "Near breakout": 2,
        "Forming": 1,
    }

    return max(
        valid,
        key=lambda c: (
            priority.get(c["status"], 0),
            c["score"],
            c["lookback"]
        )
    )


def scan_all(lookback=120,
             volume_ratio=1.5,
             breakout_pct=1.0):

    DATA.mkdir(exist_ok=True)

    signals = []
    errors = []

    files = sorted(DATA.glob("*.csv"))

    for file in files:
        try:
            rows = load_csv(file.stem)

            result = detect(
                rows, lookback,
                volume_ratio, breakout_pct
            )

            if result:
                signals.append({
                    "symbol": file.stem.upper(),
                    **result
                })

        except (
            ValueError, KeyError,
            FileNotFoundError, ZeroDivisionError
        ) as exc:
            errors.append({
                "file": file.name,
                "error": str(exc)
            })

    signals.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return {
        "source": "USER_PROVIDED_CSV",
        "scanned_files": len(files),
        "signals": signals,
        "symbols": [f.stem.upper() for f in files],
        "errors": errors,
        "disclaimer": (
            "Experimental heuristic signals. "
            "Not verified trading recommendations."
        )
    }
