import numpy as np
import plotly.graph_objects as go
import pandas as pd

from trade.metadata import CandleLike
from datatools.technical import above, below, onband


def make_figure():
    return go.Figure()


def add_ohcl_chart(fig, candles: CandleLike):
    fig.add_ohlc(
        x=candles.time,
        open=candles.open,
        high=candles.high,
        low=candles.low,
        close=candles.close,
        name="ohlc",
        legendgroup="candle",
        legendgrouptitle_text="candle",
    )

    fig.update_yaxes(
        side="right",
        tickprefix="$",
        ticklabelposition="outside right",
    )

    fig.update_layout(
        xaxis_rangeslider_visible=False,
        legend=dict(
            groupclick="toggleitem",
            orientation="h",
            # xanchor="left",
            # yanchor="top",
            y=1.25,
            x=0,
        )
    )


def add_trending_line(
    fig: go.Figure,
    candles: CandleLike,
    source1: str,
    source2: str,
    band: tuple[float, float] = (0, 0),
    legendgroup: str = "regime",
):
    # Full line
    series1 = candles[source1]
    series2 = candles[source2]

    bulls = np.where(above(series2, series1, band[1]), series1, np.nan)
    fig.add_scattergl(
        x=candles.time,
        y=bulls,
        name="bullish",
        mode="markers+lines",
        line={'color': 'green', 'width': 1},
        marker={"color": "green", "size": 3},
        legendgroup=legendgroup,
        legendgrouptitle_text=legendgroup,
    )

    neutrals = np.where(onband(series2, series1, band), series1, np.nan)
    fig.add_scattergl(
        x=candles.time,
        y=neutrals,
        name="neutral",
        mode="markers+lines",
        line={'color': 'grey', 'width': 1},
        marker={"color": "grey", "size": 3},
        legendgroup=legendgroup,
    )

    # Above threshold
    bears = np.where(below(series2, series1, band[0]), series1, np.nan)
    fig.add_scattergl(
        x=candles.time,
        y=bears,
        name="bearish",
        mode="markers+lines",
        line={'color': 'red', 'width': 1},
        marker={"color": "red", "size": 3},
        legendgroup=legendgroup,
    )

    #fig.add_scatter(x=candles.time, y=series2)


def add_lines(
    fig: go.Figure,
    candles: CandleLike,
    sources: tuple[str],
    legendgroup: str = "indicator",
    ylim: tuple[float] = (0, 1)
):
    for source in sources:
        series = candles[source]

        fig.add_scattergl(
            x=candles.time,
            y=series,
            name=source,
            mode="lines",
            line={'width': 1},
            legendgroup=legendgroup,
            legendgrouptitle_text=legendgroup,
        )

    fig.update_yaxes(
        side="right",
        ticklabelposition="outside right",
        # fixedrange=True,
        range=ylim,
    )

    fig.update_layout(
        # xaxis_rangeslider_visible=False,
        legend=dict(
            groupclick="toggleitem",
            orientation="h",
            # xanchor="left",
            # yanchor="top",
            y=1.25,
            x=0,
        )
    )


def add_session(fig, candles, session_hours: tuple[int, int] = (22, 10)):
    # Create a list to hold our shapes
    shapes = []

    # Define the hours of the trading sessions
    # london_session_start = 8
    # london_session_end = 17

    # new_york_session_start = 14
    # new_york_session_end = 23

    # Iterate over the dates in the dataframe
    for date in pd.date_range(candles['time'].dt.date.min(), candles['time'].dt.date.max()):
        if date.dayofweek in (1, 2, 3, 4, 5, 7):  # Only apply to weekdays
            # Add the New York session
            shapes.append(
                dict(
                    type="rect",
                    xref="x",
                    yref="paper",
                    x0=date + pd.Timedelta(hours=session_hours[0]),
                    y0=0,
                    x1=date + pd.Timedelta(hours=session_hours[1]),
                    y1=1,
                    fillcolor="Red",
                    opacity=0.3,
                    layer="below",
                    line_width=0,
                )
            )

    fig.update_layout(shapes=shapes)

def add_entry_signals(
    fig: go.Figure,
    candles: CandleLike,
    entry_signals: np.recarray,
    source: str = "close",
    as_prices: bool = False,
)-> None:

    if not as_prices:
        buy_times = candles[entry_signals.buy].time
        buy_prices = candles[entry_signals.buy][source]

        sell_times = candles[entry_signals.sell].time
        sell_prices = candles[entry_signals.sell][source]
    else:
        buy_index = ~np.isnan(entry_signals.buy)
        buy_times = candles[buy_index].time
        buy_prices = entry_signals.buy[buy_index]

        sell_index = ~np.isnan(entry_signals.sell)
        sell_times = candles[sell_index].time
        sell_prices = entry_signals.sell[sell_index]

    fig.add_scatter(
        x=buy_times,
        y=buy_prices,
        name="buy",
        legendgroup="entries",
        mode='markers',
        opacity=0.8,
        marker=dict(
            size=8,
            symbol="arrow-right",
            # angle=45,
            color="Green",
            line=dict(
                width=1,
                color="midnightblue"
            )
        ),
    )
    fig.add_scatter(
        x=sell_times,
        y=sell_prices,
        name="sell",
        legendgroup="entries",
        mode='markers',
        opacity=0.8,
        marker=dict(
            size=8,
            symbol="arrow-right",
            # angle=135,
            color="Red",
            line=dict(
                width=1,
                color="midnightblue"
            )
        ),
    )

def add_exit_signals(
    fig: go.Figure,
    candles: CandleLike,
    exit_signals: np.recarray,
    source: str = "close",
    as_prices: bool = False,
):
    if not as_prices:
        buy_times = candles[exit_signals.buy].time
        buy_prices = candles[exit_signals.buy][source]

        sell_times = candles[exit_signals.sell].time
        sell_prices = candles[exit_signals.sell][source]
    else:
        buy_index = ~np.isnan(exit_signals.buy)
        buy_times = candles[buy_index].time
        buy_prices = exit_signals.buy[buy_index]

        sell_index = ~np.isnan(exit_signals.sell)
        sell_times = candles[sell_index].time
        sell_prices = exit_signals.sell[sell_index]

    fig.add_scatter(
        x=buy_times,
        y=buy_prices,
        name="buy",
        legendgroup="exits",
        mode='markers',
        opacity=0.8,
        marker=dict(
            size=8,
            symbol="x",
            # angle=45,
            color="Green",
            line=dict(
                width=1,
                color="midnightblue"
            )
        ),
    )
    fig.add_scatter(
        x=sell_times,
        y=sell_prices,
        name="sell",
        legendgroup="exits",
        mode='markers',
        opacity=0.8,
        marker=dict(
            size=8,
            symbol="x",
            # angle=135,
            color="Red",
            line=dict(
                width=1,
                color="midnightblue"
            )
        ),
    )