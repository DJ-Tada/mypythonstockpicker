# MyPythonStockPicker

A Python-based stock screening and financial analysis toolkit that fetches US stock tickers, downloads financial statements, screens for undervalued stocks, scores them on fundamental metrics, and performs news sentiment analysis.

## Features

- **Ticker fetching** — pulls all active US stock tickers from the Massive.com API
- **Financial data download** — batch-downloads balance sheets, income statements, and cash flow statements via yfinance
- **Fundamental screening** — Finviz-based screener filtering for low debt, low P/E, low P/B, low PEG, and positive margins
- **Financial scoring** — extracts key metrics (revenue growth, margins, ROE, ROA, debt-to-equity, current ratio, etc.) and produces a percentile-based combined ranking
- **Sentiment analysis** — uses FinBERT to classify news headlines as positive, negative, or neutral

## Setup

```bash
# 1. Clone the repo
git clone https://github.com/DJ-Tada/mypythonstockpicker.git
cd mypythonstockpicker

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your local config
cp config.template.py config.py
# Edit config.py and fill in your API keys (MASSIVE_API_KEY, etc.)
```

> **Note:** `config.py` is git-ignored. Never commit it — use `config.template.py` as the reference for required settings.

## Usage

All commands are run from the project root.

```bash
# Fetch tickers from Massive.com and download financial statements
python -m stockpicker.fetch_tickers

# Run the full analysis pipeline (compile financials → summarise → score)
python -m stockpicker.run_full_summary

# Run the Finviz stock screener
python -m stockpicker.screener
```

## Project Structure

```
MyPythonStockPicker/
├── config.template.py          # Config placeholder (tracked)
├── config.py                   # Local config with real secrets (git-ignored)
├── requirements.txt            # Python dependencies
├── data/                       # Static / cached data files
├── output/                     # Generated output (git-ignored)
│   ├── financials/             # Per-ticker financial CSVs
│   ├── financials_scored.csv   # Scored & ranked tickers
│   ├── financials_summary.csv  # One-row-per-ticker summary
│   └── Overview.csv            # Finviz screener results
├── stockpicker/
│   ├── __init__.py             # Package init & output dir helper
│   ├── fetch_tickers.py        # Fetch tickers & download financials
│   ├── run_full_summary.py     # Orchestrate full analysis pipeline
│   ├── compile_financials.py   # Compile per-ticker CSVs into unified datasets
│   ├── financial_utils.py      # Ticker list helpers, batch download, fill checks
│   ├── query_financials.py     # Extract metrics, score & rank tickers
│   ├── screener.py             # Finviz undervalued-stock screener
│   └── sentiment.py            # FinBERT news sentiment analysis
└── sandbox/                    # Experimental / scratch scripts
```

## Key Dependencies

| Library | Purpose |
|---------|---------|
| `yfinance` | Financial statement downloads |
| `finvizfinance` | Stock screening via Finviz |
| `transformers` | FinBERT sentiment model |
| `goose3` | Article text extraction for sentiment |
| `pandas` | Data manipulation |
| `tqdm` | Progress bars |

## License

Private repository — not licensed for redistribution.
