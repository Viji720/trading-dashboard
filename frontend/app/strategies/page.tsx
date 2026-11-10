import Link from 'next/link';
import { strategies } from '../../lib/strategies';

export default function StrategyIndex() {
  return (
    <main className="mx-auto max-w-5xl px-6 py-10">
      <h1 className="text-3xl font-semibold">Daily Strategy Scans</h1>
      <p className="mt-3 text-slate-300">Scan completed daily candles from the local NSE stock history.</p>
      <ul className="mt-6 grid gap-3 sm:grid-cols-2">
        {Object.entries(strategies).map(([id, name]) => (
          <li key={id}><Link className="block rounded-lg border border-slate-700 p-4 hover:border-cyan-400" href={`/strategies/${id}`}>{name}</Link></li>
        ))}
      </ul>
    </main>
  );
}
