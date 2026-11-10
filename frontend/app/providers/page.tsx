'use client';

import { useEffect, useState, type FormEvent } from 'react';
import Link from 'next/link';
import { api } from '../../lib/api';

type Status = { configured: boolean; mode: 'session' | 'environment' | null };

export default function Providers() {
  const [status, setStatus] = useState<Status>();
  const [token, setToken] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api<Status>('/api/upstox/status').then(setStatus).catch(error => setError(error.message));
  }, []);

  async function configure(event?: FormEvent<HTMLFormElement>) {
    event?.preventDefault();
    setBusy(true);
    setError('');
    try {
      setStatus(await api<Status>(event ? '/api/upstox/connect' : '/api/upstox/disconnect', {
        method: 'POST',
        ...(event ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ token }) } : {}),
      }));
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setToken('');
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="text-3xl font-semibold">Provider Settings</h1>
      <p className="mt-3 text-slate-300">
        Generate a read-only Analytics Token in Upstox Developer Apps and paste it here. This local session keeps it in server memory until you disconnect or restart.
      </p>
      <p className="mt-4" role="status">{status?.configured ? `Upstox configured (${status.mode})` : status ? 'Upstox disconnected' : 'Checking configuration…'}</p>
      <form onSubmit={configure} className="my-5 flex flex-wrap items-end gap-3">
        <label className="grow">Upstox Analytics Token
          <input className="field mt-1 block w-full" type="password" autoComplete="off" value={token} onChange={event => setToken(event.target.value)} required maxLength={4096} />
        </label>
        <button className="rounded bg-cyan-300 px-4 py-2 font-semibold text-slate-950 disabled:opacity-60" disabled={busy}>{busy ? 'Checking…' : 'Test and connect'}</button>
      </form>
      {error && <p role="alert" className="text-red-300">{error}</p>}
      {status?.mode === 'session' && <button className="mr-4 underline" onClick={() => void configure()} disabled={busy}>Disconnect session token</button>}
      <Link className="text-cyan-300" href="/live">Open live market</Link>
    </main>
  );
}
