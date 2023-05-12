import plotly.graph_objects as go
import numpy as np

import pandas as pd
from datetime import datetime
pd.options.plotting.backend = "plotly"

# sample data
df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv')
df.index = df.Date
df = df[['AAPL.Close', 'mavg']]
df['mavg2'] = df['AAPL.Close'].rolling(window=50).mean()
df.columns = ['y', 'ma1', 'ma2']
df=df.tail(250).dropna()
df1 = df.copy()

# split data into chunks where averages cross each other
fig = go.Figure()

def add_regime_line(fig, time, line1, line2, name:str):
    mask = np.where(line1 > line2, line1, np.nan)

    fig.add_scattergl(x=xs, y=df.y.where(df.y < df.z), line={'color': 'green'}, marker={"color": "black"}, legendgroup="Regime")
    # fig.add_scattergl(x=xs, y=df.z, line={'color': 'black'})

    # Above threshhgold
    fig.add_scattergl(x=xs, y=df.y.where(df.y >= df.z), line={'color': 'red'}, legendgroup="Regime")

    # # include averages
    # fig.add_traces(go.Scatter(x=df1.index, y = df1.ma1,
    #                           line = dict(color = 'blue', width=1)))

    # fig.add_traces(go.Scatter(x=df1.index, y = df1.ma2,
    #                           line = dict(color = 'red', width=1)))

    # include main time-series
    fig.add_traces(go.Scatter(x=df1.index, y = df1.y,
                            line = dict(color = 'black', width=2)))

    fig.update_layout(showlegend=False)
    fig.show()