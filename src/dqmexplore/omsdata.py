import pandas as pd
from cmsdials.filters import OMSFilter, OMSPage
from dqmexplore.utils.datautils import makeDF
import numpy as np
import json

OPS = ["EQ", "NEQ", "LT", "GT", "LE", "GE", "LIKE"]


class OMSData:
    def __init__(self, dials):
        self.dials = dials
        self.endpoints = [
            "runs",
            "runkeys",
            "l1configurationkey",  # Not working
            "l1algorithmtriggers",
            "hltconfigdata",
            "deadtime",  #
            "daqreadouts",
            "fill",  #
            "l1triggerrate",  # Not working
            "lumisections",
        ]
        self._resetDataDict()  # Initializes as empty dictionary
        self._resetFilters()
        self._gold_runs = None
        self._baddata = {"runs": None, "lumisections": None}

    def _resetDataDict(self, endpoint="all"):
        if endpoint == "all":
            self._data = {endpoint: None for endpoint in self.endpoints}
        else:
            self._data[endpoint] = None

    def _resetFilters(self):
        self.filters = []

    def _targetstoOMSFilter(self, cand_filters, attr_name, flat=True):
        """Converts a target filter to single or list of OMSFilter objects."""
        fltrs = []
        for fltr in cand_filters:
            if isinstance(fltr, int):
                fltrs.append(
                    OMSFilter(attribute_name=attr_name, value=fltr, operator="EQ")
                )
            elif isinstance(fltr, list):
                range_to_add = [
                    OMSFilter(attribute_name=attr_name, value=min(fltr), operator="GE"),
                    OMSFilter(attribute_name=attr_name, value=max(fltr), operator="LE"),
                ]
                if flat:
                    fltrs.extend(range_to_add)
                else:

                    fltrs.append(range_to_add)
            else:
                raise ValueError("Invalid filter type. Expected int or list.")
        return fltrs

    def setFilters(self, filters: dict | str) -> dict:
        """
        Set filters for the data fetch.
        """

        if isinstance(filters, str):
            with open(filters) as f:
                filters = json.load(f)

        self._resetFilters()
        if "runs" not in filters.keys() and "fills" not in filters.keys():
            print(
                "WARNING: No temporal filters set. Use run_number or fill_number to set filters."
            )
        attr_fltrs = {"runs": [], "filters": []}
        runs = filters.get("runs", None)

        # Adding run filter (i.e. choosing which runs to fetch)
        if isinstance(runs, list):
            attr_fltrs["runs"] = self._targetstoOMSFilter(
                runs, "run_number", flat=False
            )

        # Adding feature filters
        if filters.get("filters", None):
            for attr, fltr in filters["filters"].items():
                for op, val in fltr.items():
                    if op not in OPS:
                        raise ValueError(f"Invalid operator: {op}.")
                    if isinstance(val, list):
                        for (
                            v
                        ) in (
                            val
                        ):  # allows for setting multiple filters on a single attr
                            attr_fltrs["filters"].append(
                                OMSFilter(attribute_name=attr, value=v, operator=op)
                            )
                    else:
                        attr_fltrs["filters"].append(
                            OMSFilter(attribute_name=attr, value=val, operator=op)
                        )

        self.filters = attr_fltrs
        return self.filters

    def _formatRunQuery(self, query_results: dict) -> pd.DataFrame | None:
        df = makeDF(query_results)
        if df.empty:
            return None
        df["run_number_idx"] = df["run_number"]
        df.set_index("run_number_idx", inplace=True)
        df.index.name = "runnb"
        return df

    def _formatLSQuery(self, query_results: dict):
        if not query_results:
            return None

        df = makeDF(query_results)
        if df.empty:
            return None
        df["run_number_idx"] = df["run_number"]
        df["lumisection"] = df["lumisection_number"]
        df.set_index(["run_number_idx", "lumisection"], inplace=True)
        df.index.names = ["runnb", "lumisection"]
        return df

    def _formatOthers(self, query_results):
        if not query_results:
            return None

        dfs = map(makeDF, query_results)
        df = pd.concat(dfs, ignore_index=True)
        if not df.empty:
            return df
        else:
            return None

    def _query(self, endpoint: str, filters: list[OMSFilter]) -> pd.DataFrame | None:
        """Queries the OMS through DIALS and formats the results."""

        query_results = self.dials.oms.query(
            endpoint=endpoint,
            filters=filters,
            pages=[OMSPage(attribute_name="limit", value=2000)],
        )
        if len(query_results["data"]) == 0:
            raise ValueError("Empty query.")

        if endpoint == "runs":
            query_results = self._formatRunQuery(query_results)
        elif endpoint == "lumisections":
            query_results = self._formatLSQuery(query_results)
        else:
            query_results = self._formatOthers(query_results)

        return query_results

    def fetchData(
        self,
        endpoint: str = "runs",
        include: list[str] = [],
        ignore_filters: bool = False,
        match_runs: bool = False,
    ):
        """Fetches data from OMS through DIALS."""

        if endpoint not in self.endpoints:
            raise ValueError(f"Invalid endpoint: {endpoint}.")
        if self._data[endpoint] is not None:
            print(
                f"WARNING: Data already fetched for endpoint: {endpoint}. Will try appending to the existing data."
            )

        results_lst = []  # List of formatted (into dfs) query results
        if (endpoint != "lumisections") or (
            endpoint == "lumisections" and not match_runs
        ):
            for run_fltrs in self.filters["runs"]:

                if not isinstance(run_fltrs, list):
                    run_fltrs = [run_fltrs]
                filters = (
                    run_fltrs if ignore_filters else run_fltrs + self.filters["filters"]
                )

                try:
                    results_lst.append(self._query(endpoint, filters))
                except Exception as e:
                    print(f"WARNING: Unable to fetch data for filter {run_fltrs}: {e}")

            if include:
                include_filters = self._targetstoOMSFilter(
                    include, "run_number", flat=False
                )
                try:
                    results_lst.append(self._query(endpoint, include_filters))
                except Exception as e:
                    print(
                        f"WARNING: Unable to fetch data for filter {self.filters}: {e}"
                    )

        else:
            if self._data["runs"] is None:
                raise ValueError(
                    "No runs data available to match lumisections with runs. Please fetch runs data first."
                )
            runs_runnbs = self._data["runs"].index.to_list()
            # Turn run numbers into OMSFilter objects
            run_fltrs = self._targetstoOMSFilter(runs_runnbs, "run_number", flat=False)
            # iterate over run filters and fetch lumisections for each run
            for run_fltr in run_fltrs:
                try:
                    results_lst.append(self._query(endpoint, [run_fltr]))
                except Exception as e:
                    print(f"WARNING: Unable to fetch data for filter {run_fltr}: {e}")

        # Filter None values or empty DataFrames
        results_lst = [res for res in results_lst if res is not None and not res.empty]

        # Concatenate all results into a single DataFrame
        if not results_lst:
            print(f"WARNING: No data fetched for endpoint: {endpoint}.")
            return None

        results_df = pd.concat(results_lst, ignore_index=False)

        if not len(results_df):
            print(f"WARNING: No data fetched for endpoint: {endpoint}.")
            return None

        results_df = results_df[~results_df.index.duplicated(keep="first")]
        self._data[endpoint] = results_df
        return self._data[endpoint]

    def applyGoldenJSON(self, gold_runs: str | dict, keep=[]):
        """
        Filters the 'runs' and 'lumisections' DataFrames based on a golden JSON file.
        Entries not matching the golden JSON are stored in separate DataFrames.
        """
        if isinstance(gold_runs, str):
            with open(gold_runs) as f:
                gold_runs = json.load(f)

        self._gold = gold_runs
        gold_runnbs = list(map(int, gold_runs.keys()))
        self._baddata = {"runs": None, "lumisections": None}

        # Filtering runs DF
        if self._data["runs"] is not None:
            runs_df = self._data["runs"]
            golden_run_filter = runs_df.index.isin(gold_runnbs) | np.array(
                runs_df.index.isin(keep)
            )
            self._data["runs"] = runs_df[golden_run_filter]
            self._baddata["runs"] = runs_df[~golden_run_filter]
        if self._data["lumisections"] is not None:
            lss_df = self._data["lumisections"]
            golden_ls_filter = lss_df.index.get_level_values("runnb").isin(
                gold_runnbs
            ) | np.array(lss_df.index.get_level_values("runnb").isin(keep))
            self._data["lumisections"] = lss_df[golden_ls_filter]
            self._baddata["lumisections"] = lss_df[~golden_ls_filter]

    def __getitem__(self, endpoint):
        return self._data[endpoint]

    def getFilters(self):
        return self.filters

    def getRunnbs(self):
        runs = []
        for runfilter in self.filters["runs"]:
            if isinstance(runfilter, list):
                runs.append([runfilter[0].value, runfilter[1].value])
            else:
                runs.append(runfilter.value)
        return runs

    def getAvailFtrs(self, which="all"):
        if which == "all":
            return {
                key: df.columns.to_list() if isinstance(df, pd.DataFrame) else None
                for key, df in self._data.items()
            }
        elif which == "numerical":
            return {
                key: (
                    df.select_dtypes(include=[int, float]).columns.to_list()
                    if isinstance(df, pd.DataFrame)
                    else None
                )
                for key, df in self._data.items()
            }
        elif which == "bools":
            return {
                key: (
                    df.select_dtypes(include=[bool]).columns.to_list()
                    if isinstance(df, pd.DataFrame)
                    else None
                )
                for key, df in self._data.items()
            }
        else:
            return None
