"""Read-only Upstox quote snapshots for the local dashboard."""

import gzip
import json
import os
import re
from datetime import datetime, timezone
from threading import Lock
from time import monotonic, time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Request as IncomingRequest
from pydantic import BaseModel, SecretStr

router = APIRouter(prefix="/api/upstox")
MASTER_URL = "https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"
QUOTE_URL = "https://api.upstox.com/{version}/market-quote/quotes"
LOCAL_ORIGINS = {"http://127.0.0.1:3000", "http://localhost:3000"}
lock = Lock()
session_token = None
quote_version = "v3"
master_cache = (0, {})
quote_cache = (0, None)


def equity_keys(instruments, now_ms):
    return {
        item["underlying_key"]: item["underlying_symbol"]
        for item in instruments
        if item.get("segment") == "NSE_FO"
        and item.get("underlying_type") == "EQUITY"
        and item.get("instrument_type") in {"FUT", "CE", "PE"}
        and item["expiry"] >= now_ms
        and item.get("underlying_key", "").startswith("NSE_EQ|")
    }


def universe():
    global master_cache
    expires, keys = master_cache
    if monotonic() >= expires:
        with urlopen(MASTER_URL, timeout=15) as response:
            keys = equity_keys(json.loads(gzip.decompress(response.read())), time() * 1000)
        if not keys:
            raise ValueError("Empty Upstox instrument master")
        master_cache = (monotonic() + 3600, keys)
    return keys


def request_quotes(token, keys, version):
    query = urlencode({"instrument_key": ",".join(keys)})
    url = f"{QUOTE_URL.format(version=version)}?{query}"
    request = Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json", "User-Agent": "TradeEdge/1.0"})
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.load(response)
        if payload.get("status") != "success" or not isinstance(payload.get("data"), dict):
            raise ValueError("Unexpected Upstox response")
        return payload["data"]
    except HTTPError as error:
        if error.code in (401, 403, 404):
            try:
                code = json.loads(error.read(4096))["errors"][0]["errorCode"]
            except (ValueError, KeyError, IndexError, TypeError, OSError):
                code = ""
            suffix = f" · {code}" if isinstance(code, str) and re.fullmatch(r"UDAPI[0-9]{4,8}", code) else ""
            raise HTTPException(
                error.code, f"Upstox Quotes {version.upper()} returned HTTP {error.code}{suffix}"
            ) from None
        if error.code == 429:
            raise HTTPException(429, "Upstox rate limit reached. Try again shortly.") from None
        raise HTTPException(502, f"Upstox quote request failed (HTTP {error.code})") from None
    except (URLError, OSError, ValueError):
        raise HTTPException(502, "Could not retrieve Upstox quotes") from None


def compatible_quotes(token, keys):
    global quote_version
    try:
        return request_quotes(token, keys, quote_version)
    except HTTPException as first:
        if quote_version != "v3" or first.status_code not in (401, 403, 404):
            raise
        try:
            result = request_quotes(token, keys, "v2")
        except HTTPException as second:
            if second.status_code not in (401, 403, 404):
                raise
            raise HTTPException(
                second.status_code,
                f"{first.detail}; {second.detail}. Check that the token is for production Upstox market data.",
            ) from None
        quote_version = "v2"
        return result


def active_token():
    return session_token or os.getenv("UPSTOX_ACCESS_TOKEN")


def local_settings(request):
    if request.headers.get("origin") not in LOCAL_ORIGINS:
        raise HTTPException(403, "Open the local dashboard to configure Upstox")


class Connection(BaseModel):
    token: SecretStr


@router.get("/status")
def status():
    return {"configured": bool(active_token()), "mode": "session" if session_token else "environment" if active_token() else None}


@router.post("/connect")
def connect(body: Connection, request: IncomingRequest):
    global session_token, quote_cache, quote_version
    local_settings(request)
    token = re.sub(r"^Bearer\s+", "", body.token.get_secret_value().strip(), flags=re.IGNORECASE)
    if not 16 <= len(token) <= 4096 or not token.isascii() or any(c.isspace() for c in token):
        raise HTTPException(400, "Enter a valid Upstox access token")
    with lock:
        try:
            keys = universe()
        except (OSError, ValueError, KeyError):
            raise HTTPException(502, "Could not load the Upstox instrument master") from None
        previous_version = quote_version
        quote_version = "v3"
        try:
            if not normalize_quotes(compatible_quotes(token, list(keys)[:1]), keys):
                raise HTTPException(502, "Upstox returned no usable quote for the connection test")
        except Exception:
            quote_version = previous_version
            raise
        session_token = token
        quote_cache = (0, None)
    return status()


@router.post("/disconnect")
def disconnect(request: IncomingRequest):
    global session_token, quote_cache, quote_version
    local_settings(request)
    with lock:
        session_token = None
        quote_version = "v3"
        quote_cache = (0, None)
    return status()


def normalize_quotes(raw, keys):
    quotes = []
    for item in raw.values():
        symbol = keys.get(item.get("instrument_token"))
        price = item.get("last_price")
        if not symbol or not isinstance(price, (int, float)) or not 0 < price < float("inf"):
            continue
        try:
            traded_at = datetime.fromtimestamp(int(item["last_trade_time"]) / 1000, timezone.utc)
            last_trade = traded_at.isoformat()
        except (KeyError, TypeError, ValueError, OverflowError, OSError):
            last_trade = None
        previous_close = item.get("prev_close_price")
        if previous_close is None and isinstance(item.get("net_change"), (int, float)):
            previous_close = price - item["net_change"]
        quotes.append({
            "symbol": symbol, "price": price, "last_trade": last_trade,
            "previous_close": previous_close, "volume": item.get("volume"),
        })
    return sorted(quotes, key=lambda quote: quote["symbol"])


@router.get("/quotes")
def quotes():
    global quote_cache
    with lock:
        token = active_token()
        if not token:
            raise HTTPException(503, "Connect Upstox in Provider Settings first")
        expires, snapshot = quote_cache
        if monotonic() < expires:
            return snapshot
        try:
            keys = universe()
        except (OSError, ValueError, KeyError):
            raise HTTPException(502, "Could not load the Upstox instrument master") from None
        raw = {}
        instruments = sorted(keys)
        for start in range(0, len(instruments), 250):
            raw.update(compatible_quotes(token, instruments[start:start + 250]))
        rows = normalize_quotes(raw, keys)
        if not rows:
            raise HTTPException(502, "Upstox returned no usable stock quotes")
        snapshot = {
            "source": f"Upstox Full Market Quotes {quote_version.upper()}", "requested": len(keys),
            "fetched_at": datetime.now(timezone.utc).isoformat(), "quotes": rows,
        }
        quote_cache = (monotonic() + 10, snapshot)
        return snapshot
