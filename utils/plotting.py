import numpy as np
import plotly.graph_objects as go

from trade.metadata import CandleLike
from datatools.technical import above, below, onband


def make_figure():
    return go.Figure()


def add_ohcl_chart(fig, candles: CandleLike):
    fig.add_ohlc(
        x=candles.index,
        open=candles.open,
        high=candles.high,
        low=candles.low,
        close=candles.close,
        name="price"
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
        x=candles.index,
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
        x=candles.index,
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
        x=candles.index,
        y=bears,
        name="bearish",
        mode="markers+lines",
        line={'color': 'red', 'width': 1},
        marker={"color": "red", "size": 3},
        legendgroup=legendgroup,
    )

    #fig.add_scatter(x=candles.index, y=series2)


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
            x=candles.index,
            y=series,
            name=source,
            mode="lines",
            line={'color': 'red', 'width': 1},
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
