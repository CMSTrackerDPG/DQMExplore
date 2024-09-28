import numpy as np
import plotly.graph_objects as go
from cmsdials.filters import OMSFilter, OMSPage
from dqmexplore.utils.datautils import makeDF


def get_rate(dials, runnb, dataset_name="ZeroBias", extrafilters=[]):
    filters = [
        OMSFilter(attribute_name="run_number", value=runnb, operator="EQ"),
        OMSFilter(attribute_name="dataset_name", value=dataset_name, operator="EQ"),
    ]

    data = dials.oms.query(
        endpoint="datasetrates",
        filters=filters,
        pages=[OMSPage(attribute_name="limit", value=5000)],
    )

    data_df = makeDF(data)
    data_df.sort_values(by="last_lumisection_number", inplace=True)

    return data_df["rate"].to_numpy()


def plot_rate(rate, fig_title="Trigger Rate", norm=False, show=False):
    fig = go.Figure()

    if norm:
        rate = rate / rate.sum()

    fig.add_trace(go.Scatter(x=np.arange(1, len(rate) + 1), y=rate, mode="lines"))

    fig.update_layout(
        title=fig_title,
        xaxis_title="Lumisection",
        yaxis_title="Trigger rate",
    )

    fig.update_yaxes(range=[0, rate.max() + rate.max() * 0.1])
    fig.update_xaxes(range=[1, len(rate)])

    if show:
        fig.show()
    return fig
