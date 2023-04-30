# This is going to be the risk framework file
# First I need to establish my risk appetite as an investor
import numpy as np
import pandas as pd
import scipy
import basics as bs

def options_probability(asset_ticker, strike, T):
    # This is 99.999% likely to be an option
    options_type = None
    if len(asset_ticker) > 15:
        options_type = asset_ticker[-9:-8]
        asset_ticker = asset_ticker[:-15]
    else:
        asset_ticker = asset_ticker

    vol = float(bs.getVol(asset_ticker)['volatility'])
    spot = float(bs.quote(asset_ticker)['last'])
    div = float(bs.getDiv(asset_ticker)['div'])
    rate = 4.08 * 1e-2

    d1 = (np.log(spot/strike) + (rate - div + 0.5*vol**2) * T) / (vol * np.sqrt(T))
    d2 = d1 - vol * np.sqrt(T)

    if options_type == 'C':
        prob = float(scipy.stats.norm.cdf(d2))
    else:
        prob = float(scipy.stats.norm.cdf(-d2))

    return prob

def quadratic_utility(w):
    a, b = 0.001, 0.0001
    return a * w + b * w**2

