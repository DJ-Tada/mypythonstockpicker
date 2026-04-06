"""Fetch all US stock tickers from the Massive.com API and optionally download financials.

Usage:
    python -m stockpicker.fetch_tickers                     # fetch tickers only
    python -m stockpicker.fetch_tickers --financials        # fetch tickers + financials
    python -m stockpicker.fetch_tickers --check-status      # check fill status of existing financials
"""
from __future__ import annotations

import argparse
import csv
import sys
import time

import pandas as pd
import requests

from stockpicker import get_output_dir
from stockpicker.financial_utils import fetch_financials_for_df, tickers_fill_status, to_dataframe


def _get_api_key() -> str:
    """Read the Massive API key from config.py (never hardcoded)."""
    try:
        from config import MASSIVE_API_KEY
        if MASSIVE_API_KEY:
            return MASSIVE_API_KEY
    except ImportError:
        pass
    print("ERROR: Set MASSIVE_API_KEY in config.py (see config.template.py)", file=sys.stderr)
    sys.exit(1)


def fetch_all_tickers(api_key: str, rate_limit_sleep: float = 12.0) -> list[dict]:
    """Paginate through the Massive.com tickers endpoint and return all results."""
    url = "https://api.massive.com/v3/reference/tickers"
    params = {"market": "stocks", "active": "true", "order": "asc", "limit": 1000, "sort": "ticker"}
    headers = {"Authorization": f"Bearer {api_key}"}
    tickers = []
    while url:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        tickers.extend(data.get("results", []))
        url = data.get("next_url")
        params = {}  # only needed for first request
        if url:
            time.sleep(rate_limit_sleep)
    return tickers


def main():
    parser = argparse.ArgumentParser(description="Fetch tickers from Massive.com API")
    parser.add_argument("--financials", action="store_true", help="Also fetch financials via yfinance")
    parser.add_argument("--check-status", action="store_true", help="Check fill status of existing financials")
    parser.add_argument("--financials-dir", default="output/financials", help="Directory for financial CSVs")
    args = parser.parse_args()

    out_dir = get_output_dir()

    # Fetch tickers
    api_key = _get_api_key()
    print("Fetching tickers from Massive.com API ...")
    tickers = fetch_all_tickers(api_key)
    print(f"Fetched {len(tickers)} tickers")

    # Save raw tickers to CSV
    if tickers:
        tickers_csv = out_dir / "tickers.csv"
        with open(str(tickers_csv), "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=tickers[0].keys())
            writer.writeheader()
            writer.writerows(tickers)
        print(f"Saved to {tickers_csv}")

    # Convert to DataFrame
    df = to_dataframe(tickers)
    df.to_csv(str(out_dir / "tickers_dataframe.csv"), index=False)

    if args.financials:
        print("Fetching financials via yfinance ...")
        summary = fetch_financials_for_df(df, ticker_col="ticker", out_dir=args.financials_dir, overwrite=False)
        print(summary.head())

    if args.check_status:
        tickers_series = pd.read_csv(str(out_dir / "tickers.csv"))["ticker"]
        status_df = tickers_fill_status(tickers_series, folder=args.financials_dir, threshold_bytes=100)
        print(status_df.head())


if __name__ == "__main__":
    main()
