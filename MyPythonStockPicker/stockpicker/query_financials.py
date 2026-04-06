"""Helpers to extract per-ticker summary metrics and compute rankings.

This module works with the long-format DataFrame produced by
`compile_financials.process_file_to_long` or with a DuckDB/parquet dataset.

Functions:
- extract_metrics_from_long_df(long_df): returns a small per-ticker metrics DataFrame
- score_tickers(df_metrics, criteria): compute percentile-based scores and combined ranking

CLI: quick demo to load one CSV and show computed metrics.
"""
from __future__ import annotations

from typing import Dict, Tuple
import pandas as pd
import numpy as np


def extract_metrics_from_long_df(long_df: pd.DataFrame) -> pd.DataFrame:
    """Given a long-format DataFrame (ticker, date, line_item, [section], value),
    compute a small set of example metrics per ticker.

    Metrics produced:
      - revenue_latest, revenue_prev, revenue_yoy
      - netincome_latest, margin_latest (netincome / revenue)
      - assets_latest

    Returns a DataFrame indexed by ticker.
    """
    if long_df.empty:
        return pd.DataFrame()

    df = long_df.copy()
    # ensure date is comparable: keep as string but sort lexicographically (ISO-like timestamps)
    # find latest two dates per ticker
    df['date'] = df['date'].astype(str)

    results = []
    for ticker, g in df.groupby('ticker'):
        dates = sorted(g['date'].unique(), reverse=True)
        if not dates:
            continue
        latest = dates[0]
        prev = dates[1] if len(dates) > 1 else None

        # helper to pull a scalar value for a given line_item & date
        def v_for(line_item: str, date: str):
            if date is None:
                return np.nan
            sub = g[(g['date'] == date) & (g['line_item'] == line_item)]
            if sub.empty:
                return np.nan
            # if multiple rows, take first non-null
            vals = pd.to_numeric(sub['value'], errors='coerce')
            if vals.notna().any():
                return float(vals.dropna().iloc[0])
            return np.nan

        def v_for_multi(candidates, date: str):
            # try multiple possible line_item names
            for name in candidates:
                val = v_for(name, date)
                if pd.notna(val):
                    return val
            return np.nan

        revenue_latest = v_for_multi(['Total Revenue', 'TotalRevenue', 'Revenue', 'Operating Revenue'], latest)
        revenue_prev = v_for_multi(['Total Revenue', 'TotalRevenue', 'Revenue', 'Operating Revenue'], prev) if prev else np.nan
        revenue_yoy = (revenue_latest - revenue_prev) / revenue_prev if pd.notna(revenue_latest) and pd.notna(revenue_prev) and revenue_prev != 0 else np.nan

        netincome_latest = v_for_multi(['Net Income', 'NetIncome', 'Net Income Common Stockholders', 'Net Income Including Noncontrolling Interests'], latest)
        margin_latest = netincome_latest / revenue_latest if pd.notna(netincome_latest) and pd.notna(revenue_latest) and revenue_latest != 0 else np.nan

        assets_latest = v_for_multi(['Total Assets', 'TotalAssets', 'Assets'], latest)

        # expanded metrics
        equity_latest = v_for_multi(['Stockholders Equity', 'Stockholders Equity, Net', 'Total Equity Gross Minority Interest', 'Total Equity', 'Common Stock Equity', 'Shareholders Equity', 'Shareholders Equity (Total)', 'Total Equity'], latest)
        total_debt_latest = v_for_multi(['Total Debt', 'TotalDebt', 'Long Term Debt', 'Current Debt', 'Current Debt And Capital Lease Obligation', 'Long Term Debt And Capital Lease Obligation'], latest)
        cash_latest = v_for_multi(['Cash And Cash Equivalents', 'CashCashEquivalentsAndShortTermInvestments', 'Cash Cash Equivalents And Short Term Investments', 'Cash And Cash Equivalents And Short Term Investments', 'Cash And Cash Equivalents, Ending'], latest)
        free_cash_flow_latest = v_for_multi(['Free Cash Flow', 'FreeCashFlow', 'Free Cash Flow (No Extraordinary Items)'], latest)
        ebitda_latest = v_for_multi(['EBITDA', 'Normalized EBITDA'], latest)
        current_assets_latest = v_for_multi(['Current Assets', 'CurrentAssets'], latest)
        current_liabilities_latest = v_for_multi(['Current Liabilities', 'CurrentLiabilities', 'Current Debt And Capital Lease Obligation'], latest)

        # derived metrics
        roe = np.nan
        if pd.notna(netincome_latest) and pd.notna(equity_latest) and equity_latest != 0:
            roe = netincome_latest / equity_latest

        roa = np.nan
        if pd.notna(netincome_latest) and pd.notna(assets_latest) and assets_latest != 0:
            roa = netincome_latest / assets_latest

        debt_equity = np.nan
        if pd.notna(total_debt_latest) and pd.notna(equity_latest) and equity_latest != 0:
            debt_equity = total_debt_latest / equity_latest

        net_debt_latest = np.nan
        if pd.notna(total_debt_latest) and pd.notna(cash_latest):
            try:
                net_debt_latest = float(total_debt_latest) - float(cash_latest)
            except Exception:
                net_debt_latest = np.nan

        net_debt_to_ebitda = np.nan
        if pd.notna(net_debt_latest) and pd.notna(ebitda_latest) and ebitda_latest != 0:
            net_debt_to_ebitda = net_debt_latest / ebitda_latest

        fcf_margin = np.nan
        if pd.notna(free_cash_flow_latest) and pd.notna(revenue_latest) and revenue_latest != 0:
            fcf_margin = free_cash_flow_latest / revenue_latest

        current_ratio = np.nan
        if pd.notna(current_assets_latest) and pd.notna(current_liabilities_latest) and current_liabilities_latest != 0:
            current_ratio = current_assets_latest / current_liabilities_latest

        results.append({
            'ticker': ticker,
            'date_latest': latest,
            'revenue_latest': revenue_latest,
            'revenue_prev': revenue_prev,
            'revenue_yoy': revenue_yoy,
            'netincome_latest': netincome_latest,
            'margin_latest': margin_latest,
            'assets_latest': assets_latest,
            'equity_latest': equity_latest,
            'total_debt_latest': total_debt_latest,
            'cash_latest': cash_latest,
            'net_debt_latest': net_debt_latest,
            'ebitda_latest': ebitda_latest,
            'free_cash_flow_latest': free_cash_flow_latest,
            'fcf_margin': fcf_margin,
            'roa': roa,
            'roe': roe,
            'debt_equity': debt_equity,
            'net_debt_to_ebitda': net_debt_to_ebitda,
            'current_ratio': current_ratio,
        })

    out = pd.DataFrame(results).set_index('ticker')
    return out


def score_tickers(df_metrics: pd.DataFrame, criteria: Dict[str, Tuple[str, float]]) -> pd.DataFrame:
    """Compute percentile-based scores and combined ranking.

    criteria: dict mapping metric column -> (direction, weight)
      - direction: 'higher' means higher metric is better, 'lower' means lower is better
      - weight: numeric weight (sums need not be 1)

    Returns df_metrics with added per-criterion score columns and 'score' and 'rank'.
    """
    if df_metrics.empty:
        return df_metrics

    df = df_metrics.copy()
    score_cols = []
    for metric, (direction, weight) in criteria.items():
        col = f'score_{metric}'
        score_cols.append(col)
        if metric not in df.columns:
            df[col] = np.nan
            continue

        vals = df[metric]
        # compute percentile rank in [0,1]
        # handle NaNs by leaving them as NaN
        ranks = vals.rank(method='average', pct=True, na_option='keep')
        if direction == 'higher':
            score = ranks
        else:
            score = 1.0 - ranks

        df[col] = score * float(weight)

    # combined score
    df['score'] = df[[c for c in df.columns if c.startswith('score_')]].sum(axis=1, skipna=False)
    # smaller score is worse; compute rank (1 best)
    df['rank'] = df['score'].rank(ascending=False, method='min')
    df = df.sort_values('rank')
    return df


if __name__ == '__main__':
    # quick demo: process one CSV and print metrics + score
    import argparse
    from stockpicker.compile_financials import process_file_to_long

    parser = argparse.ArgumentParser(description='Demo metric extraction and ranking for one CSV')
    parser.add_argument('csv', help='one financials CSV to analyze')
    args = parser.parse_args()

    long = process_file_to_long(args.csv)
    metrics = extract_metrics_from_long_df(long)
    print('Extracted metrics:')
    print(metrics)

    # example criteria: favour higher revenue_yoy and higher margin
    crit = {
        'revenue_yoy': ('higher', 0.6),
        'margin_latest': ('higher', 0.4),
    }
    scored = score_tickers(metrics, crit)
    print('\nScored:')
    print(scored)
