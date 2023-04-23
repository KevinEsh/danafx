from numpy import recarray, ndarray
from typing import Union
from pandas import Series

CandleLike = Union[Series, recarray, ndarray]

__unstable_indicators__ = [
    'HT_DCPERIOD',
    'HT_DCPHASE',
    'HT_PHASOR',
    'HT_SINE',
    'HT_TRENDMODE',
    'ADX',
    'ADXR',
    'CMO',
    'DX',
    'MFI',
    'MINUS_DI',
    'MINUS_DM',
    'PLUS_DI',
    'PLUS_DM',
    'RSI',
    'STOCHRSI',
    'EMA',
    'HT_TRENDLINE',
    'KAMA',
    'MAMA',
    'T3',
    'ATR',
    'NATR',
    "WT",
    "RQK",
    "RBFK",
]

__linear_indicators__ = [
    'MAX',
    'MIN',
    'MINMAX',
    'BBANDS',
    'DEMA',
    'EMA',
    'HT_TRENDLINE',
    'KAMA',
    'MA',
    'MAMA',
    'MAVP',
    'MIDPOINT',
    'MIDPRICE',
    'SAR',
    'SAREXT',
    'SMA',
    'T3',
    'TEMA',
    'TRIMA',
    'WMA',
    'AVGPRICE',
    'MEDPRICE',
    'TYPPRICE',
    'WCLPRICE',
    'LINEARREG',
    'LINEARREG_INTERCEPT',
    'TSF',
    "HL2",
    "HLC3",
    "OHLC4",
]

__new_indicators__ = [
    "HL2",
    "HLC3",
    "OHLC4",
    "WT",
    "RQK",
    "RBFK"
]
