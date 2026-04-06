"""Run a full-pass: compile per-file metrics, produce a one-row-per-ticker summary and scored ranking.

This script uses the repository's `compile_financials` and `query_financials` helpers.
It writes these files to the repository root by default:
  - financials_summary.parquet  (and .csv)
  - financials_scored.parquet   (and .csv)

The script is intentionally simple and single-threaded to be robust. It tolerates
per-file failures and records them to `financials_errors.json`.
"""
from __future__ import annotations

import json
from pathlib import Path
import argparse
import sys

import pandas as pd
from tqdm import tqdm

from stockpicker.compile_financials import process_file_to_long
from stockpicker.query_financials import extract_metrics_from_long_df, score_tickers
from stockpicker import get_output_dir

OUT_DIR = get_output_dir()


def run(financials_dir: str, out_prefix: str = "financials_summary", pattern: str = "*_financials.csv", criteria: dict | None = None):
    financials_dir = Path(financials_dir)
    files = sorted(financials_dir.glob(pattern))

    results = []
    errors = {}

    for f in tqdm(files, desc="processing CSVs", unit="file"):
        ticker = f.name.split("_")[0].upper()
        try:
            long = process_file_to_long(str(f), ticker=ticker)
            if long is None or long.empty:
                # still include an empty row so ticker shows up if needed
                continue

            metrics = extract_metrics_from_long_df(long)
            if metrics is None or metrics.empty:
                continue

            # metrics is indexed by ticker; convert to row
            results.append(metrics.reset_index())

        except Exception as e:
            errors[ticker] = str(e)

    if results:
        df_all = pd.concat(results, axis=0, ignore_index=True)
        # set ticker as index
        if 'ticker' in df_all.columns:
            df_all = df_all.set_index('ticker')
    else:
        df_all = pd.DataFrame()

    # Save summary files
    out_parquet = Path(OUT_DIR) / (out_prefix + '.parquet')
    out_csv = Path(OUT_DIR) / (out_prefix + '.csv')
    try:
        if not df_all.empty:
            df_all.to_parquet(out_parquet)
            df_all.to_csv(out_csv)
        else:
            # write empty placeholders
            pd.DataFrame().to_parquet(out_parquet)
            pd.DataFrame().to_csv(out_csv)
    except Exception as e:
        print(f"Failed to write summary files: {e}", file=sys.stderr)

    # scoring
    if criteria is None:
        criteria = {
            'revenue_yoy': ('higher', 0.6),
            'margin_latest': ('higher', 0.4),
        }

    try:
        scored = score_tickers(df_all, criteria)
        out_parquet_s = Path(OUT_DIR) / 'financials_scored.parquet'
        out_csv_s = Path(OUT_DIR) / 'financials_scored.csv'
        if not scored.empty:
            scored.to_parquet(out_parquet_s)
            scored.to_csv(out_csv_s)
        else:
            pd.DataFrame().to_parquet(out_parquet_s)
            pd.DataFrame().to_csv(out_csv_s)
    except Exception as e:
        print(f"Failed to score/write scored outputs: {e}", file=sys.stderr)

    # write errors
    if errors:
        Path(OUT_DIR / 'financials_errors.json').write_text(json.dumps(errors, indent=2))

    # print summary
    print(f"Files processed: {len(files)}")
    print(f"Tickers summarized: {0 if df_all.empty else len(df_all)}")
    print(f"Errors: {len(errors)}")
    if not df_all.empty:
        print('\nTop 10 by score (if scored present):')
        try:
            top = scored.head(10)
            print(top[['score', 'rank']])
        except Exception:
            print(df_all.head(10))


def main():
    parser = argparse.ArgumentParser(description='Run full dataset financials summary and scoring')
    parser.add_argument('--financials_dir', default='financials')
    parser.add_argument('--pattern', default='*_financials.csv')
    parser.add_argument('--out_prefix', default='financials_summary')
    args = parser.parse_args()
    run(args.financials_dir, args.out_prefix, args.pattern)


if __name__ == '__main__':
    main()
