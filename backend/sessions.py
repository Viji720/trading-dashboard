"""Configurable session overrides. Weekdays are assumed regular, not verified.

Unknown/weekend, special and incomplete candles never confirm volume.
"""
import json
from datetime import datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

CONFIG = Path(__file__).with_name('sessions.json')


def metadata(row, config=None, now=None):
    if config is None:
        config = json.loads(CONFIG.read_text(encoding='utf-8'))
    day = datetime.strptime(row['date'], '%Y-%m-%d').date()
    override = config.get('sessions', {}).get(row['date'], {})
    kind = override.get('type', 'regular' if day.weekday() < 5 and
                        config.get('weekday_policy') == 'regular' else 'unknown')
    if kind not in ('regular', 'special', 'unknown'):
        raise ValueError(f'Invalid session type for {day}')
    now = now or datetime.now(ZoneInfo('Asia/Kolkata'))
    complete = (day < now.date() or
                (day == now.date() and kind == 'regular' and now.time() >= time(15, 30)))
    # Explicit false always wins; true cannot make a future candle complete.
    complete = complete and row.get('complete', True) and override.get('complete', True)
    return {'session_type': kind, 'session_label': override.get('label', kind),
            'session_source': override.get('source', 'Configured weekday assumption'),
            'complete': bool(complete)}


def volume_context(rows, threshold):
    config = json.loads(CONFIG.read_text(encoding='utf-8'))
    last = metadata(rows[-1], config)
    prior = [r['volume'] for r in rows[:-1]
             if metadata(r, config)['session_type'] == 'regular' and metadata(r, config)['complete']
             and r['volume'] > 0][-20:]
    comparable = last['session_type'] == 'regular' and last['complete'] and len(prior) == 20
    ratio = rows[-1]['volume'] / (sum(prior) / len(prior)) if comparable else None
    reason = ('Comparable with 20 complete regular sessions' if comparable else
              'Special/unknown session, incomplete candle, or fewer than 20 regular sessions')
    return {**last, 'volume_comparable': comparable, 'volume_confirmed':
            bool(comparable and ratio >= threshold),
            'volume_ratio': round(ratio, 2) if ratio is not None else None,
            'volume_reason': reason, 'volume_baseline_count': len(prior)}
