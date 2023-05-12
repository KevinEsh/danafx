# from utils.config import get_settings
# from trade.broker import BrokerSession

# login_settings = get_settings("settings/demo/login.json")
# trading_settings = get_settings("settings/demo/trading.json")


# # Login on a broker session
# broker = BrokerSession()
# broker.start_session(login_settings["mt5_login"])
# broker.enable_symbols([symbol])
from dash import Dash, dcc, html, Input, Output
from pandas import read_csv
from yfinance import download
from datetime import datetime as dt
import pytz
from numpy import gradient

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from trade.indicators import RSI, EMA, SMA, get_stable_min_bars, set_unstable_period

symbols = ["EURUSD"]

# tz = pytz.timezone("US/Central")
# start = tz.localize(dt(2023, 1, 1))
# end = tz.localize(dt.today())
# df = broker.get_candles(symbol, "M1", 100, as_dataframe=True, format_time=True)
# df = download("EURUSD=X", start, end, interval="1h", auto_adjust=True)
# df.rename(columns={C:C.lower() for C in df.columns}, inplace=True)
# df.to_csv("data/raw/eurusd_1000.csv")

df = read_csv("data/raw/eurusd_2000.csv", index_col="time")

rsi = RSI(df.close, 14)
bars = get_stable_min_bars("RSI", 14)
# set_unstable_period("RSI", bars - 10 + 1)
rsi2 = gradient(SMA(RSI(df.close, 14), 5), 2) * 10

x = df.index[50:60]
y = df.close[50:60]

x2 = df.index[60:70]
y2 = df.close[60:70]

fig = make_subplots(rows=2, cols=1)
# df.to_csv("eurusd.csv")

# fig_ohlc.update_yaxes()

# fig.add_trace(go.Ohlc(x=df.index,
#                       open=df.open,
#                       high=df.high,
#                       low=df.low,
#                       close=df.close,
#                       name="price",
#                       ), row=1, col=1)

# fig.update_layout(xaxis_rangeslider_visible=False, legend=dict(
#     groupclick="toggleitem", orientation="h", xanchor="auto", yanchor="auto", y=-0.12))
# fig.update_xaxes(title_text='Date')
# fig.update_yaxes(ticklabelposition="outside right", side="right")
# fig.update_yaxes(tickprefix='$', row=1, col=1)
# fig.update_yaxes(range=(0, 100), fixedrange=True, row=2, col=1)
# fig.update_xaxes(showline=True, linewidth=2, linecolor='black')

fig_indic = go.Figure()
fig_indic.add_trace(
    go.Scatter(
        x=df.index,
        y=rsi,
        mode="lines",
        name="RSI(14)",
        legendgroup="indicators"
    )
)

fig_indic.add_trace(
    go.Scatter(
        x=df.index,
        y=rsi2,
        mode="lines",
        name="RSI2(14)",
        legendgroup="indicators",
    )
)

fig_indic.update_yaxes(
    side="right",
    ticklabelposition="outside right",
    # fixedrange=True,
    range=(0, 100),
)
fig_indic.update_layout(
    # xaxis_rangeslider_visible=False,
    legend=dict(
        groupclick="toggleitem",
        orientation="h",
        # xanchor="left",
        # yanchor="top",
        y=1.2,
        x=0,
    )
)

app = Dash(__name__)

app.layout = html.Div([
    html.Div([
        dcc.Dropdown(
            options=symbols,
            value=symbols[0],
            id='symbol-selector-dropdown'
        )],
        style={'width': '15%', 'display': 'inline-block'}
    ),
    dcc.Graph(id='candlestick-graph'),
    dcc.Slider(
        0,
        100,
        step=10,
        value=100,
        marks={str(pct): str(pct) for pct in range(0, 110, 10)},
        id='year-slider'
    ),
    dcc.Graph(id='indicators-graph'),
])


@app.callback(
    Output('candlestick-graph', 'figure'),
    Output('indicators-graph', 'figure'),
    Input('symbol-selector-dropdown', 'value'),
    # Output('indicators-graph', 'figure')
)
def update_symbol(symbol):
    # filtered_df = df[df.year == symbol]

    # fig = px.scatter(filtered_df, x="gdpPercap", y="lifeExp",
    #                  size="pop", color="continent", hover_name="country",
    #                  log_x=True, size_max=55)

    return fig_ohlc, fig_indic


if __name__ == '__main__':
    app.run_server(debug=True)

    fig_ohlc = go.Figure(
        data=go.Ohlc(
            x=df.index,
            open=df.open,
            high=df.high,
            low=df.low,
            close=df.close,
            name="price"
            )
        )

def add_regime_line(fig, time, indicator, mask, name:str):
    
    fig.add_trace(
        go.Scatter(
            x=time,
            y=indicator,
            mode="lines",
            name=name,
            legendgroup="regimeline",
            marker=dict(
                color=mask
            )
        )
    )
    fig_ohlc.add_trace(
        go.Scatter(
            x=x2,
            y=y2,
            name="sell",
            legendgroup="signals",
            mode='markers',
            opacity=0.8,
            marker=dict(
                size=12,
                symbol="arrow",
                angle=135,
                color="Red",
                # line=dict(
                #     width=2,
                #     color="Red"
                # )
            ),
        ),
        # row=1,
        # col=1,
    )
    fig_ohlc.update_layout(
        xaxis_rangeslider_visible=False,
        legend=dict(
            groupclick="toggleitem",
            orientation="h",
            # xanchor="left",
            # yanchor="top",
            y=1.2,
            x=0,
        )
    )
    fig_ohlc.update_yaxes(
        ticklabelposition="outside right",
        tickprefix='$',
        side="right"
    )
    return