# Phase 2 continuation

The implementation was copied from `F:\tradeedge-phase2` into this writable workspace,
`F:\tradeedge-codex`. The original directory is unchanged. Start both servers from
this workspace to use these changes; stop older instances on ports 3000/8000 first.

## Windows commands

Backend setup and start (PowerShell, from project root):

```powershell
python -m venv backend\.venv
backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python.exe -m unittest discover -s backend -v
cd backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend (separate terminal):

```powershell
cd F:\tradeedge-codex\frontend
npm.cmd ci
npm.cmd run build
npm.cmd run dev
```

## Changes and contracts

- `backend/sessions.json` supplies exchange-wide date overrides. NSE's calendar
  confirms 2026-11-08 Muhurat trading; the source URL is stored with that entry.
  No duration normalization or exact session hours are assumed.
- Weekday CSV candles are **assumed** regular by configuration, not checked against
  a complete exchange calendar. Unlisted weekends are unknown. Set
  `weekday_policy` to `unknown` for conservative operation and explicitly list
  verified regular sessions. Add special-session overrides as the calendar changes.
- Optional CSV `complete=false` excludes a candle from volume comparison.
  Future dates and today's regular candle before 15:30 India time are incomplete.
  Special sessions are incomparable regardless of completeness.
- `volume_ratio` is now nullable. `volume_comparable`, `volume_confirmed`,
  `volume_reason`, `volume_baseline_count`, session metadata and `complete` explain
  the result. The baseline uses the preceding 20 complete regular candles,
  excluding special/unknown/incomplete candles. No low-participation inference is
  made from incomparable volume. Zero-volume placeholders are excluded; duplicate
  dates (including placeholder duplicates) remain file errors.
- Pattern validity, price above buffered resistance, recent crossing and current
  volume confirmation are independent fields. A confirmed breakout also requires
  comparable confirming volume on its crossing candle and a crossing within five
  observations. Volume uses the unrounded ratio for decisions.
- Resistance uses left-shoulder historical highs. Pattern fitting excludes the
  signal candle, including from smoothing. These remain experimental heuristics.
- `GET /api/history/{symbol}` returns daily CSV candles and the same candidate
  used by the scanner. It accepts the scanner's lookback, volume_ratio and
  breakout_pct settings. Missing files return 404, malformed input/data 400.
- The historical scanner has its own selectable chart, neckline and date markers
  for start, trough, right shoulder and price crossing. No qualifying candidate
  means candles without pattern overlays. It is shown above clearly labeled demo
  components. Existing demo APIs, simulated fills and in-memory account remain.

## Validation and limitations

Unit tests cover regular/special/unknown/incomplete volume, baseline filtering,
zero-volume placeholders, duplicates, signal-candle leakage and real CSV loading.
All nine supplied CSV files scan without errors. No broker integration was added.

Validation: 10 backend tests, TypeScript checking, and the webpack production build
pass. Browser interaction/visual QA has not been run. Turbopack fails locally
while starting its CSS worker, including outside the sandbox; use
`npm.cmd run build -- --webpack` to run the alternative production build.

Daily CSV history is user supplied, not a live feed or independently verified market
data. Scores are shape heuristics, not probabilities. This is not a backtester;
historical annotations fitted as of the last candle must not be treated as signals
known at their earlier marker dates. Intraday feeds, a full verified calendar,
rejected-pattern diagnostics, backtesting and deployment dependency review remain
future work.
