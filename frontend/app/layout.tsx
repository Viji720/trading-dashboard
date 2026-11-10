import type { ReactNode } from 'react';
import Link from 'next/link';
import './globals.css';

export const metadata = {
  title: 'TradeEdge',
  description: 'Indian derivatives research and simulated paper trading',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <nav aria-label="TradeEdge screens" className="flex flex-wrap gap-5 border-b border-slate-800 px-6 py-3 text-sm text-cyan-300">
          <Link href="/">F&amp;O Intelligence</Link>
          <Link href="/live">Live Market</Link>
          <Link href="/strategies">Strategies</Link>
          <Link href="/providers">Provider Settings</Link>
          <Link href="/paper-trading">Paper Trading &amp; Historical Scanner</Link>
        </nav>
        {children}
      </body>
    </html>
  );
}
