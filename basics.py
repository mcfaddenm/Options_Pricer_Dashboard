from ally_setup import michel_acct as a
import matplotlib.pyplot as plt
import datetime as d
from options import *
from risk import *

def symbols(industry: str):
    if industry.lower() == 'tech':
        return ['AAPL', 'GOOG', 'AMZN', 'MSFT', 'V', 'TSLA', 'NVDA', 'AMD', 'GRMN']
    elif industry.lower() == 'etfs':
        return ['QQQ', 'XLF', 'XLP', 'VIX', 'SPY', 'VOO', 'GLD', 'SPBO', 'SUSC', 'VBK']
    elif industry.lower() == 'def':
        return list(a.watchlists['DEFAULT'])
    elif industry.lower() == 'holdings':
        return list(a.watchlists['HOLDINGS'])

# Returns account transaction history
def history():
    his = a.history()
    return his[['activity', 'date', 'amount', 'symbol']]


# Returns the latest prices for the symbols on the default watchlist
@dispatch()
def getWLquotes():
    syms = symbols('def')
    x = a.quote(syms, ['last']).transpose()
    x.sort_index(axis=1, inplace=True)
    return x


# Returns the latest prices for the symbols on a specific watchlist
@dispatch(str)
def getWLquotes(wL: str):
    syms = symbols(wL)
    x = a.quote(syms, ['last']).transpose()
    x.sort_index(axis=1, inplace=True)
    return x


@dispatch(str)
def stream(sym: str):
    for q in a.stream(sym):
        qu = [q['symbol'], q['bid'], q['ask']]
        # action(qu)
        print(qu)


@dispatch(list)
def stream(syms: list):
    for q in a.stream(syms):
        qu = [q['symbol'], q['bid'], q['ask']]
        # action(qu)
        print(qu)


# Retrieves cash available for investment
def updateBal():
    return float(a.balances()[['money.cashavailable']].to_numpy())


def holdings():
    hold = a.holdings()[['sym', 'costbasis', 'marketvalue', 'gainloss', 'qty']]
    return hold


def gainloss():
    values = holdings()[['gainloss']].values
    total = 0
    for x in values:
        total += float(x)
    return total


def quote(sym: str):
    df = pd.DataFrame(columns=['last'])
    df.loc[sym] = float(a.quote(sym, ['last'])['last'])
    return df


def optionsPlot(options_data: type(pd.DataFrame())):
    options_data = options_data.reset_index()
    title = options_data['symbol'][0][:-15] + " Options Chain"

    plt.plot(options_data[['strikeprice']], options_data[['imp_Volatility']])
    plt.title(title)
    plt.show()


def action(x: list):
    price = x[1]
    if price < 51.60:
        print('STOP LOSS')
    elif price > 52.20:
        print('TAKE PROFIT')



stock_dict = {'volatility12': 'volatility',
              'adp_50': '50-Day MA',
              'adp_100': '100-Day MA',
              'adp_200': '200-Day MA',
              'beta': 'beta',
              'div':'div'
              }

@dispatch(str, str)
def getStockData(symbol: str, index: str):
    vol = pd.DataFrame(columns=[stock_dict[index]])
    vol.loc[symbol] = float(a.quote(symbol, index)[index])
    return vol


@dispatch(list, str)
def getStockData(symbols: list, index: str):
    vols = pd.DataFrame(columns=[stock_dict[index]])
    for x in symbols:
        vols.loc[x] = float(a.quote(x, index)[index])
    return vols


@dispatch(str)
def getVol(symbol: str):
    x = getStockData(symbol, 'volatility12')
    return x


@dispatch(list)
def getVol(symbols: list):
    x = getStockData(symbols, 'volatility12')
    return x


@dispatch(str)
def getMA(symbol: str):
    today = d.today()
    start = pd.DataFrame(index=[symbol])
    dates = [5, 10, 20]
    for x in dates:
        test = a.timesales(symbol, today - d.timedelta(days=x), today)['last']
        avg, index = [sum(test) / len(test)], str(x) + '-Day MA'
        temp = pd.DataFrame(avg, columns=[index], index=[symbol])
        start = start.join(temp)
    x = start.join(getStockData(symbol, 'adp_50'))
    y = x.join(getStockData(symbol, 'adp_100'))
    z = y.join(getStockData(symbol, 'adp_200'))
    return z

@dispatch(list)
def getMA(symbols: list):
    result = pd.DataFrame()
    for x in symbols:
        df = getMA(x)
        result = pd.concat([result, df], axis=0)
    result.sort_index(inplace=True)
    return result


@dispatch(str)
def getBeta(symbol: str):
    x = getStockData(symbol, 'beta')
    return x


@dispatch(list)
def getBeta(symbols: list):
    x = getStockData(symbols, 'beta')
    return x

def getDiv(symbol: str):
    div = getStockData(symbol, 'div')
    return div
