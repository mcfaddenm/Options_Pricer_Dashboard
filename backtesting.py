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
        self.strategy = strategy

    def run(self):
        # Get price data for assets
        tickers = yf.Tickers(self.assets)
        cls_price = tickers.history(start=self.start, end=self.end, interval="1d")['Close']
        returns = cls_price.pct_change()[1:]

        # Generate buy/sell signals
        signals = self.strategy.generate_signals()

        weights = pd.DataFrame(1 / 6, index=signals.index, columns=self.portfolio.index)
        portfolio_weights = pd.DataFrame(columns=signals.columns)

        jpst_index = weights.columns.get_loc('JPST')
        signals_values = signals.values
        weights_values = self.portfolio.Weights.values
        portfolio_values = portfolio_weights.values

        for i in range(len(signals)):
            jpst_weight = weights_values[jpst_index]
            other_weights = weights_values[:jpst_index] + weights_values[jpst_index + 1:]

            signals_row = signals_values[i]
            updated_weights = weights_values.copy()

            for j in range(len(signals.columns)):
                if j == jpst_index:
                    continue

                signal = signals_row[j]
                if signal == 1:
                    delta = -0.05
                elif signal == -1:
                    delta = 0.05
                else:
                    delta = 0.0

                if delta != 0 and other_weights.sum() > 0:
                    new_weight = updated_weights[j] * (1 + delta)
                    jpst_delta = -delta * other_weights.sum() / jpst_weight

                    if jpst_weight <= jpst_delta:
                        new_weight += jpst_weight
                        jpst_delta = jpst_weight

                    updated_weights[j] = max(new_weight, 0)
                    updated_weights[jpst_index] = max(jpst_weight + jpst_delta, 0)

            total_weight = updated_weights.sum()
            if total_weight > 0:
                updated_weights /= total_weight

            weights_values = updated_weights
            portfolio_values[i] = updated_weights

        portfolio_weights = pd.DataFrame(portfolio_values, index=signals.index, columns=signals.columns)

        # Calculate weighted returns
        weighted_returns = (returns * weights).sum(axis=1)
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
