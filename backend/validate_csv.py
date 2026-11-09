
from pathlib import Path
import pandas as pd

data_dir = Path("data")

columns = ["open", "high", "low", "close", "volume"]

for file in sorted(data_dir.glob("*.csv")):
    print(f"\nChecking {file.name}")

    try:
        df = pd.read_csv(file)

        df.columns = [
            str(c).strip().lower() for c in df.columns
        ]

        required = ["date"] + columns

        if not all(c in df.columns for c in required):
            print("Missing required columns")
            continue

        df["date"] = pd.to_datetime(
            df["date"], errors="coerce"
        )

        for col in columns:
            df[col] = pd.to_numeric(
                df[col], errors="coerce"
            )

        valid = (
            df["date"].notna()
            & df[columns].notna().all(axis=1)
            & (df[["open", "high", "low", "close"]] > 0).all(axis=1)
            & (df["volume"] > 0)
            & (df["high"] >= df[["open", "close", "low"]].max(axis=1))
            & (df["low"] <= df[["open", "close", "high"]].min(axis=1))
        )

        invalid = df.loc[~valid]

        print("Total rows:", len(df))
        print("Invalid rows:", len(invalid))

        if not invalid.empty:
            print(invalid[required].head(10).to_string(index=False))

        cleaned = (
            df.loc[valid, required]
            .sort_values("date")
            .drop_duplicates("date", keep="last")
        )

        if len(cleaned) < 140:
            print("WARNING: Fewer than 140 valid candles")

        cleaned["date"] = cleaned["date"].dt.strftime("%Y-%m-%d")

        cleaned.to_csv(file, index=False)

        print("Valid rows saved:", len(cleaned))

    except Exception as exc:
        print("ERROR:", exc)
