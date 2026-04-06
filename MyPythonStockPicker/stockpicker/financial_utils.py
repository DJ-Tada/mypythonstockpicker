import pandas as pd
import os
import glob
import yfinance as yf
from time import sleep
from tqdm import tqdm
from typing import Any, List, Iterable, Union


def to_dataframe(tickers: List[Any]) -> pd.DataFrame:
    """
    Convert `tickers` (list) to a pandas DataFrame.
    Handles:
      - list of dicts -> columns from keys
      - list of strings -> single-column DataFrame with column 'ticker'
      - list of tuples/lists -> columns named col_0, col_1, ...
      - empty list -> empty DataFrame
      - mixed types -> coerces to strings in a single column
    """
    if not tickers:
        return pd.DataFrame()  # empty

    first = tickers[0]

    # list of dicts
    if isinstance(first, dict):
        return pd.DataFrame(tickers)

    # list of strings
    if isinstance(first, str):
        return pd.DataFrame(tickers, columns=['ticker'])

    # list of tuples/lists
    if isinstance(first, (list, tuple)):
        # determine max length to normalize rows
        max_len = max(len(x) for x in tickers)
        cols = [f'col_{i}' for i in range(max_len)]
        normalized = [list(x) + [None]*(max_len - len(x)) for x in tickers]
        return pd.DataFrame(normalized, columns=cols)

    # fallback: mixed or unknown types -> single column of repr
    return pd.DataFrame([str(x) for x in tickers], columns=['value'])


def fetch_financials_for_df(df: pd.DataFrame,
                            ticker_col: str = 'ticker',
                            out_dir: str = 'financials',
                            overwrite: bool = False,
                            sleep_between: float = 0.0,
                            show_progress: bool = True) -> pd.DataFrame:
    """
    For each ticker in `df[ticker_col]`, fetch financial statements via yfinance and
    save them as CSV files under `out_dir/<ticker>_financials.csv`.

    Returns a summary DataFrame with columns: ticker, has_balance_sheet, has_income_stmt, has_cashflow
    """
    from pathlib import Path
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    summaries = []
    tickers = df[ticker_col].dropna().unique() if ticker_col in df.columns else []

    iterator = tickers
    if show_progress:
        iterator = tqdm(tickers, desc='fetching financials', unit='ticker')

    for t in iterator:
        if sleep_between and sleep_between > 0:
            sleep(sleep_between)
        # safe filename
        safe_t = str(t).upper()
        file_path = str(out_path / f"{safe_t}_financials.csv")

        if os.path.exists(file_path) and not overwrite:
            # load summary from existing file (we'll still record presence)
            tmp = pd.read_csv(file_path)
            has_bs = 'Balance Sheet' in tmp.columns or 'balanceSheet' in tmp.columns
            has_is = 'Income Statement' in tmp.columns or 'incomeStatement' in tmp.columns
            has_cf = 'Cash Flow' in tmp.columns or 'cashflowStatement' in tmp.columns
            summaries.append({'ticker': safe_t, 'has_balance_sheet': has_bs, 'has_income_stmt': has_is, 'has_cashflow': has_cf})
            continue

        try:
            ticker = yf.Ticker(safe_t)
            # yfinance provides .balance_sheet, .financials (income stmt), .cashflow as DataFrames
            bs = ticker.balance_sheet
            is_ = ticker.financials
            cf = ticker.cashflow

            # normalize and concatenate into a single CSV per ticker with a section column
            parts = []
            if not bs.empty:
                df_bs = bs.reset_index().rename(columns={'index': 'line_item'})
                df_bs['section'] = 'balance_sheet'
                parts.append(df_bs)
            if not is_.empty:
                df_is = is_.reset_index().rename(columns={'index': 'line_item'})
                df_is['section'] = 'income_statement'
                parts.append(df_is)
            if not cf.empty:
                df_cf = cf.reset_index().rename(columns={'index': 'line_item'})
                df_cf['section'] = 'cashflow'
                parts.append(df_cf)

            if parts:
                out_df = pd.concat(parts, ignore_index=True, sort=False)
                out_df.to_csv(file_path, index=False)
                summaries.append({'ticker': safe_t, 'has_balance_sheet': not bs.empty, 'has_income_stmt': not is_.empty, 'has_cashflow': not cf.empty})
            else:
                # create an empty placeholder file so we don't re-query if not desired
                pd.DataFrame([{'ticker': safe_t}]).to_csv(file_path, index=False)
                summaries.append({'ticker': safe_t, 'has_balance_sheet': False, 'has_income_stmt': False, 'has_cashflow': False})

        except Exception as e:
            # record failure
            summaries.append({'ticker': safe_t, 'has_balance_sheet': False, 'has_income_stmt': False, 'has_cashflow': False, 'error': str(e)})

    return pd.DataFrame(summaries)


def tickers_fill_status(tickers: Union[pd.DataFrame, Iterable],
                        folder: str = 'financials',
                        ticker_col: str = 'ticker',
                        threshold_bytes: int = 100,
                        filename_template: str = '{ticker}_financials.csv') -> pd.DataFrame:
    """
    Return a DataFrame with one row per ticker and a status column:
      - 'filled' if file size >= threshold_bytes
      - 'empty' if file size < threshold_bytes (includes missing files)
    Columns returned: ticker, filename, size_bytes, status
    """
    # normalize tickers input to an iterable of unique strings
    if isinstance(tickers, pd.DataFrame):
        if ticker_col not in tickers.columns:
            raise ValueError(f"DataFrame does not contain column '{ticker_col}'")
        tickers_iter = pd.Series(tickers[ticker_col].dropna().unique()).astype(str).tolist()
    else:
        tickers_iter = [str(x) for x in tickers]

    rows = []
    folder = os.path.abspath(folder)

    for t in tickers_iter:
        ticker_up = str(t).upper()
        expected_name = filename_template.format(ticker=ticker_up)
        expected_path = os.path.join(folder, expected_name)

        found_path = None
        if os.path.exists(expected_path):
            found_path = expected_path
        else:
            # fallback: case-insensitive search for files starting with the ticker
            pattern = os.path.join(folder, f"{ticker_up}*.csv")
            # Try both uppercase and lowercase matches
            matches = glob.glob(pattern)
            if not matches:
                # try lowercase
                pattern2 = os.path.join(folder, f"{ticker_up.lower()}*.csv")
                matches = glob.glob(pattern2)
            if matches:
                # pick the first match
                found_path = matches[0]

        if found_path:
            try:
                size = os.path.getsize(found_path)
            except OSError:
                size = 0
        else:
            size = 0
            found_path = ''  # empty to indicate missing

        status = 'filled' if size >= threshold_bytes else 'empty'
        rows.append({
            'ticker': ticker_up,
            'filename': os.path.relpath(found_path) if found_path else '',
            'size_bytes': int(size),
            'status': status
        })

    return pd.DataFrame(rows)
