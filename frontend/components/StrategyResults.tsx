'use client';

import { useState } from 'react';
import { api } from '../lib/api';

type Scan = {
  scanned: number;
  matches: { symbol: string; date: string; close: number; finding: string }[];
  errors: { file: string; error: string }[];
};

export default function StrategyResults({ strategy }: { strategy: string }) {
  const [result, setResult] = useState<Scan>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  async function run() {
    setBusy(true);
    setError('');
    setResult(undefined);
    try {
      setResult(await api<Scan>(`/api/strategies/${strategy}`));
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <p className="text-slate-300">Uses completed daily candles from the local CSVs. Dates reflect the latest available candle for each stock.</p>
      {strategy === 'breakouts' && <p className="mt-2 text-slate-300">Available-history highs cover the loaded files. Listing-to-date coverage must be verified separately.</p>}
      <button className="my-5 rounded bg-cyan-300 px-4 py-2 font-semibold text-slate-950 disabled:opacity-60" onClick={run} disabled={busy}>
        {busy ? 'Scanning…' : 'Run scan'}
      </button>
      {error && <p role="alert" className="text-red-300">{error}</p>}
      {result && (
        <>
          <p role="status">{result.scanned} stocks scanned · {new Set(result.matches.map(row => row.symbol)).size} matched · {result.errors.length} file errors</p>
          {result.matches.length === 0 && <p className="mt-3 text-slate-300">No matching setups in the available data.</p>}
          {result.matches.length > 0 && <div className="mt-4 overflow-auto">
            <table className="w-full text-left text-sm">
              <thead><tr><th className="p-2">Symbol</th><th className="p-2">Candle date</th><th className="p-2">Close</th><th className="p-2">Evidence</th></tr></thead>
              <tbody>{result.matches.map(row => (
                <tr className="border-t border-slate-700" key={`${row.symbol}:${row.finding}`}>
                  <td className="p-2">{row.symbol}</td><td className="p-2">{row.date}</td>
                  <td className="p-2">₹{row.close.toFixed(2)}</td><td className="p-2">{row.finding}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>}
          {result.errors.length > 0 && <ul className="mt-4 text-red-300">{result.errors.map(row => <li key={row.file}>{row.file}: {row.error}</li>)}</ul>}
        </>
      )}
    </>
  );
}
