# TradeEdge F&O platform · Phase 1

## Current application and boundary

The existing Next.js app uses Lightweight Charts and a same-origin API proxy to a FastAPI monolith. It serves a deterministic simulated equity feed and in-memory paper account alongside a CSV-backed historical scanner. The scanner handles the two local NSE equity exports, but daily cash candles cannot supply futures basis, expired options, tick direction, depth or intraday evidence. Preserve those APIs and put their UI at /paper-trading. The root route introduces the F&O workspace and shows the provider prerequisite. There is no live feed or AI engine in Phase 1.

## Reference source and license audit

All six repositories were shallow-cloned and examined at the revisions below. Compatibility decisions apply to those revisions. Pin and audit dependencies and data terms before vendoring. No reference code was incorporated.

| Repository / revision | Source observations | Decision, destination and acceptance tests |
|---|---|---|
| [Bhav](https://github.com/rajmaurya0904/bhav/tree/562dc21) | MIT. bhav/data/upstox_client.py wraps HTTP and expired-contract requests. bhav/engine/bar_engine.py couples its reader, NSE calendar, resolver, cost model and portfolio. bhav/ai/validate.py implements an AST guard. Next.js backtest pages and report code exist. | Evaluate adapting the expired-instrument request handling into data/providers/upstox, retaining MIT notices. Update auth, request throttling, retry budgets and typed records. Test 401/429, pagination, timestamp conversion and expired instrument identifiers. Evaluate the engine behind an adapter only after next-bar execution, missing prices, expiry and costs pass golden tests. An AST guard alone is insufficient to run generated Python. |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents/tree/9fa1196) | Apache 2.0. tradingagents/graph/trading_graph.py orchestrates analysts and provider clients. propagation.py creates structured investment and risk debate state. CLI and graph/provider tests exist. | Reference the debate structure in agents/committee with independent evidence schemas and a deterministic risk veto. Avoid inheriting general-market feeds and a mandatory graph runtime. If source is adapted, preserve license and attribution, mark changes and carry any applicable NOTICE. Test disagreements, invalid outputs, timeout and veto. |
| [day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill/tree/3d0f4ef) | MIT. trader-risk/check.py and trader-broker/ticket.py are CLI scripts within Claude skills, with risk and ticket tests. They encode US session and execution assumptions. | Reference the separation of evidence, sizing and tickets. Implement India-specific risk independently under risk/ and keep broker execution out of the architecture. Test lot rounding, exposure, stale quotes and daily stops. |
| [indian-market-backtester](https://github.com/aayushsinha30/indian-market-backtester/tree/c950430) | No license file in the audited tree. indian_backtester/engine.py coordinates strategy and portfolio; charges.py has a fee configuration and calculator. The UI entry point is app.py. | No redistribution permission established. Build independent charges and fills under risk/fees and backtesting/ using current official schedules and dated test cases. |
| [NSE-Options-Backtester](https://github.com/VaibhavYDev/NSE-Options-Backtester/tree/a002ed7) | MIT. core/data_loader.py maps and normalizes columns with Pandas/NumPy. strategies/multi_leg.py builds bull call and bear put spreads using core/backtester.py legs. UI is Streamlit. | Consider adapting alias handling and leg models under data/normalization and backtesting/options, retaining MIT notices. Use exact contract identities, synchronized quotes, adverse-side fills and expiry settlement. Test missing legs, stale quotes and spread payoff at expiry. |
| [VectorBT](https://github.com/polakowo/vectorbt/tree/07f5e85) | Apache 2.0 with Commons Clause at this revision. portfolio/base.py and portfolio/nb.py implement array and Numba simulation with extensive tests. | Exclude from distributed baseline pending review of the restriction on selling software or substantially derived services. Use independently written NumPy/Pandas parameter sweeps and an event simulator where contract execution matters. Check parity against hand-worked fill and metric fixtures. |

## Proposed modular monolith

Keep Next.js and FastAPI. Mount new endpoints under /api/fno/v1 and keep the existing equity demo separate. A bounded background worker ingests provider data and runs scheduled scans. PostgreSQL holds authoritative records, TimescaleDB can partition market series, Parquet holds licensed research snapshots and Redis can cache quotes and coordinate work. The browser talks only to FastAPI. Provider and Claude credentials remain server side. No order endpoints for broker execution.

Data flow: approved read-only broker adapter → timestamped raw snapshot → validation and normalization → contract universe and bar storage → deterministic features → scan and confluence → risk veto → Claude interpretation → recommendation journal. An expired or incomplete snapshot cannot authorize a recommendation. Claude may explain evidence but cannot change calculations, choose fill prices or bypass risk checks.

Proposed schema, subject to migration review in Phase 2:

| Record | Identity and contents |
|---|---|
| universe_snapshot / contract | Provider, fetched time and checksum; effective-from/to contract version with exchange, underlying, type, strike, expiry, lot and tick size. Store provider tokens as mappings. |
| candle / quote / chain_snapshot | Contract, provider and event time; interval where applicable, ingestion time, units, completeness and provenance. Keep exchange timestamps alongside normalized UTC. |
| scan_run / evidence | Universe and market snapshot IDs, strategy/version, timeframe, direction, reason, quality and freshness. Persist conflicts and missing evidence. |
| recommendation / paper_fill | Evidence and risk snapshot IDs, strategy version, trigger, invalidation, charges, simulated fill and outcome. Journal abstentions as well. |
| risk_policy / audit_event | Effective dated settings, actor, action and redacted metadata. Never log credentials. |

Provider adapter capabilities are explicit: instruments, historical candles, quotes, depth, stream and option chain. Unsupported capabilities return an unavailable status. Treat depth snapshots and aggressor-classified trades as different inputs. Use provider entitlement and exchange redistribution terms as a release gate. Store session-aware bar boundaries and retain point-in-time universes for backtests.

## External dependencies and operating estimate

- [DhanHQ Data API](https://dhan.co/support/platforms/dhanhq-api/how-to-access-dhan-api/) lists ₹499 plus tax per month. Verify segment coverage, expired history and contract master fields with an authenticated account.
- [Kite Connect](https://www.zerodha.com/products/api/) lists ₹500/month for realtime streaming and historical candles. Check how chain snapshots can be assembled and confirm expired-options availability before selection.
- [Upstox option chain](https://upstox.com/developer/api-documentation/get-pc-option-chain/) documents quotes, OI and Greeks. [Expired contracts](https://upstox.com/developer/api-documentation/announcements/expired-instruments-api/) require Plus. Confirm current entitlement and price in the account before budgeting. This is the first adapter candidate because the documented chain and expired-contract endpoints cover two hard requirements.
- [FYERS API](https://fyers.in/products/api) lists free standard API access with Prime for extended limits. Verify options coverage, historical retention and full-universe streaming caps.
- [Claude Sonnet 5](https://www.anthropic.com/news/claude-sonnet-5) lists $2 per million input and $10 per million output tokens. At 22 sessions and 20 shortlisted evaluations per session, with 12k input and 2k output tokens total per evaluation across agents, budget about $19.36/month at those rates before caching, retries and taxes. Measure actual usage and cap concurrency and spend. Run calculations on the full universe and reserve Claude calls for shortlisted setups.
- Local infrastructure needs no hosted service subscription. Hosted database, worker, backups and licensed redistribution are separate costs. Estimate them after measuring retention, bytes per instrument and connection counts. No paid services have been provisioned.

## Prioritized implementation checklist

| Priority / phase | Work and release check |
|---|---|
| P0 / 1 | Source audit, architecture and backlog; verify legacy and F&O entry routes and existing API proxy. |
| P0 / 2 | Provider capability interface, settings, Compose, migrations, authentication, role separation and audit. Verify clean startup and migrations from a blank database. |
| P0 / 3 | Integrate one entitled provider; synchronize NSE/BSE instrument snapshots, expiry and contract changes; expose admin status. Normalize bars, quotes and stream reconnects. Verify real read-only data, stale/missing detection and session boundaries. |
| P1 / 4 | Build timeframe aggregation, deterministic indicators, SMC, price action and quantitative features. Gate order flow on real inputs. Verify known values and no look-ahead in swing confirmation. |
| P1 / 5 | Implement option-chain analysis, expiry and spread checks, OI with price changes, IV/Greeks and futures basis. Verify synchronized inputs, units and missing legs. |
| P1 / 6 | Add evidence schemas, configurable confluence and specialist Claude agents with an optional read-only MCP boundary. Verify contradictory evidence, missing inputs and deterministic NO TRADE. |
| P1 / 7 | Add scheduled full-universe and scoped scans, explanations, ranking and watchlists. Load-test within broker limits and check every eligible symbol has a scan outcome. |
| P0 before recommendations / 8 | Deterministic risk, dated fee schedules, circuit breaker and journaled recommendation decisions. Test exposure, lot sizing, correlated risk, stale data and circuit-breaker resets. |
| P1 / 9 | Event replay, expired contracts, paper fills, walk-forward, sensitivity, Monte Carlo and out-of-sample reports. Prove point-in-time inputs, conservative fills and fee accounting before presenting results. |
| P1 / 10 | Finish overview, indices, scanner, instruments, options, SMC, order flow, recommendations, backtest, journal, analytics, risk, provider and admin screens. Verify responsive flows and publish API docs, setup, security guidance and runbook. |

Before Phase 3, confirm which account can provide read-only live and historical data, including the seven requested indices and NSE stock derivatives. Before external deployment, confirm redistribution rights and applicable exchange, broker and regulatory requirements with qualified reviewers.
