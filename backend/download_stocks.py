
from pathlib import Path
import yfinance as yf

STOCKS = [
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFCBANK",
    "ICICIBANK",
    "JIOFIN",
    "SBIN",
    "ITC",
    "TATAMOTORS",
    "BHARTIARTL",
]

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

for symbol in STOCKS:
    ticker = f"{symbol}.NS"
    print(f"Downloading {ticker}...")

    try:
        df = yf.download(
            ticker,
            period="2y",
            interval="1d",
            auto_adjust=False,
            progress=False,
        )

        if df.empty:
            print(f"No data for {symbol}")
            continue

        # Flatten yfinance multi-level columns
        if isinstance(df.columns, __import__("pandas").MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()

        df = df.rename(columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        })

        df = df[
            ["date", "open", "high", "low", "close", "volume"]
        ]

        df["date"] = df["date"].dt.strftime("%Y-%m-%d")

        file_path = DATA_DIR / f"{symbol}.csv"
        df.to_csv(file_path, index=False)

        print(f"Saved {len(df)} rows to {file_path}")

    except Exception as error:
        print(f"Failed {symbol}: {error}")

print("Download process completed.")