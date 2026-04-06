# testing yahoo finance API functions

#%%
from matplotlib.pylab import size
import yfinance as yf
import pandas as pd
import time


# ticker = yf.Ticker('AAAA')  # not just 'AAPL'
# s = ticker.balance_sheet
# print(s)

#%%
from pathlib import Path
import pandas as pd
import os

DEFAULT_OUTPUT_DIR = os.getenv('DEFAULT_OUTPUT_DIR', 'out')
ROOT = Path.cwd()                             # where you ran the command from
csv_path = ROOT / DEFAULT_OUTPUT_DIR / 'tickers.csv'
tickers_csv = pd.read_csv(csv_path)

#%%
from pathlib import Path
# run from repo root (or use full path)
ROOT = Path.cwd()

folder = ROOT / 'financials'
trash = Path.home() / '.Trash'
threshold = 512  # bytes

small_csvs = [p for p in folder.rglob('*.csv') if p.is_file() and p.stat().st_size < threshold]



from shutil import move

for p in small_csvs:
    if p.is_file() and p.stat().st_size < threshold:
        dest = trash / p.name
        # handle name collisions by appending a suffix if needed
        i = 1
        while dest.exists():
            dest = trash / f"{p.stem}_{i}{p.suffix}"
            i += 1
        move(str(p), str(dest))
        # print('moved', p, '->', dest)
print('found', len(small_csvs), 'small csv files')
# 6001 small files moved

# %%

# from compile_financials import process_file_to_long
# df = process_file_to_long("financials/AAPL_financials.csv")



# %%
