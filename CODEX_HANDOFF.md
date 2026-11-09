# TradeEdge Phase 2 — Codex Project Handoff

## Project name
`tradeedge-phase2`

## Objective
Build a personal Indian-equity technical trading dashboard to identify rounding-bottom patterns, resistance breakouts, and potential setups across intraday, swing, and positional trading. Initial execution is **paper trading only**. Broker integration is undecided and must remain provider-independent.

## Current local environment
- Windows PowerShell
- Project root: `F:\tradeedge-phase2`
- Frontend: `F:\tradeedge-phase2\frontend` — Next.js, TypeScript, Tailwind; start with `npm.cmd install` and `npm.cmd run dev`.
- Backend: `F:\tradeedge-phase2\backend` — FastAPI; virtual environment `.venv`; start with `.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000`.
- UI: http://localhost:3000 ; API docs: http://127.0.0.1:8000/docs
- Python environment previously had trouble compiling PyYAML with `uvicorn[standard]`; use plain `uvicorn` unless a compatible binary is confirmed.

## Completed
1. Phase 1 local frontend/backend working with demo charts, demo scanner, and in-memory paper portfolio.
2. Phase 2 CSV historical scanner integrated separately from demo components.
3. Historical daily OHLCV CSV files loaded from `backend/data/` for nine NSE stocks: BHARTIARTL, HDFCBANK, ICICIBANK, INFY, ITC, JIOFIN, RELIANCE, SBIN, TCS.
4. CSV columns: `date,open,high,low,close,volume`.
5. Zero-volume placeholder rows were identified and excluded during cleaning; valid CSV scans now return zero file errors.
6. Scanner updated from one fixed window to multiple durations and richer structural checks. Statuses include Forming, Near breakout, Above resistance - unconfirmed, Breakout - volume unconfirmed, Confirmed breakout, and Rejected (internally).
7. Most recent UI displayed 9 files scanned, 5 qualifying structural candidates, 0 errors. Do not interpret these as validated trade signals.

## Existing backend scanner API and fields
`backend/scanner.py` exports:
- `load_csv(symbol)`
- `detect(rows, lookback=120, volume_ratio=1.5, breakout_pct=1.0)`
- `scan_all(lookback=120, volume_ratio=1.5, breakout_pct=1.0)`

`scan_all` returns a dictionary containing `source`, `scanned_files`, `signals`, `errors`, `disclaimer`.
Signal fields include `status`, `score`, `resistance`, `close`, `volume_ratio`, `distance_pct`, `depth_pct`, `shoulder_difference_pct`, `bottom_width_pct`, `date`, `lookback`, `pattern_start`, `pattern_bottom`, `pattern_end`, `rejection_reasons`, plus `symbol`.

The experimental algorithm smooths closing prices, seeks a central low, compares shoulders, checks depth, width, decline/recovery consistency, calculates approximate resistance from shoulder averages, and checks latest close and volume. **This is not a validated rounding-bottom detector.** Avoid claiming 90+ scores represent success probabilities.

## Critical current issue: shortened/special session
The latest RELIANCE CSV data shown:
```
2026-11-03,1287.9000244140625,1307.9000244140625,1282.0,1307.9000244140625,42319913
2026-11-04,1301.9000244140625,1318.9000244140625,1296.0,1311.0,19451679
2026-11-05,1324.0,1325.0,1303.699951171875,1313.4000244140625,19479324
2026-11-06,1295.0,1320.0,1295.0,1320.0,22768301
2026-11-08,1322.0999755859375,1324.9000244140625,1314.699951171875,1324.0,4171663
```
User reports November 8, 2026 was a shortened Muhurat trading session (~1–2 hours). **Verify against an authoritative exchange calendar before labeling the date.** Preserve real special-session candles. The current `relvol = last['volume'] / mean(previous_20_volumes)` yields ~0.20x for RELIANCE and similarly low values for others, which is not comparable with full-day volume. Do not label these as weak participation solely based on that comparison.

### Required fix
- Add session metadata (regular/special/unknown) from a verified calendar or configurable local metadata file.
- Keep the special-session price candle, but report `volume_comparable=false`, `volume_confirmed=false`, and `volume_ratio=null` (or separately show unadjusted raw ratio clearly labeled), unless time-normalized comparable data is available.
- Avoid using a hardcoded date as the permanent solution.
- Distinguish pattern validity, price breakout, and volume confirmation independently.
- Do not generate a 'Confirmed breakout' on incomparable volume.
- Add tests for special sessions, incomplete candles, zero-volume placeholders, duplicate dates, and normal sessions.

## Other issues to address
1. Main Pattern Scanner still shows `DEMO SIGNALS — NOT DETECTED` and simulated prices, distinct from the real CSV scanner. Replace or clearly isolate the demo after verification.
2. Current 'resistance' uses `max(left_shoulder_average, right_shoulder_average)`, which may yield prices far below the current close and falsely imply recent breakouts. Use historical swing highs/neckline with breakout-event timing, and check whether a breakout is recent.
3. Scanner scores 90+ are heuristic shape scores only; display this accurately.
4. Show why patterns are rejected, including near misses, without relaxing standards just to increase results.
5. Connect real CSV candles to a selectable historical chart with pattern start, trough, right shoulder, resistance, and breakout markers.
6. Backtest without look-ahead bias, include trading costs and slippage, and preserve paper-only execution.
7. For intraday, use an appropriate intraday data feed; current CSV is daily only.
8. Review `npm audit` findings (one moderate, one high reported) before public deployment; do not run `npm audit fix --force` blindly.

## Recommended next Codex task
Inspect the actual repository before editing. Implement a robust special-session-aware volume confirmation model, tests, and UI display of incomparable volume; then implement the real historical chart and pattern overlays. Preserve existing API compatibility. Do not connect to a broker or place live orders. Run available tests and report changes, assumptions, and remaining risks.

## Initial Codex prompt
> Work on the local repository `tradeedge-phase2`. Read `CODEX_HANDOFF.md` and inspect the actual files. Do not assume the handoff exactly matches the latest code. First identify the current API contracts and frontend scanner component. Then implement special-session-aware volume treatment, with verified or configurable session metadata and explicit volume comparability. Preserve paper-only execution. Add unit tests. After that, propose and implement real CSV chart integration with annotated rounding-bottom candidates. Show diffs and commands to run tests on Windows.
