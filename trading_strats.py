import datetime
import pandas as pd
import numpy as np
import yfinance as yf


class Long:
    def __init__(self, assets, start, end):
        self.assets = assets
        self.start = start
        self.end = end

    def generate_signals(self):
        # Downloads closing price history from
        tickers = yf.Tickers(self.assets)
        cls_price = tickers.history(start=self.start, end=self.end, interval="1d")['Close']

        # An empty dataframe
        signals = pd.DataFrame(0, index=cls_price.index, columns=self.assets)

        return signals

    def updateAssets(self, assets: list):
        self.assets = assets


class SMA:
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

        # Initialize the raw_signal dataframe with zeros
        raw_signal = pd.DataFrame(0, index=cls_price.index, columns=self.assets)

        # Generate boolean masks for crossover conditions
        crossover_up = sma50 > sma200
        crossover_down = sma50 < sma200

        # Calculate the first occurrence of crossover for each asset
        first_crossover_up = crossover_up & (~crossover_up.shift(fill_value=False))
        first_crossover_down = crossover_down & (~crossover_down.shift(fill_value=False))

        # Compute boolean mask where signal changes
        mask = (raw_signal != raw_signal.shift())
        # Final dataframe containing trading signals
        signals = raw_signal.where(mask, 0)

        return signals

    def updateAssets(self, assets: list):
        self.assets = assets


class EWMA:
    def __init__(self, assets, start, end):
        self.assets = assets
        self.start = start
        self.end = end

    def generate_signals(self):
        # Downloads closing price history
        tickers = yf.Tickers(self.assets)
        cls_price = tickers.history(start=self.start, end=self.end, interval="1d")['Close']

        # Computes the short-term and long-term EWMA for the portfolio
        ewma_long = cls_price.ewm(span=100, adjust=False).mean().dropna()
        ewma_short = cls_price.ewm(span=30, adjust=False).mean().dropna()
        ewma_short = ewma_short[ewma_short.index.isin(ewma_long.index)]

        # Initialize the raw_signal dataframe with zeros
        raw_signal = pd.DataFrame(0, index=cls_price.index, columns=self.assets)

        # Generate boolean masks for crossover conditions
        crossover_up = ewma_short > ewma_long
        crossover_down = ewma_short < ewma_long

        # Calculate the first occurrence of crossover for each asset
        first_crossover_up = crossover_up & (~crossover_up.shift(fill_value=False))
        first_crossover_down = crossover_down & (~crossover_down.shift(fill_value=False))

        # Update the raw_signal dataframe with the first crossover values
        raw_signal[first_crossover_up] = -1
        raw_signal[first_crossover_down] = 1

        return raw_signal

    def updateAssets(self, assets: list):
        self.assets = assets
