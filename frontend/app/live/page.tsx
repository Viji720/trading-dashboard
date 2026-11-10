'use client';

import { useState } from 'react';
import Link from 'next/link';
import { indiaTime, useMarketQuotes } from '../../lib/marketQuotes';

export default function LiveMarket() {
  const { snapshot, error } = useMarketQuotes();
  const [query, setQuery] = useState('');


  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <h1 className="text-3xl font-semibold">Live Market</h1>
      <p className="my-3 text-slate-300">Upstox quotes for NSE F&amp;O stock underlyings. Refreshes every 15 seconds. The last trade can predate the snapshot when a stock has not traded or the market is closed.</p>
      <Link className="text-cyan-300" href="/providers">Provider Settings</Link>
      {error && <p role="alert" className="my-3 text-red-300">{error}{snapshot && ' Showing the last successful snapshot.'}</p>}
      {!snapshot && !error && <p className="my-3">Requesting quotes…</p>}
      {snapshot && (
        <>
          <p className="my-4 text-sm">{snapshot.quotes.length}/{snapshot.requested} stocks · Snapshot {indiaTime.format(new Date(snapshot.fetched_at))} IST</p>
          <label>Filter symbols <input className="field ml-2" value={query} onChange={event => setQuery(event.target.value)} /></label>
          <div className="mt-4 overflow-auto">
            <table className="w-full text-left text-sm">
              <thead><tr><th className="p-2">Symbol</th><th className="p-2">Last price</th><th className="p-2">Change</th><th className="p-2">Volume</th><th className="p-2">Last trade (IST)</th></tr></thead>
              <tbody>{snapshot.quotes.filter(row => row.symbol.includes(query.trim().toUpperCase())).map(row => (
                <tr className="border-t border-slate-700" key={row.symbol}>
                  <td className="p-2">{row.symbol}</td><td className="p-2">₹{row.price.toFixed(2)}</td>
                  <td className="p-2">{row.previous_close && row.previous_close > 0 ? `${((row.price / row.previous_close - 1) * 100).toFixed(2)}%` : '—'}</td>
                  <td className="p-2">{row.volume?.toLocaleString('en-IN') ?? '—'}</td>
                  <td className="p-2">{row.last_trade ? indiaTime.format(new Date(row.last_trade)) : '—'}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        </>
      )}
    </main>
  );
}
