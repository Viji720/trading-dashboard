import Link from 'next/link';
import MarketOverview from '../components/MarketOverview';

export default function Home() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <p className="text-sm font-medium uppercase tracking-widest text-cyan-300">TradeEdge Research</p>
      <h1 className="mt-3 text-4xl font-semibold text-slate-100">Indian F&amp;O Intelligence</h1>
      <MarketOverview />
      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <Link className="rounded-xl border border-slate-700 bg-slate-900 p-5 hover:border-cyan-400" href="/strategies">
          <h2 className="font-semibold">Daily Strategy Scans</h2>
          <p className="mt-2 text-sm text-slate-300">Find setups in completed daily candles.</p>
        </Link>
        <Link className="rounded-xl border border-slate-700 bg-slate-900 p-5 hover:border-cyan-400" href="/paper-trading">
          <h2 className="font-semibold">Paper Trading &amp; Historical Scanner</h2>
          <p className="mt-2 text-sm text-slate-300">Scan CSV history and place simulated orders.</p>
        </Link>
      </div>
    </main>
  );
}
