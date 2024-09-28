import plotly.graph_objects as go
from plotly.subplots import make_subplots


def plotMEs1D_static(
    me_data,
    fig_title="",
    ax_labels=None,
    ls_filter=[],
    to_exclude=[],
    ref_data=None,
    show=False,
):

    # Check that all given MEs are either 1D or 2D
    me_dim_sum = 0
    for me in me_data.getMENames():
        me_dim_sum += me_data.getDims(me)

    if me_dim_sum != len(me_data):
        raise ValueError("All MEs to be plotted need to be 1D.")

    # Integrate
    me_data.setExcluded(to_exclude)
    me_data.integrateData(norm=True)
    ref_data.integrate(norm=True)

    fig = create_plot_static(
        me_data, fig_title=fig_title, ref_data=ref_data, ax_labels=ax_labels
    )

    if show:
        fig.show()
    return fig


def create_plot_static(me_data, fig_title="", ref_data=None, ax_labels=None):
    mes = me_data.getMENames()

    num_mes = len(me_data)
    num_rows = (num_mes + 1) // 2
    num_cols = 2 if num_mes > 1 else 1

    fig = make_subplots(
        rows=num_rows,
        cols=num_cols,
        subplot_titles=mes,
        vertical_spacing=0.1,
        horizontal_spacing=0.1,
    )

    for i, me in enumerate(mes):
        row = (i // 2) + 1
        col = (i % 2) + 1
        if me_data.getDims() == 1:
            trace = go.Bar()
            trace.x = me_data.getBins(me, dim="x")
            trace.y = me_data.getData(me, type="integral")
            trace.name = me
        elif me_data.getDims() == 2:
            trace = go.Heatmap()
            trace.x = me_data.getBins(me, dim="x")
            trace.y = me_data.getBins(me, dim="y")
            trace.z = me_data.getData(me, type="integral")
            trace.name = me
        fig.add_trace(trace, row=row, col=col)

    fig.update_layout(
        title_text=fig_title,
        title_font={"size": 24},
        bargap=0,
        showlegend=True,
        width=1500,
        height=1500,
    )

    for i, me in enumerate(mes):

        row = (i // num_cols) + 1
        col = (i % num_cols) + 1

        if me_data.getDims(me) == 1:
            ref_max = (
                0 if ref_data is None else ref_data.getData(me, type="integral").max()
            )

            max_data = max([me_data.getData(me, type="integral").max(), ref_max]) + (
                0.01 if me_data.getData(me, type="integral").max() < 1 else 10
            )
            fig.update_yaxes(range=[0, max_data], row=row, col=col)

        if me_data.getDims(me) == 1:
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


def plotheatmaps1D(
    me_data,
    fig_title="",
    ax_labels=None,
    trigger_rates=None,
    norm=False,
    show=False,
):

    if (
        norm and trigger_rates is not None
    ):  # There shouldn't be the both types of normalizations at the same time
        raise ValueError("Normalize by area or trigger rate, not both.")

    if trigger_rates is not None:
        to_plot = "trignorm"
        me_data.normData(trigger_rate=trigger_rates)
    elif norm:
        to_plot = "norm"
        me_data.normData()
    else:
        to_plot = "data"

    fig = create_heatmap(
        me_data, fig_title=fig_title, ax_labels=ax_labels, to_plot=to_plot
    )

    if show:
        fig.show()
    else:
        return fig


def create_heatmap(me_data, fig_title="", ax_labels=None, to_plot="data"):

    mes = me_data.getMENames()
    num_mes = len(me_data)
    num_rows = (num_mes + 1) // 2
    num_cols = 2 if num_mes > 1 else 1

    # Making figure object
    fig = make_subplots(
        rows=num_rows,
        cols=num_cols,
        subplot_titles=mes,
        vertical_spacing=0.1,
        horizontal_spacing=0.1,
    )

    # Adding heatmap trace to figure
    for i, me in enumerate(mes):
        row = (i // 2) + 1
        col = (i % 2) + 1
        fig.add_trace(
            go.Heatmap(
                z=me_data.getData(me, type=to_plot),
                x=me_data.getBins(me, dim="x"),
                showscale=False,
            ),
            row=row,
            col=col,
        )
        if ax_labels is not None:
            fig.update_xaxes(title_text=ax_labels[i]["x"], row=row, col=col)
            fig.update_yaxes(title_text=ax_labels[i]["y"], row=row, col=col)

    # Adding layour elements to figure
    fig.update_layout(
        title_text=fig_title,
        title_font={"size": 24},
        height=1100,
        width=1100,
        annotations=[dict(text=me, font={"size": 14}, showarrow=False) for me in mes],
    )

    fig.update_yaxes(autorange="reversed")

    return fig
