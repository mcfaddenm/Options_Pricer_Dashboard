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
        self.strategy = strategy

    def run(self):
        # Get price data for assets
        tickers = yf.Tickers(self.assets)
        cls_price = tickers.history(start=self.start, end=self.end, interval="1d")['Close']
        returns = cls_price.pct_change()[1:]

        # Generate buy/sell signals
        signals = self.strategy.generate_signals()

        portfolio_weights = pd.DataFrame([self.portfolio.Weights.values] * len(signals), index=signals.index, columns=self.assets)

        SIG_index = signals.columns
        for i, day in enumerate(signals.index[1:], start=1):
            new_weights = portfolio_weights.iloc[i-1].copy(deep=True)
            for asset in SIG_index:
                if signals.loc[day, asset] == 1:
                    delta = 0.05
                elif signals.loc[day, asset] == -1:
                    delta = -0.05
                else:
                    delta = 0.0

                if delta != 0:
                    new_weights.loc[asset] *= (1 + delta)
                    new_weights.loc['JPST'] *= (1 - delta)

            portfolio_weights.loc[day] = new_weights.values

        # returns = returns[returns.index.isin(portfolio_weights)]
        # Calculate weighted returns
        weighted_returns = np.multiply(returns, portfolio_weights).sum(axis=1)
        portfolio_returns = (1 + weighted_returns).cumprod() * self.equity

        return portfolio_returns, portfolio_weights

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
