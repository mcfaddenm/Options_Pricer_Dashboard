import pandas as pd
import yfinance as yf
import numpy as np
import numexpr as ne
import datetime
from trading_strats import *


class Backtest:
    def __init__(self, start, end, strategy, portfolio, cash):
        # Class objects
        self.start = start
        self.end = end
        self.portfolio = portfolio
        self.assets = list(self.portfolio.index)
        self.equity = cash
        self.strategy = strategy

    def run(self):
        # Get price data for assets
        tickers = yf.Tickers(self.assets)
        closing_price = tickers.history(start=self.start, end=self.end, interval="1d")['Close']

        # Uses percent difference method to calculate daily returns
        returns = closing_price.pct_change()[1:]

        # Generate buy/sell signals
        signals = self.strategy.generate_signals()

        days = closing_price.index.strftime('%Y-%m-%d')

        for index, day in signals.iterrows():
            print(index, "-------", closing_price.loc[index], "-----", signals.loc[index])

        return 1

    def generate_report(self):
        # Gets portfolio values over time with weights
        portfolio_value, portfolio_weights = self.run()

        # Portfolio log difference change
        portfolio_returns = portfolio_value.pct_change()

        # Pre-compute portfolio_value[-1] and portfolio_value[0]
        portfolio_value_end = portfolio_value[-1]
        portfolio_value_start = portfolio_value[0]

        # Use numpy functions to perform calculations on arrays
        portfolio_volatility = (np.std(portfolio_returns, ddof=1) * np.sqrt(252))
        portfolio_cumulative_return = (portfolio_value_end - portfolio_value_start) / portfolio_value_start
        portfolio_annual_return = ((1 + portfolio_cumulative_return) ** (252/len(portfolio_value.index))) - 1

        # Use numexpr to evaluate complex numerical expressions with high performance
        portfolio_sharpe_ratio = (portfolio_annual_return - 0.035) / portfolio_volatility

        performance = [portfolio_volatility, portfolio_annual_return, portfolio_sharpe_ratio]

        print("Portfolio Volatility: ", performance[0])
        print("Portfolio Annual Return: ", performance[1])
        print("Portfolio Sharpe Ratio: ", performance[2])

        return performance

    def update_portfolio(self, portfolio: pd.DataFrame):
        # Add cash position to portfolio
        portfolio.loc['JPST'] = self.portfolio.Weights.loc['JPST'] * self.equity
        self.portfolio = portfolio

        # Convert portfolio to dataframe and normalize weights
        self.portfolio['Weights'] = np.divide(self.portfolio['Weights'], np.sum(self.portfolio['Weights']))

        # Get list of assets in portfolio
        self.assets = portfolio.index.tolist()

        # Updates the strategy
        # self.strategy = MovingAverageCrossoverStrategy(self.assets, self.start, self.end)

    def get_portfolio(self):
        # Returns the current portfolio in-use by the backtesting model
        return self.portfolio

    def initPort(self):
        # Get price data for assets
        tickers = yf.Tickers(self.assets)
        prices = tickers.history(start=self.start, end=self.end, interval="1d")['Close'].iloc[0]

        # Calculate the number of shares
        self.portfolio['Shares'] = (self.portfolio.Weights * self.equity)/prices