export const API=process.env.NEXT_PUBLIC_API_URL||'http://127.0.0.1:8000';
export async function api<T>(path:string,init?:RequestInit):Promise<T>{const res=await fetch(`${API}${path}`,{cache:'no-store',...init});const body=await res.json();if(!res.ok)throw new Error(body.detail||'Request failed');return body as T;}
export type Stock={symbol:string;name:string;price:number};
export type Candle={time:number;open:number;high:number;low:number;close:number;volume:number};
export type Signal={symbol:string;name:string;price:number;pattern:string;status:string;score:number;timeframe:string};
export type Account={cash:number;equity:number;starting_cash:number;holdings:{symbol:string;quantity:number;price:number}[];orders:{id:number;symbol:string;side:string;quantity:number;price:number;time:string;status:string}[]};
