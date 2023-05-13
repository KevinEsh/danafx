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
from plotly.express import scatter_3d
from plotly.subplots import make_subplots
from datatools.transform import normalize
from trade.indicators import RSI, EMA, SMA, ADX, CCI, WT, HLC3, get_stable_min_bars, set_unstable_period

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
adx = ADX(df.high, df.low, df.close, 20)
cci = CCI(df.high, df.low, df.close, 20)
wt = WT(df.high, df.low, df.close, 10)

hlc3 = HLC3(df.high, df.low, df.close)
ema = EMA(df.close[::-1], 4)[::-1]
sma = SMA(df.close[::-1], 4)[::-1]
sss = hlc3.shift(-4) - hlc3

df["rsi"] = normalize(rsi, (0, 100), "range_scale")
df["adx"] = normalize(adx)
df["cci"] = normalize(cci)
df["wt"] = normalize(wt)
df["sma"] = normalize(sma - df.close, (-1, 1))
df["ema"] = normalize(ema - df.close, (-1, 1))
df["sss"] = normalize(sss - df.close, (-1, 1))

df.dropna()
# df.to_csv("eurusd.csv")

fig_3d = go.Figure(
    data=[
        go.Scatter3d(
            x=df.rsi,
            y=df.adx,
            z=df.wt,
            mode='markers',
            marker=dict(
                size=3,
                color=df.sss,                # set color to an array/list of desired values
                # 'rdylgn',   # choose a colorscale
                # [(0, "red"), (0.5, "rgb(153, 153, 153)"), (1, "green")],  # "oxy",
                colorscale=[
                    (0, "red"),
                    # (0.4, "rgb(153, 153, 153)"),
                    (0.5, "rgb(153, 153, 153)"),
                    # (0.6, "rgb(153, 153, 153)"),
                    (1, "green")],
                opacity=0.6
            ),

        ),
    ]
)

fig_3d.update_scenes(
    xaxis=dict(
        range=(0, 1)
    ),
    yaxis=dict(
        range=(0, 1)
    ),
    zaxis=dict(
        range=(0, 1)
    )
)
fig_3d.update_layout(
    margin=dict(l=0, r=0, b=0, t=0),
    width=850, height=850, title='Lorentzian Space',
    scene=dict(
        xaxis=dict(
            title='RSI(14)',
            # titlefont_color='white'
        ),
        yaxis=dict(
            title='ADX(20)',
            # titlefont_color='white'
        ),
        zaxis=dict(
            title='WT(10)',
            # titlefont_color='white'
        ),
        # bgcolor='rgb(20, 24, 54)'
    ))
# fig_ohlc = go.Figure(
#     data=go.Ohlc(
#         x=df.index,
#         open=df.open,
#         high=df.high,
#         low=df.low,
#         close=df.close,
#         name="price"
#     )
# )
# fig_ohlc.add_trace(
#     go.Scatter(
#         x=x,
#         y=y,
#         name="buy",
#         legendgroup="signals",
#         mode='markers',
#         opacity=0.8,
#         marker=dict(
#             size=12,
#             symbol="arrow",
#             angle=45,
#             color="Green",
#             # line=dict(
#             #     width=2,
#             #     color="Green"
#             #     )
#         ),
#     ),
#     # row=1,
#     # col=1,
# )
# fig_ohlc.add_trace(
#     go.Scatter(
#         x=x2,
#         y=y2,
#         name="sell",
#         legendgroup="signals",
#         mode='markers',
#         opacity=0.8,
#         marker=dict(
#             size=12,
#             symbol="arrow",
#             angle=135,
#             color="Red",
#             # line=dict(
#             #     width=2,
#             #     color="Red"
#             # )
#         ),
#     ),
#     # row=1,
#     # col=1,
# )
# fig_ohlc.update_layout(
#     xaxis_rangeslider_visible=False,
#     legend=dict(
#         groupclick="toggleitem",
#         orientation="h",
#         # xanchor="left",
#         # yanchor="top",
#         y=1.2,
#         x=0,
#     )
# )
# fig_ohlc.update_yaxes(
#     ticklabelposition="outside right",
#     tickprefix='$',
#     side="right"
# )
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

# fig_indic = go.Figure()
# fig_indic.add_trace(
#     go.Scatter(
#         x=df.index,
#         y=rsi,
#         mode="lines",
#         name="RSI(14)",
#         legendgroup="indicators"
#     )
# )

# fig_indic.add_trace(
#     go.Scatter(
#         x=df.index,
#         y=rsi2,
#         mode="lines",
#         name="RSI2(14)",
#         legendgroup="indicators",
#     )
# )

# fig_indic.update_yaxes(
#     side="right",
#     ticklabelposition="outside right",
#     # fixedrange=True,
#     range=(0, 100),
# )
# fig_indic.update_layout(
#     # xaxis_rangeslider_visible=False,
#     legend=dict(
#         groupclick="toggleitem",
#         orientation="h",
#         # xanchor="left",
#         # yanchor="top",
#         y=1.2,
#         x=0,
#     )
# )

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
    # dcc.Slider(
    #     0,
    #     100,
    #     step=10,
    #     value=100,
    #     marks={str(pct): str(pct) for pct in range(0, 110, 10)},
    #     id='year-slider'
    # ),
    # dcc.Graph(id='indicators-graph'),
])


@app.callback(
    Output('candlestick-graph', 'figure'),
    # Output('indicators-graph', 'figure'),
    Input('symbol-selector-dropdown', 'value'),
    # Output('indicators-graph', 'figure')
)
def update_symbol(symbol):
    # filtered_df = df[df.year == symbol]

    # fig = px.scatter(filtered_df, x="gdpPercap", y="lifeExp",
    #                  size="pop", color="continent", hover_name="country",
    #                  log_x=True, size_max=55)

    return fig_3d


if __name__ == '__main__':
    app.run_server(debug=True)
