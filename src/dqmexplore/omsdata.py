import pandas as pd
from cmsdials.filters import OMSFilter, OMSPage
import dask
from dask import delayed
from dqmexplore.utils.datautils import makeDF


class OMSData:
    def __init__(self, dials):
        self.dials = dials
        self.runfilters = []  # List of filters for runs
        self.filters = []  # List of other types of filters (e.g. max num lss)
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
        self._resetDataDict()

    def __getitem__(self, endpoint):
        return self._data[endpoint]

    def _resetDataDict(self, endpoint="all"):
        if endpoint == "all":
            self._data = {endpoint: None for endpoint in self.endpoints}
        else:
            self._data[endpoint] = None

    def _resetFilters(self):
        self.filters = []

    def _resetRunFilters(self):
        self.runfilters = []

    def getEndpoints(self):
        return self.endpoints

    def getRunFilters(self):
        return self.runfilters

    def getRunnbs(self):
        runnbs = []
        for runFilter in self.runfilters:
            runnbs.append(runFilter.value)
        return runnbs

    def getFilters(self):
        return self.filters

    def getData(self, endpoint="runs"):
        return self._data[endpoint]

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

    def setRuns(self, runnbs: list, keep_prev=True):
        if not keep_prev:
            self._resetRunFilters()
        for runnb in runnbs:
            self.runfilters.append(
                OMSFilter(attribute_name="run_number", value=runnb, operator="EQ")
            )

    def setFilters(self, filters: dict, keep_prev=True):
        if not keep_prev:
            self._resetFilters()
        for filter in filters:
            self.filters.append(OMSFilter(**dict))

    def fetchData(self, endpoint="runs", keep_prev=True):
        """
        Fetches data from OMS endpoints using Dask for parallel execution.
        """
        if not keep_prev:
            self._resetDataDict(endpoint=endpoint)

        @delayed
        def fetch_single_filter(runFilter):
            try:
                query_result = self.dials.oms.query(
                    endpoint=endpoint, filters=[runFilter]
                )
                if query_result:
                    df = makeDF(query_result)

                    # Specific indexing based on endpoint
                    if endpoint == "runs":
                        df["run_number_idx"] = df["run_number"]
                        df.set_index("run_number_idx", inplace=True)
                        df.index.name = "run_number"
                    elif endpoint == "lumisections":
                        df["run_number_idx"] = df["run_number"]
                        df["lumisection"] = df["lumisection_number"]
                        df.set_index(["run_number_idx", "lumisection"], inplace=True)
                        df.index.names = ["run_number", "lumisection"]
                    return df
            except Exception as e:
                print(f"WARNING: Unable to fetch data for filter {runFilter}: {e}")
                return None

        tasks = [fetch_single_filter(runFilter) for runFilter in self.runfilters]
        results = dask.compute(*tasks)
        for df in results:
            if df is not None:
                if self._data[endpoint] is None:
                    self._data[endpoint] = df
                else:
                    self._data[endpoint] = pd.concat([self._data[endpoint], df])
