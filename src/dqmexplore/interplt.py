import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dqmexplore.medata import MEData


# Plotting function
def plot1DMEs(
    me_data,
    fig_title="",
    ax_labels=None,
    trigger_rates=None,
    ref_data=None,
    norm=False,
    show=False,
    hspace=0.05,
    vspace=0.15,
    width=1600,
    height=1600,
):
    """
    Create interactive per-LS plotly figure from monitoring element(s) dataframe. Just for one run and for 1D MEs.
    """

    if (not isinstance(me_data, MEData)) or (
        not isinstance(ref_data, MEData) and ref_data is not None
    ):  # Check data data types
        raise TypeError("Data must be of type MEData")

    if (
        norm and trigger_rates is not None
    ):  # There shouldn't be the both types of normalizations at the same time
        raise ValueError("Normalize by area or trigger rate, not both.")

    # # Normalizing
    if trigger_rates is not None:
        to_plot = "trignorm"
        me_data.normData(trigger_rates)
    elif norm:
        to_plot = "norm"
        me_data.normData()
    else:
        to_plot = "data"

    # Integrate reference data if given
    if ref_data is not None:
        ref_data.integrateData(norm=True)

    # Plotting
    fig = create_plot(
        me_data,
        fig_title=fig_title,
        hspace=hspace,
        vspace=vspace,
        width=width,
        height=height,
        ax_labels=ax_labels,
        ref_data=ref_data,
        to_plot=to_plot,
    )

    if show:
        fig.show()
    return fig


def plot2DMEs(
    me_data,
    fig_title="",
    hspace=0.05,
    vspace=0.15,
    width=1600,
    height=1600,
    ax_labels=None,
    trigger_rates=None,
    show=False,
):
    if not isinstance(me_data, MEData):
        raise TypeError("Data must be of type MEData")

    if trigger_rates is not None:
        to_plot = "trignorm"
        me_data.normData(trigger_rates)
    else:
        to_plot = "data"

    # Plotting
    fig = create_plot(
        me_data,
        fig_title=fig_title,
        ax_labels=ax_labels,
        hspace=hspace,
        vspace=vspace,
        width=width,
        height=height,
        to_plot=to_plot,
    )

    if show:
        fig.show()
    return fig


def create_plot(
    me_data,
    fig_title,
    hspace,
    vspace,
    width,
    height,
    ref_data=None,
    ax_labels=None,
    to_plot=None,
):
    """
    Creates plotly interactive per-LS plot
    """
    if to_plot is None:
        raise ValueError("Specify what will be plotted")

    # Check dimensions
    all_1D = np.array([me_data.getDims(me) == 1 for me in me_data.getMENames()]).all()
    if (not all_1D) and (ref_data is not None):
        raise ValueError(
            "Reference data given for invalid ME type(s). Plot 2D reference MEs separately."
        )

    # Getting info about data
    num_mes = len(me_data)
    num_lss = me_data.getNumLSs()
    num_rows = (num_mes + 1) // 2
    num_cols = 2 if num_mes > 1 else 1
    mes = me_data.getMENames()

    # Making subplot and traces
    fig = make_subplots(
        rows=num_rows,
        cols=num_cols,
        subplot_titles=mes,
        vertical_spacing=vspace,
        horizontal_spacing=hspace,
    )
    fig.update_annotations(font_size=10)

    traces = []

    for i, me in enumerate(mes):
        row = (i // num_cols) + 1
        col = (i % num_cols) + 1
        for ls in range(num_lss):
            if me_data.getDims(me) == 1:
                trace = go.Bar()
                trace.x = me_data.getBins(me, dim="x")
                trace.y = me_data.getData(me, ls=ls, type=to_plot)
            elif me_data.getDims(me) == 2:
                trace = go.Heatmap()
                trace.x = me_data.getBins(me, dim="x")
                trace.y = me_data.getBins(me, dim="y")
                trace.z = me_data.getData(me, ls=ls, type=to_plot)
            trace.name = me

            trace.visible = ls == 0
            traces.append(trace)
            fig.add_trace(traces[-1], row=row, col=col)

    steps = []
    for i in range(num_lss):
        step = {
            "method": "restyle",
            "args": [
                {"visible": [False] * num_mes * num_lss + [True] * len(mes)},
            ],
            "label": f"LS {i+1}",
        }
        for j in range(num_mes):
            step["args"][0]["visible"][i + j * num_lss] = True
        steps.append(step)

    sliders = [
        {
            "active": 0,
            "currentvalue": {"prefix": "LS: "},
            "pad": {"t": 50},
            "steps": steps,
        }
    ]

    # Making plots a bit prettier
    fig.update_layout(
        sliders=sliders,
        title_text=fig_title,
        title_font={"size": 24},
        bargap=0,
        showlegend=False,
        width=width,
        height=height,
    )

    for i, me in enumerate(mes):

        row = (i // num_cols) + 1
        col = (i % num_cols) + 1

        max_data = me_data.getData(me, type=to_plot).max()
        if me_data.getDims(me) == 1:
            fig.update_yaxes(range=[0, max_data], row=row, col=col)

        if me_data.getDims(me) == 2:
            fig.update_traces(showscale=False)

        if ax_labels is not None:
            fig.update_xaxes(title_text=ax_labels[i]["x"], row=row, col=col)
            fig.update_yaxes(title_text=ax_labels[i]["y"], row=row, col=col)

        if ref_data is not None:
            trace_ref = go.Scatter()
            trace_ref.name = me + "-Reference"
            trace_ref.x = ref_data.getBins(me, dim="x")
            trace_ref.y = ref_data.getData(me, type="integral")
            trace_ref.opacity = 0.6
            trace_ref.line = dict(shape="hvh")
            fig.add_trace(trace_ref, row=row, col=col)

    return fig
