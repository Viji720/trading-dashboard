from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
from math import sin, cos
from typing import Literal

app = FastAPI(title='TradeEdge Paper API', version='0.1.0')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000','http://127.0.0.1:3000'], allow_methods=['*'], allow_headers=['*'])
STOCKS = [
 {'symbol':'RELIANCE','name':'Reliance Industries','base':1460},
 {'symbol':'TCS','name':'Tata Consultancy Services','base':3180},
 {'symbol':'INFY','name':'Infosys','base':1560},
 {'symbol':'HDFCBANK','name':'HDFC Bank','base':960},
 {'symbol':'ICICIBANK','name':'ICICI Bank','base':1310},
 {'symbol':'SBIN','name':'State Bank of India','base':860},
 {'symbol':'JIOFIN','name':'Jio Financial Services','base':220},
 {'symbol':'TATAMOTORS','name':'Tata Motors','base':690},
]
accounts = {'cash': 100000.0, 'initial_cash':100000.0, 'positions':{}, 'orders':[]}

def candles(symbol: str, timeframe: str):
    stock = next((s for s in STOCKS if s['symbol']==symbol),None)
    if not stock: raise HTTPException(404,'Unknown symbol')
    if timeframe not in ('15m','1h','1d','1w'): raise HTTPException(400,'Unsupported timeframe')
    count=120
    now=datetime(2026,11,6,15,30,tzinfo=timezone(timedelta(hours=5,minutes=30)))
    delta={'15m':timedelta(minutes=15),'1h':timedelta(hours=1),'1d':timedelta(days=1),'1w':timedelta(weeks=1)}[timeframe]
    result=[]
    for i in range(count):
        # Deterministic synthetic U-shaped trend with oscillations; NOT historical market data.
        x=(i-60)/60
        center=stock['base']*(0.88+0.13*x*x+0.014*sin(i*0.31)+0.006*cos(i*0.11))
        op=center*(1+0.002*sin(i*0.91)); close=center*(1+0.003*cos(i*0.57))
        hi=max(op,close)*1.006; lo=min(op,close)*0.994
        ts=now-(count-1-i)*delta
        result.append({'time':int(ts.timestamp()),'open':round(op,2),'high':round(hi,2),'low':round(lo,2),'close':round(close,2),'volume':int(100000*(1+0.4*abs(sin(i*0.23))))})
    return result

@app.get('/api/health')
def health(): return {'status':'ok','mode':'SIMULATED_PAPER_ONLY'}

@app.get('/api/stocks')
def stocks():
    return [{**{k:v for k,v in s.items() if k!='base'}, 'price':candles(s['symbol'],'1d')[-1]['close']} for s in STOCKS]

@app.get('/api/candles/{symbol}')
def get_candles(symbol:str,timeframe:str='1d'):return {'symbol':symbol,'timeframe':timeframe,'synthetic':True,'candles':candles(symbol,timeframe)}

@app.get('/api/signals')
def signals(style:Literal['intraday','swing','positional']='swing'):
    timeframe={'intraday':'15m','swing':'1d','positional':'1w'}[style]
    statuses=['Forming','Near breakout','Watch','Forming','Near breakout','Watch','Forming','Near breakout']
    return {'synthetic':True,'signals':[{'symbol':s['symbol'],'name':s['name'],'price':candles(s['symbol'],timeframe)[-1]['close'],'pattern':'Rounding bottom (demo)','status':statuses[i],'score':min(95,68+i*3),'timeframe':timeframe} for i,s in enumerate(STOCKS)]}

class Order(BaseModel):
    symbol:str
    side:Literal['BUY','SELL']
    quantity:int=Field(gt=0,le=100000)

@app.post('/api/paper/orders')
def paper_order(order:Order):
    stock=next((s for s in STOCKS if s['symbol']==order.symbol),None)
    if not stock:raise HTTPException(404,'Unknown symbol')
    price=candles(order.symbol,'1d')[-1]['close']
    amount=round(price*order.quantity,2)
    owned=accounts['positions'].get(order.symbol,0)
    if order.side=='BUY':
        if amount>accounts['cash']:raise HTTPException(400,'Insufficient paper cash')
        accounts['cash']=round(accounts['cash']-amount,2)
        accounts['positions'][order.symbol]=owned+order.quantity
    else:
        if order.quantity>owned:raise HTTPException(400,'Insufficient paper shares; shorting disabled')
        accounts['cash']=round(accounts['cash']+amount,2)
        accounts['positions'][order.symbol]=owned-order.quantity
    result={'id':len(accounts['orders'])+1,'symbol':order.symbol,'side':order.side,'quantity':order.quantity,'price':price,'notional':amount,'time':datetime.now(timezone.utc).isoformat(),'mode':'PAPER','status':'FILLED_SIMULATED'}
    accounts['orders'].insert(0,result)
    return result

@app.get('/api/paper/account')
def account():
    holdings=[{'symbol':symbol,'quantity':qty,'price':candles(symbol,'1d')[-1]['close']} for symbol,qty in accounts['positions'].items() if qty>0]
    equity=round(accounts['cash']+sum(h['quantity']*h['price'] for h in holdings),2)
    return {'cash':accounts['cash'],'equity':equity,'starting_cash':accounts['initial_cash'],'holdings':holdings,'orders':accounts['orders']}

@app.post('/api/paper/reset')
def reset():
    accounts.update({'cash':100000.0,'initial_cash':100000.0,'positions':{},'orders':[]})
    return account()

# Phase 2: independent CSV-based historical scanner. Phase 1 demo endpoints remain unchanged.
from scanner import scan_all
@app.get('/api/scanner/rounding-bottom')
def rounding_bottom_scan(lookback:int=120,volume_ratio:float=1.5,breakout_pct:float=1.0):
    if not 60<=lookback<=250 or not 1<=volume_ratio<=5 or not 0<=breakout_pct<=5:
        raise HTTPException(400,'Invalid scanner settings')
    return scan_all(lookback,volume_ratio,breakout_pct)


@app.get('/api/history/{symbol}')
def historical_candles(symbol: str, lookback: int = 120, volume_ratio: float = 1.5, breakout_pct: float = 1.0):
    from scanner import load_csv, detect
    from sessions import metadata
    if not 60 <= lookback <= 250 or not 1 <= volume_ratio <= 5 or not 0 <= breakout_pct <= 5:
        raise HTTPException(400, 'Invalid scanner settings')
    try:
        rows = load_csv(symbol)
        return {'symbol': symbol.upper(), 'timeframe': '1d', 'synthetic': False,
                'source': 'USER_PROVIDED_CSV', 'candles': [{**r, **metadata(r)} for r in rows],
                'pattern': detect(rows, lookback, volume_ratio, breakout_pct)}
    except FileNotFoundError:
        raise HTTPException(404, 'No historical CSV for symbol')
    except (ValueError, KeyError) as exc:
        raise HTTPException(400, str(exc))
