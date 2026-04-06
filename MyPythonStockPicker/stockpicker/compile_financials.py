"""Utilities to compile the per-ticker financial CSV files into unified datasets.

Behavior
- Each source CSV is expected to have at least columns: `line_item`, some date columns (e.g. "2024-09-30 ..."), and optionally `section`.
- Two output shapes are supported:
  * long: rows = (ticker, date, line_item, section, value) -- memory-friendly and recommended
  * wide: rows = (ticker, date, <one column per line_item>) -- can be very wide and memory heavy

Recommended workflow for large collections (thousands of files):
  - Run compile_all(..., mode='long') which writes one Parquet file per ticker into an output directory (partitioned on filesystem).
  - Use pyarrow.dataset or DuckDB to query the parquet files without loading everything into memory.

This file is written to be dependency-light: it uses pandas and (optionally) pyarrow for parquet writing.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional

import pandas as pd
from tqdm import tqdm


def _detect_date_columns(df: pd.DataFrame) -> List[str]:
    # date columns are all columns except these known id columns
    candidates = [c for c in df.columns if c not in ("line_item", "section")]
    # prefer columns that look like YYYY- or contain digits
    if not candidates:
        return []
    return candidates


def process_file_to_long(csv_path: str, ticker: Optional[str] = None, dropna: bool = True) -> pd.DataFrame:
    """Read a single financials CSV and return a long-format DataFrame.

    Returns columns: ['ticker', 'date', 'line_item', 'section', 'value']
    """
    p = Path(csv_path)
    if ticker is None:
        ticker = p.name.split("_")[0]

    df = pd.read_csv(p, dtype=str)
    if df.empty:
        return pd.DataFrame(columns=["ticker", "date", "line_item", "section", "value"]).astype(object)

    # ensure expected columns exist
    if "line_item" not in df.columns:
        # try first column name as fallback
        df = df.rename(columns={df.columns[0]: "line_item"})

    date_cols = _detect_date_columns(df)
    if not date_cols:
        # nothing to melt
        return pd.DataFrame(columns=["ticker", "date", "line_item", "section", "value"]).astype(object)

    # keep section if present
    id_vars = ["line_item"]
    if "section" in df.columns:
        id_vars.append("section")

    long = df.melt(id_vars=id_vars, value_vars=date_cols, var_name="date", value_name="value")
    long["ticker"] = str(ticker).upper()

    # normalize types
    # convert numeric strings to floats where possible
    long["value"] = pd.to_numeric(long["value"], errors="coerce")

    if dropna:
        long = long.dropna(subset=["value"]).reset_index(drop=True)
    else:
        long = long.reset_index(drop=True)

    # order columns
    cols = ["ticker", "date", "line_item", "value"]
    if "section" in long.columns:
        cols.insert(3, "section")

    return long[cols]


def process_file_to_wide(csv_path: str, ticker: Optional[str] = None, dropna: bool = True) -> pd.DataFrame:
    """Read a single financials CSV and return a wide-format DataFrame.

    Returns columns: ['ticker', 'date', <line_item columns...>]
    Warning: this may produce very wide DataFrames and large memory usage.
    """
    long = process_file_to_long(csv_path, ticker=ticker, dropna=False)
    if long.empty:
        return pd.DataFrame()

    # pivot so line_items become columns
    try:
        wide = long.pivot_table(index=["ticker", "date"], columns="line_item", values="value", aggfunc="first")
    except Exception:
        # fallback: groupby-unstack
        wide = long.set_index(["ticker", "date", "line_item"])["value"].unstack("line_item")

    wide = wide.reset_index()

    if dropna:
        # drop rows that are entirely NaN except the index columns
        value_cols = [c for c in wide.columns if c not in ("ticker", "date")]
        if value_cols:
            wide = wide.dropna(axis=0, how="all", subset=value_cols).reset_index(drop=True)

    return wide


def compile_all(
    financials_dir: str | Path = "financials",
    out_dir: str | Path = None,
    mode: str = "long",
    pattern: str = "*_financials.csv",
    skip_existing: bool = True,
):
    """Process all CSV files in `financials_dir` and write per-ticker parquet files to `out_dir`.

    mode: 'long' or 'wide'. 'long' is recommended for large datasets.
    """
    financials_dir = Path(financials_dir)
    if out_dir is None:
        from stockpicker import get_output_dir
        out_dir = get_output_dir() / 'financials_parquet'
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(financials_dir.glob(pattern))
    for f in tqdm(files, desc="processing financials", unit="file"):
        ticker = f.name.split("_")[0].upper()
        target = out_dir / f"{ticker}.parquet"
        if skip_existing and target.exists():
            continue

        try:
            if mode == "long":
                df = process_file_to_long(str(f), ticker=ticker, dropna=True)
            else:
                df = process_file_to_wide(str(f), ticker=ticker, dropna=True)

            if df is None or df.empty:
                # write an empty placeholder (so we know it was processed)
                pd.DataFrame().to_parquet(target)
            else:
                # try writing parquet (pyarrow recommended)
                try:
                    df.to_parquet(target, index=False)
                except Exception:
                    # fallback to pandas default (may still require pyarrow)
                    df.to_parquet(target, index=False)

        except Exception as e:
            # write a small error marker so the file won't be retried endlessly
            err_path = out_dir / f"{ticker}__ERROR.txt"
            err_path.write_text(str(e))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compile per-ticker financial CSVs into parquet dataset")
    parser.add_argument("--financials_dir", default="financials")
    parser.add_argument("--out_dir", default="financials_parquet")
    parser.add_argument("--mode", choices=["long", "wide"], default="long")
    parser.add_argument("--pattern", default="*_financials.csv")
    parser.add_argument("--skip-existing", action="store_true")

    args = parser.parse_args()
    compile_all(args.financials_dir, args.out_dir, mode=args.mode, pattern=args.pattern, skip_existing=args.skip_existing)
