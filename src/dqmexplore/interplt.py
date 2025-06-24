import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dqmexplore.medata import MEData
from dqmexplore.me_ids import meIDs1D, meIDs2D
from dqmexplore.utils.datautils import get_me_id_map
import json

reqkeys = ["xlim", "ylim", "xlabel", "ylabel", "logy", "norm"]


def add_missing_keys(plots_config):
    for me_name, config in plots_config.items():
        for key in reqkeys:
            if key not in config:
                config[key] = None


def plot1DMEs(
    me_data,
    plots_config: dict | str,
    figure_config: dict | str,
    trigger_rates: np.ndarray | list | None = None,
    ref_data=None,
    show: bool = False,
):
    """Create interactive per-LS plotly figure from monitoring element(s) dataframe. Just for one run and for 1D MEs."""

    if isinstance(plots_config, str):
        with open(plots_config, "r") as f:
            plots_config = json.load(f)
    if isinstance(figure_config, str):
        with open(figure_config, "r") as f:
            figure_config = json.load(f)

    # Add missing plot config keys
    add_missing_keys(plots_config)

    # Data type check
    if (not isinstance(me_data, MEData)) or (
        ref_data is not None and not isinstance(ref_data, MEData)
    ):  # Check data data types
        raise TypeError("Data must be of type MEData")

    # Normalizing
    for me_name, config in plots_config.items():
        if config.get("norm"):
            if (config.get("norm") == "trig") and (trigger_rates is None):
                raise ValueError(
                    "Trigger rate normalization requested, but trigger rates are not provided."
                )
            me_data.normData(
                trigger_rate=(
                    trigger_rates if config.get("norm") == "trignorm" else None
                ),
                mes=[me_name],
            )

    # Integrate reference data if given
    if ref_data is not None:
        ref_data.integrateData(norm=True)

    # Plotting
    fig = create_plot(
        me_data,
        figure_config,
        plots_config,
        ref_data=ref_data,
    )

    if show:
        fig.show()
    return fig


def plot2DMEs(
    me_data,
    plots_config: dict | str,
    figure_config: dict | str,
    trigger_rates: np.ndarray | list | None = None,
    ref_data=None,
    show: bool = False,
):
    """Create interactive per-LS plotly figure from monitoring element(s) dataframe. Just for one run and for 1D MEs."""

    if isinstance(plots_config, str):
        with open(plots_config, "r") as f:
            plots_config = json.load(f)
    if isinstance(figure_config, str):
        with open(figure_config, "r") as f:
            figure_config = json.load(f)

    # Add missing plot config keys
    add_missing_keys(plots_config)

    # Data type check
    if (not isinstance(me_data, MEData)) or (
        ref_data is not None and not isinstance(ref_data, MEData)
    ):  # Check data data types
        raise TypeError("Data must be of type MEData")

    # Normalizing
    for me_name, config in plots_config.items():
        if config.get("norm"):
            if (config.get("norm") == "trig") and (trigger_rates is None):
                raise ValueError(
                    "Trigger rate normalization requested, but trigger rates are not provided."
                )
            me_data.normData(
                trigger_rate=(
                    trigger_rates if config.get("norm") == "trignorm" else None
                ),
                mes=[me_name],
            )

    # Integrate reference data if given
    if ref_data is not None:
        ref_data.integrateData(norm=True)

    # Plotting
    fig = create_plot(
        me_data,
        figure_config,
        plots_config,
        ref_data=ref_data,
    )

    if show:
        fig.show()
    return fig


def plotMEs(
    me_data,
    plots_config: dict | str,
    figure_config: dict | str,
    trigger_rates: np.ndarray | list | None = None,
    ref_data=None,
    show: bool = False,
):
    """
    Create interactive per-LS plotly figure from monitoring element(s) dataframe.
    Supports both 1D and 2D MEs for a single run.
    """

    # Load configs from file if passed as path
    if isinstance(plots_config, str):
        with open(plots_config, "r") as f:
            plots_config = json.load(f)
    if isinstance(figure_config, str):
        with open(figure_config, "r") as f:
            figure_config = json.load(f)

    # Add missing plot config keys
    add_missing_keys(plots_config)

    # Type checks
    if not isinstance(me_data, MEData):
        raise TypeError("me_data must be of type MEData")
    if ref_data is not None and not isinstance(ref_data, MEData):
        raise TypeError("ref_data must be of type MEData")

    # Normalizing
    for me_name, config in plots_config.items():
        if config.get("norm"):
            if config["norm"] == "trig" and trigger_rates is None:
                raise ValueError(
                    "Trigger rate normalization requested but trigger rates not provided."
                )
            me_data.normData(
                trigger_rate=trigger_rates if config["norm"] == "trignorm" else None,
                mes=[me_name],
            )

    # Reference data integration
    if ref_data is not None:
        ref_data.integrateData(norm=True)

    # Plotting
    fig = create_plot(
        me_data,
        figure_config,
        plots_config,
        ref_data=ref_data,
    )

    if show:
        fig.show()
    return fig


def create_plot(
    me_data,
    figure_config,
    plots_config,
    ref_data=None,
):
    """
    Creates plotly interactive per-LS plot
    """

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
    me_id_map = get_me_id_map().set_index("me")
    mixed_fig = len(me_id_map.loc[mes]["me_id"].unique()) > 1

    # Making subplot and traces
    subplot_titles = [
        mes[i].split("/")[-1] if figure_config.get("short_titles") else mes[i]
        for i in range(num_mes)
    ]
    fig = make_subplots(
        rows=num_rows,
        cols=num_cols,
        subplot_titles=subplot_titles,
        vertical_spacing=figure_config.get("vspace", 0.15),
        horizontal_spacing=figure_config.get("hspace", 0.05),
    )
    fig.update_annotations(font_size=10)

    traces = []
    for i, me in enumerate(mes):
        row = (i // num_cols) + 1
        col = (i % num_cols) + 1
        config = plots_config.get(me, add_missing_keys({}))
        to_plot = config.get("norm", None)
        for ls in range(num_lss):
            if me_data.getDims(me) == 1:
                trace = go.Bar()
                trace.x = me_data.getBins(me, dim="x")
                trace.y = me_data.getData(me, ls=ls, data_type=to_plot)
            elif me_data.getDims(me) == 2:
                trace = go.Heatmap()
                trace.x = me_data.getBins(me, dim="x")
                trace.y = me_data.getBins(me, dim="y")
                trace.z = me_data.getData(me, ls=ls, data_type=to_plot)
            trace.name = me

            trace.visible = ls == 0
            traces.append(trace)
            fig.add_trace(traces[-1], row=row, col=col)

    steps = []
    for i in range(num_lss):
        step = {
            "method": "restyle",
            "args": [
                {"visible": [False] * (num_mes * num_lss) + [True] * len(mes)},
            ],
            "label": f"{i+1}",
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

    # Updating layout from figure_config
    fig.update_layout(
        sliders=sliders,
        title_text=figure_config.get("figure_title", ""),
        title_font={"size": 24},
        bargap=0,
        showlegend=False,
        width=figure_config.get("width", 1000),
        height=figure_config.get("height", 1000),
    )

    # Updating axes for subplots using plot configurations
    for i, me in enumerate(mes):
        row = (i // num_cols) + 1
        col = (i % num_cols) + 1
        config = plots_config.get(me, add_missing_keys({}))
        to_plot = config.get("norm", None)
        max_data = me_data.getData(me, data_type=to_plot).max()

        if me_data.getDims(me) == 1:
            fig.update_xaxes(
                range=config.get("xlim"),
                type="log" if config.get("logx") else "linear",
                row=row,
                col=col,
            )
            fig.update_yaxes(
                range=compute_range(config, max_data, axis="y"),
                type="log" if config.get("logy") else "linear",
                row=row,
                col=col,
            )

        if (me_data.getDims(me) == 2) and (not mixed_fig):
            fig.update_traces(showscale=figure_config.get("show_colorbar", False))

        fig.update_xaxes(title_text=config.get("xlabel"), row=row, col=col)
        fig.update_yaxes(title_text=config.get("ylabel"), row=row, col=col)

        if ref_data is not None:
            trace_ref = go.Scatter()
            trace_ref.name = me + "-Reference"
            trace_ref.x = ref_data.getBins(me, dim="x")
            trace_ref.y = ref_data.getData(me, data_type="integral")
            trace_ref.opacity = 0.6
            trace_ref.line = dict(shape="hvh")
            fig.add_trace(trace_ref, row=row, col=col)
    return fig


def compute_range(config, max_data, axis="y"):
    # If user provides ylim, use it
    if config.get(f"{axis}lim") is not None:
        range_min, range_max = config.get(f"{axis}lim")
        if config.get(f"log{axis}"):
            return [np.log10(max(range_min, 1e-3)), np.log10(max(range_max, 1e-3))]
        return (range_min, range_max)

    # If user does not provide ylim, calculate it
    if config.get("logy"):
        y_high = max(max_data, 1e-3)
        return [np.log10(1e-3), np.log10(y_high)]

    return [0, max_data]
