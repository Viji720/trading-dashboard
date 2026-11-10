# Upstox and daily strategy screens

For this local dashboard, open Provider Settings and paste a read-only
[Upstox Analytics Token](https://upstox.com/developer/api-documentation/analytics-token/).
A successful test replaces the session token. Disconnecting or restarting clears
that session token. For startup configuration, set UPSTOX_ACCESS_TOKEN in the
backend process environment. Keep this local development app on loopback.

Live Market uses the [Upstox Full Market Quotes V3 REST API](https://upstox.com/developer/api-documentation/get-full-market-quote-v3/)
and refreshes every 15 seconds while open. The server shares a 10-second quote
cache. Quote age is shown separately from the fetch time. Provider errors do not
generate substitute prices.

Strategies scan complete daily CSV candles through the last completed date.
Run the existing downloader to refresh the historical dataset.

| Strategy | Rule |
| --- | --- |
| Rounding bottom | Existing multi-window structural and volume rules. |
| Rounding top | Smoothed 60-session arch, peak inside the middle 60%, at least 5% above both shoulders, shoulders within 5%. The latest close is compared with the lower shoulder. |
| Doji after a downtrend or uptrend | Body at most 10% of candle range, with the previous close on the appropriate side of its 20-day mean and a prior move of at least 5% in the same direction. |
| Top or bottom consolidation | Ten-session high-to-low band no wider than 5%, entirely near the top or bottom quartile of the preceding 50-session range. |
| DMA test | Latest candle touches the prior 50- or 200-session mean, or closes within 1%. |
| Breakouts | Latest close above the high of the prior 252 sessions or above all earlier loaded highs. Available-history records display their coverage start date. A true listing-to-date record requires verified full coverage. |

The rules detect research setups. Quotes and daily candles are presented on
separate screens so intraday observations cannot masquerade as completed bars.
