from utils.config import get_settings
from trade.broker import BrokerSession
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig = make_subplots(rows=2, cols=1)

login_settings = get_settings("settings/demo/login.json")
# trading_settings = get_settings("settings/demo/trading.json")

symbol = "EURUSD"

# Login on a broker session
broker = BrokerSession()
broker.start_session(login_settings["mt5_login"])
broker.enable_symbols([symbol])

df = broker.get_candles(symbol, "M1", 100, as_dataframe=True, format_time=True)
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
                      close=df.close), row=1, col=1)

fig.update_layout(xaxis_rangeslider_visible=False, title=symbol)
# fig.update_xaxes(title_text='Date')
fig.update_yaxes(ticklabelposition="outside right", side="right")
fig.update_yaxes(title_text='price', tickprefix='$', row=1, col=1)
fig.update_yaxes(title_text='RSI(14)', row=2, col=1)
fig.update_xaxes(showline=True, linewidth=2, linecolor='black')
fig.add_trace(go.Scatter(x=df.index, y=df.close, mode="lines"), row=2, col=1)

x = df.index[50:60]
y = df.close[50:60]

x2 = df.index[60:70]
y2 = df.close[60:70]

fig.add_trace(
    go.Scatter(
        mode='markers',
        x=x,
        y=y,
        opacity=0.8,
        marker=dict(
            size=12, symbol="arrow", angle=45, color="Green", line=dict(width=2, color="Green")
        ),
        name="buy signals"
    ),
    row=1,
    col=1,
)

fig.add_trace(
    go.Scatter(
        mode='markers',
        x=x2,
        y=y2,
        opacity=0.8,
        marker=dict(
            size=12, symbol="arrow", angle=135, color="Red", line=dict(width=2, color="Red")
        ),
        name="sell signals"
    ),
    row=1,
    col=1,
)

fig.show()
