"""Finviz-based stock screener for undervalued stocks."""

from finvizfinance.screener.overview import Overview
import pandas as pd

from stockpicker import get_output_dir


def get_undervalued_stocks():
    """
    Returns a list of tickers with:

    - Positive Operating Margin
    - Debt-to-Equity ratio under 1
    - Low P/B (under 1)
    - Low P/E ratio (under 15)
    - Low PEG ratio (under 1)
    - Positive Insider Transactions
    """
    foverview = Overview()
    filters_dict = {
        'Debt/Equity': 'Under 1',
        'PEG': 'Low (<1)',
        'Operating Margin': 'Positive (>0%)',
        'P/B': 'Low (<1)',
        'P/E': 'Low (<15)',
        'InsiderTransactions': 'Positive (>0%)',
    }
    foverview.set_filter(filters_dict=filters_dict)
    df_overview = foverview.screener_view()
    output_dir = get_output_dir()
    df_overview.to_csv(str(output_dir / 'Overview.csv'), index=False)
    tickers = df_overview['Ticker'].to_list()
    return tickers


if __name__ == '__main__':
    print(get_undervalued_stocks())
