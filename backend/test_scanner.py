import csv
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import scanner
from sessions import volume_context


def candles():
    days = [date(2025, 1, 1) + timedelta(days=i) for i in range(180)]
    days = [d for d in days if d.weekday() < 5]
    return [dict(date=d.isoformat(), open=100, high=101, low=99,
                 close=100, volume=100, complete=True) for d in days]


class SessionTests(unittest.TestCase):
    def test_regular_volume(self):
        rows = candles()
        rows[-1]['volume'] = 200
        v = volume_context(rows, 1.5)
        self.assertEqual(v['volume_ratio'], 2)
        self.assertTrue(v['volume_confirmed'])

    def test_special_preserved_and_never_confirmed(self):
        rows = candles()
        rows[-1].update(date='2026-11-08', volume=100000)
        v = volume_context(rows, 1.5)
        self.assertIsNone(v['volume_ratio'])
        self.assertFalse(v['volume_confirmed'])
        result = scanner.evaluate_window(rows[-60:], 1.5, 1)
        self.assertEqual(result['date'], '2026-11-08')
        self.assertNotEqual(result['status'], 'Confirmed breakout')

    def test_incomplete_and_unknown(self):
        for updates in ({'complete': False}, {'date': '2025-06-29'}):
            rows = candles()
            rows[-1].update(updates)
            self.assertFalse(volume_context(rows, 1.5)['volume_comparable'])

    def test_special_excluded_from_baseline(self):
        rows = candles()
        rows.insert(-1, dict(rows[-2], date='2026-11-08', volume=100000))
        self.assertEqual(volume_context(rows, 1.5)['volume_ratio'], 1)

    def test_insufficient_baseline(self):
        self.assertFalse(volume_context(candles()[:20], 1.5)['volume_comparable'])

    def test_valid_breakout_requires_comparable_volume(self):
        rows = candles()[-80:]
        for i, row in enumerate(rows[:-1]):
            price = 80 + 20 * ((i - 39) / 39) ** 2
            row.update(open=price, close=price, high=price+1, low=price-1)
        rows[-1].update(close=106, high=107, volume=200)
        self.assertEqual(scanner.evaluate_window(rows, 1.5, 1)['status'], 'Confirmed breakout')
        rows[-1]['date'] = '2026-11-08'
        result = scanner.evaluate_window(rows, 1.5, 1)
        self.assertTrue(result['pattern_valid'])
        self.assertTrue(result['price_breakout'])
        self.assertFalse(result['volume_confirmed'])
        self.assertEqual(result['status'], 'Breakout - volume unconfirmed')

    def load_fixture(self, rows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'TEST.csv'
            with path.open('w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=list(rows[0]))
                writer.writeheader()
                writer.writerows(rows)
            with patch.object(scanner, 'DATA', Path(directory)):
                return scanner.load_csv('TEST')

    def test_zero_placeholder_excluded(self):
        rows = candles()[:3]
        rows[1]['volume'] = 0
        self.assertEqual(len(self.load_fixture(rows)), 2)

    def test_duplicate_rejected_even_placeholder(self):
        row = candles()[0]
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.load_fixture([row, dict(row, volume=0)])

    def test_signal_candle_excluded_from_shape(self):
        rows = candles()
        before = scanner.evaluate_window(rows[-60:], 1.5, 1)
        rows[-1]['close'] = 200
        after = scanner.evaluate_window(rows[-60:], 1.5, 1)
        for key in ('score', 'resistance', 'pattern_bottom', 'depth_pct'):
            self.assertEqual(before[key], after[key])

    def test_real_files_and_history(self):
        from main import historical_candles, health
        result = scanner.scan_all()
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['scanned_files'], 9)
        history = historical_candles('RELIANCE')
        self.assertFalse(history['synthetic'])
        self.assertEqual(history['candles'][-1]['session_type'], 'special')
        self.assertIn('PAPER_ONLY', health()['mode'])


if __name__ == '__main__':
    unittest.main()
