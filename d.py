import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from preputils.custom import get_recarray

# generate some random data
x = np.arange(100)
y = np.random.randint(0, 10, 100)
# define the condition (for example, if y > 3)
condition = (y > 3).astype(float) #['red' if val > 5 else 'green' for val in y]

df = get_recarray([x, y, condition], names=["time", "value", "cond"])
# create a trace for the line with conditional color scale
fig = go.Figure()

# fig = px.line(df, y="value", x="time", color="cond",
#             line_shape="spline", render_mode="svg",
#             color_continuous_scale=px.colors.diverging.BrBG,
#             # color_discrete_map=,
#              title="Built-in G10 color sequence")

fig.add_trace(go.Scattergl(
    x=df.time,
    y=df.value,
    # marker=dict(
    #     size=16,
    #     cmax=1,
    #     cmin=0,
    #     color=df.cond,
    #     colorbar=dict(
    #         title="Colorbar"
    #     ),
    #     colorscale="Viridis"
    # ),
    line=dict(
        cmax=1,
        cmin=0,
        shape="spline"
        # color=df.cond,
        # colorbar=dict(
        #     title="Colorbar"
        # ),
        # colorscale="Viridis"
    ),
    mode="lines"))

fig.add_trace(go.Scatter(
    x=df.time,
    y=df.value,
    # marker=dict(
    #     size=16,
    #     cmax=1,
    #     cmin=0,
    #     color=df.cond,
    #     colorbar=dict(
    #         title="Colorbar"
    #     ),
    #     colorscale="Viridis"
    # ),
    line=dict(
        cmax=1,
        cmin=0,
        shape="spline"
        # color=df.cond,
        # colorbar=dict(
        #     title="Colorbar"
        # ),
        # colorscale="Viridis"
    ),
    mode="lines"))

# fig.add_trace(
#     go.Scatter(
#         x=x,
#         y=y,
#         mode='lines',
#         line_color="red",
#         marker=dict(
#             line=dict(
#                 color="red",
#                 # colorscale=[[0, 'green'], [1, 'red']],
#                 # cmin=0,
#                 # cmax=1,
#                 # showscale=False
#             )
#         )
#     )
# )

# display the plot
fig.show()
