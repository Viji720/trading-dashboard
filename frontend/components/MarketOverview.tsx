'use client';

import Link from 'next/link';
import { indiaTime, quoteChange, useMarketQuotes, type Quote } from '../lib/marketQuotes';

function Movers({ title, rows }: { title: string; rows: { quote: Quote; change: number }[] }) {
  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900 p-5">
      <h3 className="text-lg font-semibold">{title}</h3>
      {rows.length === 0 ? <p className="mt-3 text-sm text-slate-400">No matching moves in this snapshot.</p> : (
        <div className="mt-3 overflow-auto">
          <table className="w-full text-left text-sm">
            <thead><tr><th>Stock</th><th>Last price</th><th>Change</th><th>Last trade (IST)</th></tr></thead>
            <tbody>{rows.map(({ quote, change }) => (
              <tr key={quote.symbol}>
                <td>{quote.symbol}</td>
                <td>₹{quote.price.toFixed(2)}</td>
                <td className={change > 0 ? 'text-emerald-300' : 'text-rose-300'}>{change > 0 ? '+' : ''}{change.toFixed(2)}%</td>
                <td>{quote.last_trade ? indiaTime.format(new Date(quote.last_trade)) : '—'}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default function MarketOverview() {
  const { snapshot, error } = useMarketQuotes();
  const movers = (snapshot?.quotes ?? []).flatMap(quote => {
    const change = quoteChange(quote);
    return change === null ? [] : [{ quote, change }];
  }).sort((a, b) => b.change - a.change);
  const gainers = movers.filter(row => row.change > 0);
  const losers = movers.filter(row => row.change < 0);

  return (
    <section aria-labelledby="market-overview" className="mt-8">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 id="market-overview" className="text-xl font-semibold">NSE F&amp;O Stock Overview</h2>
        <Link className="text-cyan-300" href="/live">View all quotes</Link>
      </div>
      {error && <p role="alert" className="mt-3 text-rose-300">
        {error} {snapshot ? 'Showing the last successful snapshot.' : <Link className="underline" href="/providers">Provider Settings</Link>}
      </p>}
      {!snapshot && !error && <p role="status" className="mt-3 text-slate-300">Loading Upstox quotes…</p>}
      {snapshot && <>
        <p className="my-3 text-sm text-slate-300">
          {snapshot.quotes.length}/{snapshot.requested} stocks · {gainers.length} advancing · {losers.length} declining · {movers.length - gainers.length - losers.length} unchanged
        </p>
        <p className="mb-4 text-sm text-slate-400">
          {snapshot.source} · Snapshot {indiaTime.format(new Date(snapshot.fetched_at))} IST. Last trades may be from an earlier session.
        </p>
        <div className="grid gap-4 lg:grid-cols-2">
          <Movers title="Top gainers" rows={gainers.slice(0, 5)} />
          <Movers title="Top losers" rows={losers.slice(-5).reverse()} />
        </div>
      </>}
    </section>
  );
}
