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
        self.cash = cash
        self.strategy = strategy
        self.pnl = 0

    def initPort(self):
        # Get price data for assets
        tickers = yf.Tickers(self.assets)
        prices = tickers.history(start=self.start, end=self.end, interval="1d")['Close'].iloc[0]

        # Adds purchase price to dataframe
        self.portfolio['Price'] = prices

        # Calculate the number of shares
        self.portfolio['Shares'] = np.floor((self.portfolio.Weights * self.cash) / prices)

        # Calculates cost of portfolio and updates the cash holdings
        cost = np.matmul(self.portfolio.Price, self.portfolio.Shares)
        self.cash -= cost

        # Recalculate the weights
        self.portfolio['Weights'] = self.portfolio.Shares / sum(self.portfolio.Shares)

    def transact(self, signal, asset, price, shares):
        # 1 == purchase transaction
        # -1 == sell transaction

        if signal == 1:
            cost = price * shares
            if cost > self.cash:
                print("NOT ENOUGH CASH")
            else:
                # Subtract the price to purchase from current cash holdings
                self.cash -= cost

                # Records new price as average of old and new price
                old_price = self.portfolio.loc[asset, 'Price']
                avg_price = 0.5 * (old_price + price)
                self.portfolio.loc[asset, 'Price'] = avg_price

                # Update the number of shares held for asset
                self.portfolio.loc[asset, 'Shares'] += shares

                # Recalculate portfolio weights
                self.portfolio.Weights = self.portfolio.Shares / sum(self.portfolio.Shares)
            return 0
        elif signal == -1:
            # Current Price
            current_price = price
            # Previous Price
            prev_price = self.portfolio.loc[asset, 'Price']

            # Asserts that there is enough shares to sell
            rem_shares = self.portfolio.loc[asset, 'Shares']
            if rem_shares < shares:
                return 0
            else:
                # Calculates and updates proceeds
                proceeds = shares * price
                self.cash += proceeds

                # Updates the number of shares
                self.portfolio.loc[asset, 'Shares'] -= shares

                # Recalculate portfolio weights
                self.portfolio.Weights = self.portfolio.Shares / sum(self.portfolio.Shares)

                # Calculates PnL
                self.pnl += (current_price - prev_price) * shares
                return self.pnl

    def run(self):
        # Get price data for assets
        tickers = yf.Tickers(self.assets)
        print(self.assets)
        closing_price = tickers.history(start=self.start, end=self.end, interval="1d")['Close']

        # Uses percent difference method to calculate daily returns
        returns = closing_price.pct_change()[1:]

        # Generate buy/sell signals
        signals = self.strategy.generate_signals()

        # Initializes dataframe for daily portfolio tracking
        daily_records = pd.DataFrame(0.0, index=signals.index, columns=['Securities', 'Cash', 'PnL'])
        pnl = 0.0
        for index, day in signals.iterrows():
            for asset in self.assets:
                if signals.loc[index, asset] == 1:
                    print(datetime.datetime.strftime(index, '%Y-%m-%d'), "BUY", asset, "@ price $", round(closing_price.loc[index, asset], 3))
                    pnl = self.transact(1, asset=asset, price=closing_price.loc[index, asset], shares=150)
                elif signals.loc[index, asset] == -1:
                    print(datetime.datetime.strftime(index, '%Y-%m-%d'), "SELL", asset, "@ price: $", round(closing_price.loc[index, asset], 3))
                    pnl = self.transact(-1, asset=asset, price=closing_price.loc[index, asset], shares=150)
                else:
                    self.portfolio.Price = closing_price.loc[index]
            # Adds daily record
            daily_records.loc[index] = [np.matmul(self.portfolio.Price, self.portfolio.Shares), self.cash, self.pnl]

        return daily_records

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
        portfolio_annual_return = ((1 + portfolio_cumulative_return) ** (252 / len(portfolio_value.index))) - 1

        # Use numexpr to evaluate complex numerical expressions with high performance
        portfolio_sharpe_ratio = (portfolio_annual_return - 0.035) / portfolio_volatility

        performance = [portfolio_volatility, portfolio_annual_return, portfolio_sharpe_ratio]

        print("Portfolio Volatility: ", performance[0])
        print("Portfolio Annual Return: ", performance[1])
        print("Portfolio Sharpe Ratio: ", performance[2])

        return performance

    def update_portfolio(self, portfolio: pd.DataFrame):
        # Add cash position to portfolio
        portfolio.loc['JPST'] = self.portfolio.Weights.loc['JPST'] * self.cash
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
