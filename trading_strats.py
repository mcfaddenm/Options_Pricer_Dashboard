import pandas as pd
import numpy as np
import yfinance as yf

class MovingAverageCrossoverStrategy:
    def __init__(self, assets, start, end):
        self.assets = assets
        self.start = start
        self.end = end

    def generate_signals(self):
        # Downloads closing price history from
        tickers = yf.Tickers(self.assets)
        cls_price = tickers.history(start=self.start, end=self.end, interval="1d")['Close']

        # Computes the 50-day SMA 200-day SMA for the portfolio
        sma50 = cls_price.rolling(window=50).mean().dropna()
        sma200 = cls_price.rolling(window=200).mean().dropna()
        sma50 = sma50[sma50.index.isin(sma200.index)]

        # Creates a dataframe containing raw signal data from the SMA crossovers
        raw_signal = np.where(sma50 > sma200, 1, 0)
        raw_signal = pd.DataFrame(np.where(sma50 < sma200, -1, raw_signal).astype(np.int_), index=sma200.index, columns=cls_price.columns)
        # Compute boolean mask where signal changes
        mask = (raw_signal != raw_signal.shift())
        # Final dataframe containing trading signals
        signals = raw_signal.where(mask, 0)

        return signals