#%%
# Source: https://www.geeksforgeeks.org/python/comparing-yfinance-vs-yahoofin-in-python/

# Which Should You Use?
# Choosing between yfinance and yahoo_fin depends on your specific needs:

# Use yfinance if you need extensive historical data, access to various types of market data, and additional financial metrics. It's particularly useful for in-depth historical quantitative analysis.
# Use yahoo_fin if you're more focused on current market conditions, earnings information, and news. It's ideal for applications that need current data and insights into market sentiment.

# yfinance is suitable for:

# Historical Data Analysis: Historians, analysts, and researchers who deploys the information from statistical technique.
# Real-time Market Monitoring: Those who require up-to-date and real-time information about the stocks, the trading prices, and such other features.
# Financial Statement Analysis: Academic researchers using financial statements for their studies, businesses looking to invest in the company and other people interested in the company.
# yahoo_fin is ideal for:

# Quick Data Access: Financial desks of various developers who require quick access to several financial data and news from Yahoo Finance.
# Additional Data Types: Some of the corporate enthusiasts and people who prefer other parameters as volumetric indicators in the financial market such as options data, headlines and other financial oddities.
# Scraping Requirements: Scraping requirements for projects that go beyond the normal HTTP/REST API request access.



#%%
import yahoo_fin.stock_info as yf

ticker = "NFLX"
balance_sheet = yf.get_balance_sheet(ticker)
print(balance_sheet)

#%%
import yfinance as yf # api for yahoo finance
import matplotlib.pyplot as plt

# Define the stock symbol and the time period
stock_symbol = 'AAPL'
start_date = '2022-01-01'
end_date = '2023-01-01'

# Fetch the historical data
stock_data = yf.download(stock_symbol, start=start_date, end=end_date)

# Display the data
print(stock_data.head())

# Plot the closing prices
plt.figure(figsize=(10, 5))
plt.plot(stock_data['Close'], label='Close Price')
plt.title(f'Closing Prices of {stock_symbol}')
plt.xlabel('Date')
plt.ylabel('Close Price USD')
plt.legend()
plt.grid()
plt.show()

#%%

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import yfinance as yf

#%%

# msft = yf.Ticker("MSFT")
# msft.info
hist = msft.history(period="max")
# msft.recommendations
hist.plot(kind = 'line', figsize = (12, 12), subplots = True, title = 'MSFT Stock Historical Data')
#%%

# msft.income_stmt
# msft.balance_sheet
# msft.cashflow
# msft.earnings
# msft.sustainability
# msft.calendar
# msft.options
# msft.dividends.plot(kind = 'line', figsize = (12, 6), title = 'MSFT Dividends History')

#actions, analyst_price_targets, balance_sheet, balancesheet, calendar, capital_gains, cash_flow, cashflow, dividends, earnings, earnings_dates, earnings_estimate, earnings_history, eps_revisions, eps_trend, fast_info, financials, funds_data, growth_estimates, history_metadata, income_stmt, incomestmt, info, insider_purchases, insider_roster_holders, insider_transactions, institutional_holders, isin, major_holders, mutualfund_holders, news, options, quarterly_balance_sheet, quarterly_balancesheet, quarterly_cash_flow, quarterly_cashflow, quarterly_earnings, quarterly_financials, quarterly_income_stmt, quarterly_incomestmt, recommendations, recommendations_summary, revenue_estimate, sec_filings, shares, splits, sustainability, ttm_cash_flow, ttm_cashflow, ttm_financials, ttm_income_stmt, ttm_incomestmt, upgrades_downgrades
#%%

# US
# GB
# ASIA
# EUROPE
# RATES
# COMMODITIES
# CURRENCIES
# CRYPTOCURRENCIES
# only seems to be giving US market data?
# EUROPE = yf.Market("EUROPE")
# status = EUROPE.status
# summary = EUROPE.summary
# summary

#%%

# doesn't work, issue raised on github
# import get_all_tickers

# get_tickers(NYSE=True, NASDAQ=True, AMEX=True)

# from get_all_tickers import get_tickers
# get_tickers

#%%
# Paper on how to get ticker symbols from various exchanges
# https://medium.com/@RealCharlie/sourcing-a-free-list-of-global-stock-tickers-db8bd30019ec
