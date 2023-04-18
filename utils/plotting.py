import mplfinance as fplt
from numpy import nan


def plot_candlestick_chart(df_rates, symbol: str, timestamp: str) -> None:
    # change columns names to make df compatible with mplfinance
    mpl_comp_names = {
        'time': 'Date',
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'tick_volume': 'Volume'
    }
    saving_config = {
        "fname": f'{symbol}_{timestamp}.jpeg',
        # "dpi": None,
        # "pad_inches": 0.01,
        # "transparent": True
    }

    uptrend = df_rates.regression * df_rates.signal.apply(lambda s: nan if s != 1 else 1)
    downtrend = df_rates.regression * df_rates.signal.apply(lambda s: nan if s != -1 else 1)

    trendmarkers = [
        fplt.make_addplot(
            uptrend,
            color="green",
            linestyle='dotted',
            # type='scatter',
            width=2,
            alpha=0.8,
            marker=".",
            # markersize=20,
        ),
        fplt.make_addplot(
            downtrend,
            color="red",
            linestyle='dotted',
            # type='scatter',
            width=2,
            alpha=0.8,
            marker=".",
            # markersize=20,
        ),
    ]

    fplt.plot(
        df_rates.rename(columns=mpl_comp_names),
        type="ohlc",  # 'hollow_and_filled',  # 'candle',
        style='yahoo',  # 'charles',
        ylabel='Price ($GBP)',
        title=symbol,
        volume=True,
        tight_layout=True,
        figscale=1.25,
        figratio=(5, 2),
        # mav=(5, 20),
        savefig=saving_config,
        addplot=trendmarkers,
        fill_between=[
            {
                "y1": df_rates['down'].values,
                "y2": df_rates['up'].values,
                # "where": df_rates["signal"] == 1,
                "color": "gray",
                "alpha": 0.07,
                # "interpolate": True,
                # "step": 'pre',
                "antialiased": True
            },
        ]
    )
