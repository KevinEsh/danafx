import numpy as np
import plotly.graph_objects as go
import pandas as pd

from trade.metadata import CandleLike


class FxFigure:
    def __init__(self) -> None:
        self.fig = go.Figure()

    def reset_figure(self):
        self.fig = go.Figure()

    def add_ohcl_chart(self, candles: CandleLike):
        self.fig.add_ohlc(
            x=candles.time,
            open=candles.open,
            high=candles.high,
            low=candles.low,
            close=candles.close,
            name="ohlc",
            legendgroup="candle",
            legendgrouptitle_text="candle",
            increasing_line_color='white',
            decreasing_line_color= 'grey',
        )

        self.fig.update_yaxes(
            side="right",
            tickprefix="$",
            ticklabelposition="outside right",
        )

        self.fig.update_layout(
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
        self,
        candles: CandleLike,
        trendline: np.recarray,
        legendgroup: str = "regime",
    ):
        self.fig.add_scattergl(
            x=candles.time,
            y=trendline.bullish,
            name="bullish",
            mode="markers+lines",
            line={'color': 'green', 'width': 1},
            marker={"color": "green", "size": 3},
            legendgroup=legendgroup,
            # legendgrouptitle_text=legendgroup,
        )

        self.fig.add_scattergl(
            x=candles.time,
            y=trendline.neutral,
            name="neutral",
            mode="markers+lines",
            line={'color': 'grey', 'width': 1},
            marker={"color": "grey", "size": 3},
            legendgroup=legendgroup,
        )

        # Above threshold
        self.fig.add_scattergl(
            x=candles.time,
            y=trendline.bearish,
            name="bearish",
            mode="markers+lines",
            line={'color': 'red', 'width': 1},
            marker={"color": "red", "size": 3},
            legendgroup=legendgroup,
        )

        #fig.add_scatter(x=candles.time, y=series2)


    def add_lines(
        self,
        candles: CandleLike,
        sources: tuple[str],
        legendgroup: str = "indicator",
        ylim: tuple[float] = (0, 1)
    ):
        for source in sources:
            series = candles[source]

            self.fig.add_scattergl(
                x=candles.time,
                y=series,
                name=source,
                mode="lines",
                line={'width': 1},
                legendgroup=legendgroup,
                legendgrouptitle_text=legendgroup,
            )

        self.fig.update_yaxes(
            side="right",
            ticklabelposition="outside right",
            # fixedrange=True,
            range=ylim,
        )

        self.fig.update_layout(
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


    def add_session(self, candles, session_hours: tuple[int, int] = (22, 10)):
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

        self.fig.update_layout(shapes=shapes)

    def add_entry_signals(
        self,
        candles: CandleLike,
        entry_signals: np.recarray,
    )-> None:

        # if not as_prices:
        #     buy_times = candles[entry_signals.buy_index].time
        #     buy_prices = candles[entry_signals.buy].open

        #     sell_times = candles[entry_signals.sell].time
        #     sell_prices = candles[entry_signals.sell].open
        # else:
        buy_indexes = entry_signals.buy_index
        buy_times = candles[buy_indexes].time
        buy_prices = entry_signals[buy_indexes].buy_price

        sell_indexes = entry_signals.sell_index
        sell_times = candles[sell_indexes].time
        sell_prices = entry_signals[sell_indexes].sell_price

        self.fig.add_scatter(
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

        self.fig.add_scatter(
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
        self,
        candles: CandleLike,
        exit_signals: np.recarray,
        show_matches: bool = False,
    ):
        # if not as_prices:
        #     buy_times = candles[exit_signals.buy].time
        #     buy_prices = candles[exit_signals.buy].open

        #     sell_times = candles[exit_signals.sell].time
        #     sell_prices = candles[exit_signals.sell].open
        # else:
        mask_buy = ~np.isnan(exit_signals.buy_index)
        buy_indexes = exit_signals[mask_buy].buy_index.astype(int)
        buy_prices = exit_signals[mask_buy].buy_price
        buy_times = candles[buy_indexes].time

        mask_sell = ~np.isnan(exit_signals.sell_index)
        sell_indexes = exit_signals[mask_sell].sell_index.astype(int)
        sell_prices = exit_signals[mask_sell].sell_price
        sell_times = candles[sell_indexes].time

            # print(buy_indexes, buy_prices, buy_times)

        self.fig.add_scatter(
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

        self.fig.add_scatter(
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

        if not show_matches:
            return
        
        