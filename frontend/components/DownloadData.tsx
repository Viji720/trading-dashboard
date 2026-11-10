'use client';

import { useEffect, useState } from 'react';
import { api } from '../lib/api';

type Download = {
  status: 'idle' | 'running' | 'complete' | 'error';
  total: number;
  downloaded: number;
  failed: string[];
  error: string | null;
};

const endpoint = '/api/scanner/download';

export default function DownloadData() {
  const [job, setJob] = useState<Download>();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');
  const running = job?.status === 'running';

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    async function poll() {
      try {
        const progress = await api<Download>(endpoint);
        if (!active) return;
        setJob(progress);
        setError('');
        if (progress.status === 'running') timer = setTimeout(poll, 2000);
      } catch (error) {
        if (!active) return;
        setError((error as Error).message);
        if (running) timer = setTimeout(poll, 4000);
      }
    }
    void poll();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [running]);

  async function start() {
    setStarting(true);
    setError('');
    try {
      setJob(await api<Download>(endpoint, { method: 'POST' }));
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setStarting(false);
    }
  }

  return (
    <>
      <button type="button" className="btn" disabled={starting || running} onClick={() => void start()}>
        {starting || running ? 'Downloading…' : 'Download Data'}
      </button>
      {running && <span role="status" className="muted text-sm">
        {job.total ? `${job.downloaded + job.failed.length}/${job.total} stocks processed` : 'Loading the NSE F&O stock list…'}
      </span>}
      {job?.status === 'complete' && <span role="status" className="text-sm">
        Downloaded {job.downloaded}/{job.total} stocks. {job.downloaded > 0 && 'Click Scan CSV files to use the updated data.'}
        {job.failed.length > 0 && ` Failed: ${job.failed.join(', ')}`}
      </span>}
      {(error || job?.error) && <span role="alert" className="text-sm text-rose-300">{error || job?.error}</span>}
    </>
  );
}
