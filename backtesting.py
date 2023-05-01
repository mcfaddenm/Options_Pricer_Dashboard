import yfinance as yf

portfolio = ['AAPL', 'GLD', 'MSFT', 'TMUS']

tickers = yf.Tickers(portfolio)
tickers_hist = tickers.history(period='5y')['Close']

class Backtest:
    def __init__(self, data, strategy):
        self.data = data
        self.strategy = strategy
        self.positions = None
        self.trades = None
        self.equity = None

    def run(self):
        self.positions = self.strategy.generate_positions(self.data)
        self.trades = self.generate_trades(self.positions)
        self.equity = self.calculate_equity()

    def generate_trades(self, positions):
        # Generates trades based on positions
        pass

    def calculate_equity(self):
        # Calculates equity based on trades
        pass

    def generate_report(self):
        # Generates a report of performance metrics
        pass
