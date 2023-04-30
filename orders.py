import datetime
import requests
import xmltodict
from requests_oauthlib import OAuth1

auth = OAuth1('uke2pVaOE6zcWy7c9EqoVuCEIbVsgX2Olxc2gvB9d087', 'ys04yTX7yvjDHoaeup55hfAlfKqr9o5IoXrUq05wulg3',
              'tsKhET3lnBkVgTZd7KzFwQCOuu1SBXx6MdTROQZzblI0', 'gyAEh1VcJT4DwFm62qhKfhXpcKD447j78K21WVzCsVg4')


def option_strike(name):
    """Pull apart an OCC standardized option name and
    retreive the strike price, in integer form"""
    return int(name[-8:]) / 1000.0


def option_maturity(name):
    """Given OCC standardized option name,
    return the date of maturity"""
    return datetime.datetime.strptime(name[-15:-9], "%y%m%d").strftime("%Y-%m-%d")


def option_callput(name):
    """Given OCC standardized option name,
    return whether its a call or a put"""
    return "call" if name.upper()[-9] == "C" else "put"


def option_symbol(name):
    """Given OCC standardized option name, return option ticker"""
    return name[:-15]


# Stock orders at market
def stock_order(sym, side, tif, qty):
    '''
    Creates a live buy, sell, or short-sell order. Returns OrderID
    FIXML KEY
    Typ:  Market: "1"
          Limit: "2"
          Stop: "3"
          Stop Limit: "4"

    Side: Buy: "1"
          Sell: "2"
          Sell Short: "5" ‐

    tif:  Day Order: "0"
          GTC Order: "1"
          Market on Close: "7"
        '''

    url = f"https://devapi.invest.ally.com/v1/accounts/3LB77972/orders.xml"
    xmlns = 'xmlns="http://www.fixprotocol.org/FIXML-5-0-SP2"'
    order = f'TmInForce="{tif}" Typ="1" "Side="{side}" Acct="3LB77972"'
    instrmt = f'SecTyp="CS" Sym="{sym}"'
    orderQty = f'Qty="{qty}"'

    payload = f"<FIXML {xmlns}>\r\n <Order {order}>\r\n <Instrmt {instrmt}/>\r\n <OrdQty {orderQty}/>\r\n  </Order> \r\n </FIXML>"

    headers = {
        'TKI_OVERRIDE': 'true',
        'Content-Type': 'application/xml',
    }
    response = requests.post(url, auth=auth, headers=headers, data=payload)

    f = xmltodict.parse(response.text.encode('utf8'))['response']['clientorderid']
    # orderids.append(f)

    return f


# Ordering options at market
def options_order(contract, side, qty):
    sym = option_symbol(contract)
    k = option_strike(contract)
    date = option_maturity(contract) + "T00:00:00.000-05:00"

    assert (side == 1 or 2)
    if side == 1:
        pos = 'O'
    else:
        pos = 'C'

    if option_callput(contract) == 'call':
        op_type = 'OC'
    else:
        op_type = 'OP'

    url = f"https://devapi.invest.ally.com/v1/accounts/3LB77972/orders.xml"
    xmlns = 'xmlns="http://www.fixprotocol.org/FIXML-5-0-SP2"'
    order = f'TmInForce="0" Typ="1" Side="{side}" PosEfct="{pos}" Acct="3LB77972"'
    instrmt = f'CFI="{op_type}" SecTyp="OPT" Sym="{sym}" MatDt="{date}" StrkPx="{k}"'
    orderQty = f'Qty="{qty}"'

    payload = f"<FIXML {xmlns}>\r\n <Order {order}>\r\n <Instrmt {instrmt}/>\r\n <OrdQty {orderQty}/>\r\n  </Order> \r\n </FIXML>"

    headers = {
        'TKI_OVERRIDE': 'true',
        'Content-Type': 'application/xml',
    }
    response = requests.post(url, auth=auth, headers=headers, data=payload)

    f = xmltodict.parse(response.text.encode('utf8'))['response']['clientorderid']
    # orderids.append(f)

    return f


## Canceling stock orders
def can_stock_order(sym, typ, side, tif, acct, qty, orderids):
    '''
    FIXML KEY
    Typ:  Market: "1"
          Limit: "2"
          Stop: "3"
          Stop Limit: "4"

    Side: Buy: "1"
          Sell: "2"
          Sell Short: "5" ‐

    tif:  Day Order: "0"
          GTC Order: "1"
          Market on Close: "7"
    '''

    url = f"https://devapi.invest.ally.com/v1/accounts/{acct}/orders.xml"

    xmlns = 'xmlns="http://www.fixprotocol.org/FIXML-5-0-SP2"'
    order = f'TmInForce="{tif}" Typ="{typ}" Side="{side}" OrigID="{orderids}" Acct="{acct}"'
    instrmt = f'SecTyp="CS" Sym="{sym}"'
    orderQty = f'Qty="{qty}"'

    payload = f"<FIXML {xmlns}>\r\n <OrdCxlReq {order}>\r\n <Instrmt {instrmt}/>\r\n <OrdQty {orderQty}/>\r\n  </OrdCxlReq> \r\n </FIXML>"

    headers = {
        'TKI_OVERRIDE': 'true',
        'Content-Type': 'application/xml',
    }

    response = requests.post(url, auth=auth, headers=headers, data=payload)
    f = xmltodict.parse(response.text.encode('utf8'))['response']
    # c_orders.append(f)

    return f
