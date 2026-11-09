# TradeEdge Phase 1 — local paper trading demo

This is a runnable Next.js + FastAPI prototype for Indian stock dashboards. **Every price and scanner result is synthetic. No live exchange data or broker access.** No real trades can be placed.

## Requirements
- Node.js 20.9+ (Node.js 22 LTS recommended)
- Python 3.10+ (Python 3.12 recommended)
- Windows PowerShell or a compatible shell

## Run backend (PowerShell terminal 1)
```powershell
cd backend
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
Open http://127.0.0.1:8000/docs and http://127.0.0.1:8000/api/health

## Run frontend (PowerShell terminal 2)
```powershell
cd frontend
npm install
npm run dev
```
Open http://127.0.0.1:3000

If `py -3` is unavailable, use `python` to create the venv instead.

## Verify
1. Switch Intraday / Swing / Positional and see chart timeframe change.
2. Choose JIOFIN or another symbol; chart and price update.
3. Place a paper BUY for 1 share; cash and holdings change.
4. Place a paper SELL for 1 share; cash and holdings reverse.
5. Try selling without holdings; API refuses the order.
6. Reset account; balance returns to ₹100,000.

## Important limitations
- Mock data is deterministic and does not represent actual NSE/BSE prices.
- Pattern scanner statuses and scores are illustrative labels, not a real rounding-bottom algorithm.
- Orders fill immediately at the mock latest daily close; no order book, fees, slippage, risk controls, or exchange sessions.
- State is in Python memory; restart backend to reset orders and cash.
- Do not expose the API to the internet. It has no authentication.
- Future phases: PostgreSQL persistence, licensed data ingestion, pattern detection, backtesting, broker adapters, and security.
