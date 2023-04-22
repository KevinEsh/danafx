# from utils.config import get_settings
# from trade.broker import BrokerSession

# login_settings = get_settings("settings/demo/login.json")
# trading_settings = get_settings("settings/demo/trading.json")


# # Login on a broker session
# broker = BrokerSession()
# broker.start_session(login_settings["mt5_login"])
# broker.enable_symbols([symbol])
from pandas import read_csv
import plotly.graph_objects as go
from plotly.subplots import make_subplots

symbol = "EURUSD"
# df = broker.get_candles(symbol, "M1", 100, as_dataframe=True, format_time=True)
df = read_csv("data/raw/eurusd.csv", index_col="time")
fig = make_subplots(rows=2, cols=1)
# df.to_csv("eurusd.csv")

# fig = go.Figure(data=go.Ohlc(x=df.index,
#                              open=df.open,
#                              high=df.high,
#                              low=df.low,
#                              close=df.close))

fig.add_trace(go.Ohlc(x=df.index,
                      open=df.open,
                      high=df.high,
                      low=df.low,
                      close=df.close,
                       name="price",
                      ), row=1, col=1)

fig.update_layout(xaxis_rangeslider_visible=False, title=symbol, legend=dict(orientation="h", xanchor="auto", yanchor="auto", y=-0.12))
# fig.update_xaxes(title_text='Date')
fig.update_yaxes(ticklabelposition="outside right", side="right")
fig.update_yaxes(tickprefix='$', row=1, col=1)
fig.update_yaxes(range=(0, 1), fixedrange=True, row=2, col=1)
fig.update_xaxes(showline=True, linewidth=2, linecolor='black')


fig.add_trace(go.Scatter(x=df.index, y=df.close-1, mode="lines", name="RSI(14)"), row=2, col=1)

x = df.index[50:60]
y = df.close[50:60]

x2 = df.index[60:70]
y2 = df.close[60:70]

fig.add_trace(
    go.Scatter(
        x=x,
        y=y,
        name="buy signal",
        mode='markers',
        opacity=0.8,
        marker=dict(
            size=12, 
            symbol="arrow", 
            angle=45, 
            color="Green", 
            # line=dict(
            #     width=2, 
            #     color="Green"
            #     )
        ),
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Scatter(
        x=x2,
        y=y2,
        name="sell signal",
        mode='markers',
        opacity=0.8,
        marker=dict(
            size=12, symbol="arrow", angle=135, color="Red", line=dict(width=2, color="Red")
        ),
    ),
    row=1,
    col=1,
)

fig.show()
