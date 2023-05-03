import pandas as pd
import yfinance as yf
import numpy as np
class Backtest:
    def __init__(self, data, strategy, start, end, portfolio):
        self.data = data
        self.strategy = strategy
        self.start = start
        self.end = end
        self.portfolio = portfolio
        self.equity = None

    def run(self):
        tickers = yf.Tickers(self.portfolio['Tickers'].tolist())
        cls_price = tickers.history(start=self.start, end=self.end, interval="1d")['Close']
        wts = self.portfolio.Shares/(sum(self.portfolio.Shares))
        returns = cls_price.pct_change()
        weighted_returns = np.multiply(np.asarray(wts), returns[1:])
        portfolio_ret = weighted_returns.sum(axis=1)
        cum_returns = (1 + portfolio_ret).cumprod()

        return cum_returns * sum(self.portfolio.Shares)

    def generate_report(self):
        # Generates a report of performance metrics
        pass

    def update_portfolio(self, portfolio: dict):
        ## Allows portfolio to be updated by user
        self.portfolio = pd.DataFrame(portfolio)

    def get_portfolio(self):
        # Returns the current portfolio in-use by the backtesting model
        wts = self.portfolio.Shares/sum(self.portfolio.Shares)
        cash = sum(self.portfolio.Shares)
        return wts, cash