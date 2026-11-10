from datetime import date, timedelta
from unittest import TestCase
from unittest.mock import patch

from strategies import evaluate
from upstox import equity_keys, normalize_quotes


def candles(prices):
    return [
        {"date": (date(2024, 1, 1) + timedelta(days=index)).isoformat(),
         "open": price, "close": price, "low": price - 1, "high": price + 1}
        for index, price in enumerate(prices)
    ]


class StrategyTests(TestCase):
    def test_rounding_bottom_reuses_existing_detector(self):
        with patch("scanner.detect", return_value={"status": "Forming", "lookback": 60}):
            self.assertIn("Forming", evaluate("rounding-bottom", candles([100]))[0])

    def test_rounding_top_requires_arch(self):
        arch = [100 + 15 * (1 - ((index - 29.5) / 29.5) ** 2) for index in range(60)]
        self.assertIn("Below neckline", evaluate("rounding-top", candles(arch + [98]))[0])
        self.assertFalse(evaluate("rounding-top", candles([100] * 61)))

    def test_doji_direction_and_body(self):
        falling = candles(list(range(120, 100, -1)) + [100])
        rising = candles(list(range(100, 120)) + [120])
        self.assertTrue(evaluate("doji-downtrend", falling))
        self.assertTrue(evaluate("doji-uptrend", rising))
        self.assertFalse(evaluate("doji-uptrend", falling))
        rising[-1]["open"] = 119
        self.assertFalse(evaluate("doji-uptrend", rising))

    def test_consolidation_near_prior_edges(self):
        context = [100, 130] * 25
        self.assertTrue(evaluate("consolidation-top", candles(context + [129] * 10)))
        self.assertTrue(evaluate("consolidation-bottom", candles(context + [101] * 10)))
        self.assertFalse(evaluate("consolidation-top", candles(context + [115] * 10)))

    def test_dma_warmup(self):
        self.assertEqual(len(evaluate("dma-test", candles([100] * 201))), 2)
        self.assertEqual(len(evaluate("dma-test", candles([100] * 200))), 1)

    def test_breakout_excludes_signal_candle_from_high(self):
        self.assertEqual(len(evaluate("breakouts", candles([100] * 252 + [110]))), 2)
        self.assertFalse(evaluate("breakouts", candles([100] * 253)))
        self.assertFalse(evaluate("breakouts", candles([100] * 20 + [110])))


class UpstoxTests(TestCase):
    def test_equity_master_deduplicates_contracts_and_excludes_expired(self):
        stock = {"segment": "NSE_FO", "underlying_type": "EQUITY", "instrument_type": "FUT",
                 "expiry": 2000, "underlying_key": "NSE_EQ|TEST", "underlying_symbol": "TEST"}
        self.assertEqual(equity_keys([
            stock, {**stock, "instrument_type": "CE"},
            {**stock, "underlying_key": "NSE_EQ|EXPIRED", "expiry": 500},
            {**stock, "underlying_type": "INDEX", "underlying_key": "NSE_INDEX|Nifty 50"},
        ], 1000), {"NSE_EQ|TEST": "TEST"})

    def test_quote_keeps_actual_trade_timestamp(self):
        row = {"instrument_token": "NSE_EQ|TEST", "last_price": 100, "last_trade_time": "1757000551130"}
        keys = {"NSE_EQ|TEST": "TEST"}
        quote, = normalize_quotes({"row": row}, keys)
        self.assertEqual(quote["symbol"], "TEST")
        self.assertEqual(quote["last_trade"], "2025-09-04T15:42:31.130000+00:00")
        self.assertFalse(normalize_quotes({"row": {**row, "last_price": -1}}, keys))
