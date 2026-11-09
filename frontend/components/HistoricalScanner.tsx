'use client';
import {useEffect,useRef,useState} from 'react';
import dynamic from 'next/dynamic';
import {api,type Candle} from '../lib/api';
import type {Pattern} from './PriceChart';
const PriceChart=dynamic(()=>import('./PriceChart'),{ssr:false});
type Result=Pattern&{symbol:string;status:string;score:number;close:number;volume_ratio:number|null;volume_comparable:boolean;volume_confirmed:boolean;volume_reason:string;session_label:string;date:string;pattern_valid:boolean;price_breakout:boolean;breakout_recent:boolean};
type Scan={source:string;scanned_files:number;symbols:string[];signals:Result[];errors:{file:string;error:string}[]};
type History={symbol:string;candles:({date:string;session_label:string;complete:boolean}&Omit<Candle,'time'>)[];pattern:Result|null};
export default function HistoricalScanner(){
 const [lookback,setLookback]=useState(120),[vol,setVol]=useState(1.5),[buffer,setBuffer]=useState(1),[data,setData]=useState<Scan|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const [selected,setSelected]=useState(''),[history,setHistory]=useState<History|null>(null),[chartError,setChartError]=useState('');
 const request=useRef(0);
 const [settings,setSettings]=useState({lookback:120,vol:1.5,buffer:1});
 async function scan(){setBusy(true);setError('');try{const result=await api<Scan>(`/api/scanner/rounding-bottom?lookback=${lookback}&volume_ratio=${vol}&breakout_pct=${buffer}`);setData(result);setSettings({lookback,vol,buffer});setSelected(s=>result.symbols.includes(s)?s:result.signals[0]?.symbol||result.symbols[0]||'')}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 useEffect(()=>{
  if(!selected)return;
  const id=++request.current;let active=true;setHistory(null);setChartError('');
  api<History>(`/api/history/${selected}?lookback=${settings.lookback}&volume_ratio=${settings.vol}&breakout_pct=${settings.buffer}`).then(h=>{if(active&&id===request.current)setHistory(h)}).catch(e=>{if(active)setChartError(e.message)});
  return ()=>{active=false};
 },[selected,settings]);
 const pattern=history?.pattern;
 return <section className="panel min-w-0"><h2 className="text-xl font-semibold mb-2">Historical CSV Rounding-Bottom Scanner</h2><p className="muted text-sm mb-4">Supplied daily OHLCV candles. Heuristic shape scores are not success probabilities. Historical chart selections do not change simulated paper fills.</p>
 <div className="flex flex-wrap gap-3 items-end mb-4"><label className="text-sm">Lookback sessions<br/><input className="field !w-28" type="number" min="60" max="250" value={lookback} onChange={e=>setLookback(Number(e.target.value))}/></label><label className="text-sm">Volume multiplier<br/><input className="field !w-28" type="number" step="0.1" min="1" max="5" value={vol} onChange={e=>setVol(Number(e.target.value))}/></label><label className="text-sm">Breakout buffer %<br/><input className="field !w-28" type="number" step="0.5" min="0" max="5" value={buffer} onChange={e=>setBuffer(Number(e.target.value))}/></label><button className="btn" disabled={busy} onClick={()=>void scan()}>{busy?'Scanning…':'Scan CSV files'}</button></div>
 {error&&<p role="alert" className="text-rose-300">{error}</p>}{data&&<><p className="muted text-sm mb-3">{data.scanned_files} files checked · {data.signals.length} qualifying patterns · {data.errors.length} file errors</p><div className="overflow-x-auto"><table><thead><tr><th>Symbol</th><th>Status</th><th>Shape score</th><th>Close</th><th>Resistance</th><th>Relative volume</th></tr></thead><tbody>{data.signals.map(s=><tr key={s.symbol}><td><button className="text-blue-300 underline" onClick={()=>setSelected(s.symbol)}>{s.symbol}</button></td><td>{s.status}</td><td>{s.score}/100</td><td>₹{s.close}</td><td>₹{s.resistance}</td><td title={s.volume_reason}>{s.volume_ratio===null?'N/A · '+s.session_label:s.volume_ratio+'×'}{!s.volume_comparable&&' · incomparable'}</td></tr>)}</tbody></table></div>{data.signals.length===0&&<p className="muted text-sm py-3">No qualifying patterns at these settings. You can still inspect each CSV below.</p>}{data.errors.map(e=><p key={e.file} className="text-rose-300 text-sm">{e.file}: {e.error}</p>)}
 <label className="block mt-5 mb-3">Historical daily chart <select aria-label="Historical symbol" className="field !w-auto ml-3" value={selected} onChange={e=>setSelected(e.target.value)}>{data.symbols.map(s=><option key={s}>{s}</option>)}</select></label>
 {chartError&&<p role="alert" className="text-rose-300">{chartError}</p>}{selected&&!history&&!chartError&&<p>Loading candles…</p>}
 {history&&<><p className="muted text-sm">{history.symbol} · User-provided CSV · Daily · Through {history.candles.at(-1)?.date} · {history.candles.at(-1)?.session_label}</p><PriceChart data={history.candles.map(c=>({...c,time:Date.parse(c.date+'T00:00:00Z')/1000}))} pattern={pattern}/>{pattern?<><p className="text-sm">{pattern.status} · Shape {pattern.score}/100 · Resistance ₹{pattern.resistance} · Price above buffered resistance: {pattern.price_breakout?'yes':'no'} · Recent crossing: {pattern.breakout_recent?'yes':'no'}</p><p className="muted text-sm">Volume: {pattern.volume_ratio===null?'N/A':pattern.volume_ratio+'×'} · {pattern.volume_reason} · Confirmed: {pattern.volume_confirmed?'yes':'no'}</p><p className="muted text-xs mt-2">Gold annotations: pattern start, trough, right shoulder, historical neckline, and price crossing when present. Crossings do not imply confirmed volume.</p></>:<p className="muted text-sm">No qualifying rounding-bottom pattern; no pattern annotations shown.</p>}</>}
 </>}
 </section>;
}
