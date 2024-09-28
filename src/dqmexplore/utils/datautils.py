import pandas as pd
import numpy as np
from dqmexplore.me_ids import meIDs1D, meIDs2D


def generate_me_dict(me_df):
    """
    Reformats monitoring element dataframe and outputs out a reduced version of it in dictionary form, putting the data into a np array which allows for vectorized operations.
    """
    mes = list(me_df["me"].unique())

    # Formatting data to a way that is easier to manipulate
    me_dict = {}
    for me in mes:

        me_dict[me] = {}

        sorted_dfsubset = me_df[me_df["me"] == me].sort_values(by="ls_number")
        me_id = sorted_dfsubset["me_id"].unique()[0]
        if me_id in meIDs1D:
            dim = 1
        elif me_id in meIDs2D:
            dim = 2
        else:
            raise ValueError("Unrecognized monitoring element id number")
        data_arr = np.array(sorted_dfsubset["data"].to_list())
        entries = np.array(sorted_dfsubset["entries"].to_list())

        me_dict[me]["x_bins"] = np.linspace(
            sorted_dfsubset["x_min"].iloc[0],
            sorted_dfsubset["x_max"].iloc[0],
            int(sorted_dfsubset["x_bin"].iloc[0]),
        )

        if dim == 2:
            me_dict[me]["y_bins"] = np.linspace(
                sorted_dfsubset["y_min"].iloc[0],
                sorted_dfsubset["y_max"].iloc[0],
                int(sorted_dfsubset["y_bin"].iloc[0]),
            )

        me_dict[me]["me_id"] = me_id
        me_dict[me]["dim"] = dim
        me_dict[me]["data"] = data_arr
        me_dict[me]["entries"] = entries

    return me_dict


def normalize(data_dict):
    """
    Normalize a data dictionary
    """
    for me in data_dict.keys():
        summation = data_dict[me]["data"].sum(axis=1, keepdims=True)
        data_dict[me]["data"] = np.nan_to_num(data_dict[me]["data"] / summation, nan=0)
    return data_dict


def integrate(data_dict, ls_filter=[]):
    """
    Integrate data dictionary and replace "data" field with integrated data
    """
    for me in list(data_dict.keys()):
        if len(ls_filter) > 0:
            ls_filter = [x - 1 for x in ls_filter]
            data_dict[me]["data"] = data_dict[me]["data"][ls_filter]
        data_dict[me]["data"] = data_dict[me]["data"].sum(axis=0, keepdims=True)

    return data_dict


def trig_normalize(data_dict, trigger_rates: np.ndarray) -> np.ndarray:
    """
    Normalize by trigger rate.
    """
    mes = list(data_dict.keys())
    for me in mes:
        if data_dict[me]["dim"] == 1:
            data_dict[me]["data"] = data_dict[me]["data"] / trigger_rates[:, np.newaxis]
        elif data_dict[me]["dim"] == 2:
            n = data_dict[me]["data"].shape[1]
            m = data_dict[me]["data"].shape[2]
            data_dict[me]["data"] = data_dict[me]["data"] / np.repeat(
                trigger_rates[:, np.newaxis], n * m, axis=1
            ).reshape(-1, n, m)
    return data_dict


def makeDF(json):
    datadict = json["data"][0]["attributes"]
    keys = datadict.keys()

    datasetlist = []

    for i in range(len(json["data"])):
        values = json["data"][i]["attributes"].values()
        datasetlist.append(values)
    return pd.DataFrame(datasetlist, columns=keys)


def check_empty_lss(me_df, thrshld=0):
    me_dict = generate_me_dict(me_df)
    empty_me_dict = {}
    for me in list(me_dict.keys()):
        empty_me_dict[me] = {}
        empty_me_dict[me]["empty_lss"] = []
        for i, entries in enumerate(me_dict[me]["entries"]):
            if entries <= thrshld:
                empty_me_dict[me]["empty_lss"].append(i + 1)
    return pd.DataFrame(empty_me_dict).T


def print_availMEs(dials, dims=None, contains=""):
    mes_df = pd.DataFrame([me_qry_rslt.__dict__ for me_qry_rslt in dials.mes.list()])
    if dims in [1, 2]:
        mes_df = mes_df[mes_df["dim"] == dims]
    for me in mes_df[mes_df["me"].str.contains(contains)]["me"]:
        print(me)
