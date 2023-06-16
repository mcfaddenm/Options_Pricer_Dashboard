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
            if shares > self.portfolio.loc[asset, 'Shares']:
                print("NOT ENOUGH SHARES")
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
        daily_records = pd.DataFrame(0.0, index=signals.index, columns=['Securities', 'Cash', 'RPnL', 'UPnL'])
        pnl = 0.0
        for index, day in signals.iterrows():
            for asset in self.assets:
                if signals.loc[index, asset] == 1:
                    print(datetime.datetime.strftime(index, '%Y-%m-%d'), "BUY", asset, "@ price $",
                          round(closing_price.loc[index, asset], 3))
                    pnl = self.transact(1, asset=asset, price=closing_price.loc[index, asset], shares=np.floor(0.3 * self.portfolio.loc[asset, 'Shares']))
                elif signals.loc[index, asset] == -1:
                    print(datetime.datetime.strftime(index, '%Y-%m-%d'), "SELL", asset, "@ price: $",
                          round(closing_price.loc[index, asset], 3))
                    pnl = self.transact(-1, asset=asset, price=closing_price.loc[index, asset], shares=np.floor(0.1 * self.portfolio.loc[asset, 'Shares']))
                else:
                    self.portfolio.Price = closing_price.loc[index]
            # Adds daily record
            port_value = np.matmul(self.portfolio.Price, self.portfolio.Shares)
            daily_records.loc[index] = [port_value, self.cash, self.pnl, (port_value + self.cash) - self.equity]

        return daily_records

    def generate_report(self, records):
        # Calculating percent change
        a = np.sum(records.iloc[:, 0:2], axis=1)
        pct_returns = np.diff(a) / a[1:]
        pct_returns = pd.DataFrame(np.insert(pct_returns, 0, 0.0, axis=0), columns=['Returns'])

        values = pd.DataFrame(np.sum(records.iloc[:, 0:2], axis=1), index=records.index, columns=['Values'])
        returns = pd.DataFrame(np.diff(values.Values), index=records.index[1:], columns=['Returns'])

        max_ret, min_ret = max(returns.Returns), min(returns.Returns)
        print("MAX DRAWDOWN:", returns.index[returns.Returns == min_ret].date[0].strftime('%Y-%m-%d'), round(min_ret, 3))
        print("GOLDEN TICKET:", returns.index[returns.Returns == max_ret].date[0].strftime('%Y-%m-%d'), round(max_ret, 3))

        # Need to get a more refined process
        years = int(self.end[0:4]) - int(self.start[0:4])
        exp_ret = 100 * (((np.sum(records.iloc[len(records)-1, 0:2], axis=0) / np.sum(records.iloc[0, 0:2])) ** (1/years)) - 1)
        vol = np.std(pct_returns.Returns) * np.sqrt(252) * 100
        print("PORTFOLIO VOLATILITY:", round(vol, 3))
        print("PORTFOLIO RETURN:", round(exp_ret, 3))
        print("SHARPE RATIO:", round((exp_ret - 2.25)/vol, 3))

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
