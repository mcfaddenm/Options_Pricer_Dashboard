import datetime

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
        raw_signal = pd.DataFrame(np.where(sma50 < sma200, -1, raw_signal).astype(np.int_), index=sma200.index,
                                  columns=cls_price.columns)
        # Compute boolean mask where signal changes
        mask = (raw_signal != raw_signal.shift())
        # Final dataframe containing trading signals
        signals = raw_signal.where(mask, 0)

        return signals


class LongStrategy:
    def __init__(self, assets, start, end):
        self.assets = assets
        self.start = start
        self.end = end

    def generate_signals(self):
        # Convert start and end dates to datetime objects
        start_date_obj = datetime.datetime.strptime(self.start, '%Y-%m-%d')
        end_date_obj = datetime.datetime.strptime(self.end, '%Y-%m-%d')
        # List of dates
        date_list = [start_date_obj.date() + datetime.timedelta(days=x) for x in
                     range((end_date_obj - start_date_obj).days + 1)]
        # An empty dataframe
        signals = pd.DataFrame(0, index=date_list, columns=self.assets)

        return signals


class EWMAverageCrossoverStrategy:
    def __init__(self, assets, start, end):
        self.assets = assets
        self.start = start
        self.end = end

    def generate_signals(self):
        # Downloads closing price history
        tickers = yf.Tickers(self.assets)
        cls_price = tickers.history(start=self.start, end=self.end, interval="1d")['Close']

        # Computes the short-term and long-term EWMA for the portfolio
        ewma_short = cls_price.ewm(span=50, adjust=False).mean().dropna()
        ewma_long = cls_price.ewm(span=200, adjust=False).mean().dropna()
        ewma_short = ewma_short[ewma_short.index.isin(ewma_long.index)]

        # Creates a dataframe containing raw signal data from the EWMA crossovers
        raw_signal = np.where(ewma_short > ewma_long, 1, 0)
        raw_signal = pd.DataFrame(np.where(ewma_short < ewma_long, -1, raw_signal).astype(np.int_), index=ewma_short.index,
                                  columns=cls_price.columns)
        # Compute boolean mask where signal changes
        mask = (raw_signal != raw_signal.shift())
        # Final dataframe containing trading signals
        signals = raw_signal.where(mask, 0)

        return signals
