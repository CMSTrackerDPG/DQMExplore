import pandas as pd
import numpy as np
import os
import json
import requests
from cmsdials.filters import (
    LumisectionHistogram1DFilters,
    LumisectionHistogram2DFilters,
)
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


def makeDF(data):
    datadict = data["data"][0]["attributes"]
    keys = datadict.keys()

    datasetlist = []

    for i in range(len(data["data"])):
        values = data["data"][i]["attributes"].values()
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


def loadJSONasDF(JSONFilePath):
    if not os.path.exists(JSONFilePath):
        raise FileNotFoundError(
            "ERROR in json_utils.py / loadjson: requested json file {} does not seem to exist...".format(
                JSONFilePath
            )
        )
    with open(JSONFilePath, "r") as f:
        JSONdict = json.load(f)
    try:
        jsondf = pd.DataFrame(JSONdict).convert_dtypes()
    except Exception:
        jsondf = pd.DataFrame(JSONdict.items()).convert_dtypes()
    return jsondf


def loadFromWeb(url, output_file):
    try:
        # Make request and check if successful
        response = requests.get(url)
        if response.status_code == 200:
            # Parse the response content as JSON
            data = response.json()

            # Store the data as JSON
            with open(output_file, "w") as file:
                json.dump(data, file, indent=4)

            print(f"Data successfully fetched and stored in {output_file}")
        else:
            print(f"Failed to fetch data. HTTP Status Code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")


def fetch_data(
    runnbs: int | list[int], me_names: list[str], dials=None
) -> pd.DataFrame:
    if dials is None:
        from dqmexplore.utils.setupdials import setup_dials_object_deviceauth

        dials = setup_dials_object_deviceauth()

    me_id_map = get_me_id_map().set_index("me")
    if isinstance(runnbs, int):
        runnbs = [runnbs]

    query_rslts = {runnb: {} for runnb in runnbs}
    for runnb in runnbs:
        for me_name in me_names:
            if me_id_map.loc[me_name]["dim"] == 1:
                query_rslts[runnb][me_name] = dials.h1d.list_all(
                    LumisectionHistogram1DFilters(
                        run_number=runnb,
                        dataset__regex="ZeroBias",
                        me=me_name,
                    ),
                    max_pages=200,
                ).to_pandas()
            elif me_id_map.loc[me_name]["dim"] == 2:
                query_rslts[runnb][me_name] = dials.h2d.list_all(
                    LumisectionHistogram2DFilters(
                        run_number=runnb,
                        dataset__regex="ZeroBias",
                        me=me_name,
                    ),
                    max_pages=200,
                ).to_pandas()
            else:
                raise ValueError(
                    f"Unrecognized monitoring element id number for {me_name} for "
                )

    query_rslt = pd.concat(
        [
            df
            for runnb in runnbs
            for df in query_rslts[runnb].values()
            if df is not None
        ],
        ignore_index=True,
    )
    return query_rslt


def get_me_id_map():
    this_dir = os.path.dirname(__file__)
    json_path = os.path.join(this_dir, "me_id_map.json")
    return pd.read_json(json_path)
