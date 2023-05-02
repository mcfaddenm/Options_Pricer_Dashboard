import yfinance as yf

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
        returns = cls_price.pct_change()
        cum_returns = (1 + returns).cumprod()
        print(cum_returns)

    def generate_report(self):
        # Generates a report of performance metrics
        pass
