import pandas
import pandas as pd
import yfinance as yf
import numpy as np
import numexpr as ne
from trading_strats import *

class Backtest:
    def __init__(self, start, end, strategy, portfolio, cash):
        # Cash is invested into a money market ETF
        cash = pd.DataFrame(dict(Tickers=['JPST'], Weights=[cash])).set_index('Tickers')
        portfolio = pd.concat([portfolio, cash], axis=0)
        # Class objects
        self.start = start
        self.end = end
        self.portfolio = portfolio
        self.assets = list(self.portfolio.index)
        self.equity = sum(self.portfolio.Weights)
        self.portfolio.Weights = self.portfolio.Weights / self.equity
        self.strategy = strategy = MovingAverageCrossoverStrategy(self.assets, self.start, self.end)

    def run(self):
        # Get price data for assets
        tickers = yf.Tickers(self.assets)
        cls_price = tickers.history(start=self.start, end=self.end, interval="1d")['Close']
        returns = cls_price.pct_change()[1:]

        # Generate buy/sell signals
        signals = self.strategy.generate_signals()


        weights = self.portfolio.Weights.copy()
        portfolio_weights = pd.DataFrame(index=signals.index, columns=signals.columns)

        # Calculate weights for each asset and day
        for day in signals.index:
            for asset in signals.columns:
                if signals.loc[day, asset] == 1:
                    weights[asset] += 0.1
                elif signals.loc[day, asset] == -1:
                    weights[asset] -= 0.1
            if any(signals.loc[day] != 0):
                portfolio_weights.loc[day] = weights

        # Calculate weighted returns
        weighted_returns = (returns * weights).sum(axis=1)
        portfolio_returns = (1 + weighted_returns).cumprod() * self.equity

        return portfolio_returns, weights

    def generate_report(self):
        # Gets portfolio values over time with weights
        portfolio_value, portfolio_weights = self.run()

        # Portfolio log difference change
        portfolio_returns = portfolio_value.pct_change()

        # Pre-compute portfolio_value[-1] and portfolio_value[0]
        portfolio_value_end = portfolio_value[-1]
        portfolio_value_start = portfolio_value[0]

        # Use numpy functions to perform calculations on arrays
        portfolio_volatility = 100 * (np.std(portfolio_returns, ddof=0) * np.sqrt(252))
        portfolio_cumulative_return = 100 * ((portfolio_value_end - portfolio_value_start) / portfolio_value_start)

        # Use numexpr to evaluate complex numerical expressions with high performance
        portfolio_sharpe_ratio = ne.evaluate(
            "((portfolio_cumulative_return / 100) - 0.035) / (portfolio_volatility / 100)")

        performance = [portfolio_volatility, portfolio_cumulative_return, float(portfolio_sharpe_ratio)]

        print("Portfolio volatility: ", performance[0])
        print("Portfolio Return: ", performance[1])
        print("Portfolio Sharpe Ratio: ", performance[2])

        return performance

    def update_portfolio(self, portfolio: pandas.DataFrame):
        # Add cash position to portfolio
        portfolio.loc['JPST'] = 1000
        self.portfolio = portfolio

        # Convert portfolio to dataframe and normalize weights
        self.portfolio['Weights'] = np.divide(self.portfolio['Weights'], np.sum(self.portfolio['Weights']))

        # Get list of assets in portfolio
        self.assets = self.portfolio.index.tolist()

        # Updates the strategy
        self.strategy = MovingAverageCrossoverStrategy(self.assets, self.start, self.end)

    def get_portfolio(self):
        # Returns the current portfolio in-use by the backtesting model
        return self.portfolio


