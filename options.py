from multipledispatch import dispatch
from ally_setup import michel_acct as acct
from datetime import date
from orders import option_strike, option_callput, option_symbol

@dispatch(str, int, int, str, int)
def getOptionsData(symbol: str, strike_min: int, strike_max: int, option: str, month: int):
    upp, low, mon = ('strikeprice-lte:' + str(strike_max)), \
                    ('strikeprice-gte:' + str(strike_min)), ('xmonth-eq:' + str(month))
    op_type = 'put_call-eq:' + option.lower()

    chain = acct.search(symbol, query=[mon, op_type, upp, low])[
        ['strikeprice', 'last', 'ask', 'imp_Volatility', 'xmonth', 'xday']]
    chain = chain[chain['last'] > 0]
    chain = chain.reset_index()

    if month == date.today().month:
        return (chain[chain['xday'] >= date.today().day]).sort_values('strikeprice').reset_index(drop=True)
    else:
        return chain.sort_values('strikeprice').reset_index(drop=True)

@dispatch(str, int, int, str, int, int)
def getOptionsData(symbol: str, strike_min: int, strike_max: int, option: str, month: int, day: int):
    chain = getOptionsData(symbol, strike_min, strike_max, option, month)
    return chain[chain['xday'] == day].sort_values('strikeprice').reset_index(drop=True)


def moneyness(syms: str) -> str:
    direction = option_callput(syms)
    strike = option_strike(syms)
    syms = option_symbol(syms)
    if direction.lower() == 'call':
        diff: float = float(acct.quote(syms, ['last'])['last']) - strike
        if diff < -0.5:
            return "Out-the-money"
        elif -0.5 <= diff <= 0.5:
            return "At-the-money"
        elif diff > 0.5:
            return "In-the-money"
    elif direction.lower() == 'put':
        diff: float = strike - float(acct.quote(syms, ['last'])['last'])
        if diff < -0.5:
            return "Out-the-money"
        elif -0.5 <= diff <= 0.5:
            return "At-the-money"
        elif diff > 0.5:
            return "In-the-money"
