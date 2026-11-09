# Phase 2: Historical rounding-bottom scanner (CSV-based starter)

This extends the Phase 1 project. **The existing Phase 1 charts, demo signals and paper fills remain synthetic.** The new *Historical CSV Rounding-Bottom Scanner* is separate and uses your supplied daily OHLCV data. No market-data provider or broker integration is included.

## Windows upgrade

1. Back up your existing `F:\tradeedge-phase1` folder, especially any local changes.
2. Extract this archive to a new directory, for example `F:\tradeedge-phase2`.
3. Copy any real historical CSV files into `F:\tradeedge-phase2\backend\data`.
4. Backend: `cd F:\tradeedge-phase2\backend`; create a new virtual environment if necessary with `py -3.12 -m venv .venv`; install `fastapi uvicorn pydantic` (no `uvicorn[standard]`); run `.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000`.
5. Frontend: `cd F:\tradeedge-phase2\frontend`; `npm.cmd install`; `npm.cmd run dev`.
6. Open `http://localhost:3000`, scroll to Historical CSV Rounding-Bottom Scanner, and click Scan CSV files.

## Data format

Place one CSV per symbol, e.g. `RELIANCE.csv` with header:

`date,open,high,low,close,volume`

Dates must be `YYYY-MM-DD`, with at least `lookback + 20` candles (140 at default settings). Values must be numeric, valid OHLC, and positive volume. Files must contain actual data obtained with appropriate permission; do not fabricate candles. Use consistently adjusted prices for corporate actions.

## Algorithm limitations

This is an experimental heuristic: center low in the middle half, shoulder difference <=15%, rounded-bottom depth >=6%, broad low zone, and resistance based on previous closes. It is **not** a validated trading strategy. A qualifying pattern is not proof of a profitable setup. Backtest with costs, slippage, corporate actions, and out-of-sample periods before use. The scanner uses only the latest window and excludes the latest candle from its resistance and baseline-volume calculations.

API: `GET /api/scanner/rounding-bottom?lookback=120&volume_ratio=1.5&breakout_pct=1.0`

**Not yet implemented:** automatic NSE data download, historical chart integration, paper fills based on actual CSV prices, intraday detection, database storage, alerts, or broker trading.
