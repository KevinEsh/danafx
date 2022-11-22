import yfinance as yf
from ta.momentum import RSIIndicator

ticker_list = ["EURUSD=X"]

data_start = "2022-11-11"
data_end = "2022-11-18"  # datatime.

df_price = yf.download(
    ticker_list,
    start=data_start,
    end=data_end,
    interval="1m",
    group_by="ticker",
    ignore_tz=False,
    auto_adjust=True,
)

df_price["RSI"] = RSIIndicator(df_price["Close"], window=14).rsi()

# print(df_price)
