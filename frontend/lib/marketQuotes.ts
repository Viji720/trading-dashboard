'use client';

import { useEffect, useState } from 'react';
import { api } from './api';

export type Quote = {
  symbol: string;
  price: number;
  previous_close: number | null;
  volume: number | null;
  last_trade: string | null;
};

type Snapshot = {
  source: string;
  fetched_at: string;
  requested: number;
  quotes: Quote[];
};

export const indiaTime = new Intl.DateTimeFormat('en-IN', {
  dateStyle: 'medium', timeStyle: 'medium', timeZone: 'Asia/Kolkata',
});

export function quoteChange(quote: Quote) {
  return quote.previous_close && quote.previous_close > 0
    ? (quote.price / quote.previous_close - 1) * 100
    : null;
}

export function useMarketQuotes() {
  const [snapshot, setSnapshot] = useState<Snapshot>();
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;

    async function refresh() {
      try {
        const data = await api<Snapshot>('/api/upstox/quotes');
        if (active) {
          setSnapshot(data);
          setError('');
        }
      } catch (error) {
        if (active) setError((error as Error).message);
      } finally {
        if (active) timer = setTimeout(refresh, 15000);
      }
    }

    void refresh();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, []);

  return { snapshot, error };
}
