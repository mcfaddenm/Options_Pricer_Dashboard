from matplotlib import pyplot as plt
from trading_strats import *


class Backtest:
    def __init__(self, start, end, strategy, portfolio, cash):
        # Class objects
        self.start = start
        self.end = end
        self.bench = pd.DataFrame()
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

        # Downloads information for benchmarks
        tickers = yf.Tickers(['SPY', 'BND'])
        prices = tickers.history(start=self.start, end=self.end, interval="1d")['Close'].iloc[0]
        self.bench['Price'] = prices
        self.bench['Shares'] = np.floor(np.divide([self.equity, self.equity], prices))

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

                # Update the number of shares held for asset
                self.portfolio.loc[asset, 'Shares'] += shares

                # Recalculate portfolio weights
                self.portfolio.Weights = self.portfolio.Shares / sum(self.portfolio.Shares)
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

    def run(self):
        # Get price data for assets
        tickers = yf.Tickers(self.assets + self.bench.index.tolist())
        print(self.assets)
        closing_price = tickers.history(start=self.start, end=self.end, interval="1d")['Close']
        dividends = tickers.history(start=self.start, end=self.end, interval="1d")['Dividends']

        # Generate buy/sell signals
        signals = self.strategy.generate_signals()

        # Initializes dataframe for daily portfolio tracking
        daily_records = pd.DataFrame(0.0, index=signals.index,
                                     columns=['Securities', 'Cash', 'RPnL', 'UPnL', 'Equity', 'Fixed'])
        for index, day in signals.iterrows():
            for asset in self.assets:
                if signals.loc[index, asset] == 1:
                    print(datetime.datetime.strftime(index, '%Y-%m-%d'), "BUY", asset, "@ price $",
                          round(closing_price.loc[index, asset], 3))
                    self.transact(1, asset=asset, price=closing_price.loc[index, asset],
                                  shares=np.floor(0.2 * self.portfolio.loc[asset, 'Shares']))
                elif signals.loc[index, asset] == -1:
                    print(datetime.datetime.strftime(index, '%Y-%m-%d'), "SELL", asset, "@ price: $",
                          round(closing_price.loc[index, asset], 3))
                    self.transact(-1, asset=asset, price=closing_price.loc[index, asset],
                                  shares=np.floor(0.2 * self.portfolio.loc[asset, 'Shares']))
            # Print Dividend Transactions
            div = sum(dividends.loc[index, ~(dividends.columns.isin(['BND', 'SPY']))] * self.portfolio.Shares)
            if div > 0:
                self.cash += div
                print(datetime.datetime.strftime(index, '%Y-%m-%d'), f"${round(div, 3)} IN DIVDENDS POSTED TO CASH")
            # Records assets closing price for portfolio valuation
            self.portfolio.Price = closing_price.loc[index, ~(closing_price.columns.isin(['BND', 'SPY']))]
            # Records benchmark assets closing price for portfolio valuation
            self.bench.Price = closing_price.loc[index, ['BND', 'SPY']]
            # Daily records
            daily_records.loc[index] = [np.matmul(self.portfolio.Price, self.portfolio.Shares),
                                        self.cash,
                                        self.pnl,
                                        (np.matmul(self.portfolio.Price,
                                                   self.portfolio.Shares) + self.cash) - self.equity,
                                        self.bench.loc['SPY', 'Price'] * self.bench.loc['SPY', 'Shares'],
                                        self.bench.loc['BND', 'Price'] * self.bench.loc['BND', 'Shares']]

        return daily_records

    def generate_report(self, records, bench):
        # Calculating daily portfolio value
        values = pd.DataFrame(np.sum(records.loc[:, ['Securities', 'Cash']], axis=1),
                              index=records.index,
                              columns=['Value'])

        # Calculates log returns and ending value change
        returns = np.log(values.Value / values.Value.shift(1))[1:]
        changes = pd.DataFrame(np.diff(values.Value)[1:],
                               index=records.index[2:])

        # Minimum and Maximum Returns
        max_ret, min_ret = max(changes[0]), min(changes[0])

        # Calculates the start/end diff in terms of years as a float
        delta = np.subtract(datetime.datetime.strptime(self.end, "%Y-%m-%d"),
                            datetime.datetime.strptime(self.start, "%Y-%m-%d")).days / 365.25

        # Portfolio Annualized Return
        exp_ret = np.divide(sum(records.loc[records.index[-1], ['Securities', 'Cash']]),
                            sum(records.loc[records.index[0], ['Securities', 'Cash']])) ** (1 / delta) - 1
        # Portfolio Volatility
        vol = np.std(returns) * np.sqrt(252) * 100

        # Prints worst trading day
        print("MAX DRAWDOWN:", changes.index[changes[0] == min_ret].date.item().strftime('%Y-%m-%d'),
              round(min_ret, 3))
        # Prints best trading day
        print("GOLDEN TICKET:", changes.index[changes[0] == max_ret].date.item().strftime('%Y-%m-%d'),
              round(max_ret, 3))
        print("PORTFOLIO RETURN:", round(100 * exp_ret, 3))
        print("PORTFOLIO VOLATILITY:", round(vol, 3))

        print("SHARPE RATIO:", round((100 * exp_ret - 2.25) / vol, 3))

        plt.plot(values)
        plt.plot(records.loc[:, bench])
        plt.title("Portfolio vs Index")
        plt.legend(['Portfolio', 'Equity Index'])
        plt.show()

    def update_portfolio(self, portfolio: pd.DataFrame, cash: float):
        # Get price data for assets and updates internal
        # object attributes
        self.assets = list(portfolio.index)
        self.equity = self.cash = cash

        # Redownloads tickers and pricing history
        tickers = yf.Tickers(self.assets)
        prices = tickers.history(start=self.start, end=self.end, interval="1d")['Close'].iloc[0]

        self.portfolio = pd.DataFrame()
        # Adds purchase and weights price to dataframe
        self.portfolio['Price'] = prices
        self.portfolio['Weights'] = portfolio.Weights

        # Calculate the number of shares
        self.portfolio['Shares'] = np.floor(np.divide(self.portfolio.Weights * self.cash, prices))

        # Calculates cost of portfolio and updates the cash holdings
        cost = np.matmul(self.portfolio.Price, self.portfolio.Shares)
        self.cash -= cost

        # Recalculate the weights
        self.portfolio['Weights'] = self.portfolio.Shares / sum(self.portfolio.Shares)

        # Update the trading strategy
        self.strategy.updateAssets(portfolio.index.tolist())

    def get_portfolio(self):
        # Returns the current portfolio in-use by the backtesting model
        return self.portfolio
