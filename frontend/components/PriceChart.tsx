'use client';
import {useEffect,useRef} from 'react';
import {createChart,CandlestickSeries,ColorType,createSeriesMarkers,LineSeries,type SeriesMarker,type UTCTimestamp} from 'lightweight-charts';
type Candle={time:number;open:number;high:number;low:number;close:number};
export type Pattern={pattern_start:string;pattern_bottom:string;right_shoulder:string;breakout_date:string|null;resistance:number};
export default function PriceChart({data,pattern}:{data:Candle[];pattern?:Pattern|null}){
 const ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{
  if(!ref.current||!data.length)return;
  const chart=createChart(ref.current,{width:ref.current.clientWidth,height:360,layout:{background:{type:ColorType.Solid,color:'#111c2d'},textColor:'#a9b9d0'},grid:{vertLines:{color:'#1d2c42'},horzLines:{color:'#1d2c42'}},timeScale:{timeVisible:true}});
  const series=chart.addSeries(CandlestickSeries,{upColor:'#25c59a',downColor:'#f26b79',borderVisible:false,wickUpColor:'#25c59a',wickDownColor:'#f26b79'});
  series.setData(data.map(x=>({...x,time:x.time as UTCTimestamp})));
  if(pattern){
   const timestamp=(date:string)=>Math.floor(Date.parse(date+'T00:00:00Z')/1000) as UTCTimestamp;
   const points=[{date:pattern.pattern_start,text:'Pattern start'},{date:pattern.pattern_bottom,text:'Trough'},{date:pattern.right_shoulder,text:'Right shoulder'},...(pattern.breakout_date?[{date:pattern.breakout_date,text:'Price breakout'}]:[])];
   const markers:SeriesMarker<UTCTimestamp>[]=points.sort((a,b)=>a.date.localeCompare(b.date)).filter(p=>data.some(c=>c.time===timestamp(p.date))).map(p=>({time:timestamp(p.date),position:'aboveBar',shape:'arrowDown',color:'#fbbf24',text:p.text}));
   createSeriesMarkers(series,markers);
   const neckline=chart.addSeries(LineSeries,{color:'#fbbf24',lineWidth:2,priceLineVisible:false,lastValueVisible:false});
   neckline.setData([{time:timestamp(pattern.pattern_start),value:pattern.resistance},{time:data[data.length-1].time as UTCTimestamp,value:pattern.resistance}]);
  }
  chart.timeScale().fitContent();
  const observer=new ResizeObserver(()=>{if(ref.current)chart.applyOptions({width:ref.current.clientWidth})});observer.observe(ref.current);
  return ()=>{observer.disconnect();chart.remove()};
 },[data,pattern]);return <div ref={ref} className="w-full"/>;
}
