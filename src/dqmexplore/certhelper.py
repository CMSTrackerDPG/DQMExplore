from dqmexplore.utils.datautils import loadJSONasDF, loadFromWeb
from fnmatch import fnmatch
import pandas as pd


class CHRunData:
    """
    Class to organize the Reference Runs information from the CertHelper API
    Credit for original JSON implementation: Gabriele Benelli
    """

    def __init__(self, JSONFilePath, goldenJSONFilePath=None, filtergolden=True):
        self.RunsDF = loadJSONasDF(JSONFilePath)
        self.RunsDF.dropna(inplace=True)
        self._setGolden(goldenJSONFilePath)
        self.RunsDF.sort_values("run_number", inplace=True)

    def _setGolden(self, goldenJSONFilePath=None):
        if goldenJSONFilePath is None:
            return
        self.goldenDF = loadJSONasDF(goldenJSONFilePath)
        self.goldenDF = self.goldenDF.rename({0: "run_number", 1: "good_lss"}, axis=1)
        self.goldenDF = self.goldenDF.astype({"run_number": int})

        # Put golden info in RunsDF
        self.RunsDF = self.RunsDF.merge(self.goldenDF, on="run_number", how="left")
        self.RunsDF["good_lss"] = self.RunsDF["good_lss"].where(
            self.RunsDF["good_lss"].notna(), None
        )

    def getGoodRuns(self):
        return self.RunsDF[self.RunsDF["good_lss"].notnull()]

    def getRuns(self, exclude_bad=True):
        if exclude_bad:
            return self.getGoodRuns()
        else:
            return self.RunsDF

    def getRun(self, runnb, reco_type=None):
        if reco_type not in [None, "express", "prompt"]:
            raise ValueError("Unexpected value for reconstruction type given.")
        if reco_type is None:
            return self.RunsDF[self.RunsDF["run_number"] == runnb]
        else:
            return self.RunsDF[
                (self.RunsDF["run_number"] == runnb)
                & (self.RunsDF["run_reconstruction_type"] == reco_type)
            ]

    def applyFilter(self, filters={}, exclude_bad=True, return_df=True):
        if exclude_bad:
            RunsDF = self.getGoodRuns()
        else:
            RunsDF = self.RunsDF

        if len(filters) == 0:
            print("Warning: No filter conditions given.")
            if return_df:
                return RunsDF
            else:
                return RunsDF["run_number"].to_list()

        mask = pd.Series([True] * len(RunsDF), index=RunsDF.index)

        for key, value in filters.items():
            if key in [
                "run_number",
                "reference_run_number",
            ]:  # must be list of ints and/or tuples
                num_mask = pd.Series([False] * len(RunsDF), index=RunsDF.index)
                for val in value:
                    if isinstance(val, list):
                        num_mask |= (RunsDF[key] >= val[0]) & (RunsDF[key] <= val[1])
                    elif isinstance(val, (int, float)):
                        num_mask |= RunsDF[key] == val
                mask &= num_mask
            elif isinstance(value, str) and key in [
                "run_reconstruction_type",
                "reference_run_reconstruction_type",
                "dataset",
            ]:
                mask &= RunsDF[key].apply(lambda x: fnmatch(x, value))
            else:
                raise KeyError("Unexpected key in input filter.")

        if return_df:
            return RunsDF[mask]
        else:
            return RunsDF[mask]["run_number"].to_list()

    def getruns(self, run, colfilters=None):
        CHftrs = [
            "run_number",
            "run_reconstruction_type",
            "reference_run_type",
            "reference_run_reconstruction_type",
            "dataset",
        ]
        try:
            runs = self.RunsDF[self.RunsDF["run_number"] == run]
            if colfilters is None:
                return runs
            else:
                if isinstance(colfilters, list):
                    badftrs = []
                    for colfilter in colfilters:
                        if colfilter not in CHftrs:
                            badftrs.append(colfilter)
                            print(
                                "WARNING: {} not a valid CH feature. Skipping.".format(
                                    colfilter
                                )
                            )
                    return runs[list(set(colfilters) - set(badftrs))]
                else:
                    raise Exception("colfilters must be of type list")
        except Exception:
            raise Exception("Run is not available.")

    def getRefFromRun(self, run, reco_type=None):
        run_info = self.getRun(run, reco_type=reco_type)
        if len(run_info) == 0:
            raise LookupError("No matches found.")
        elif len(run_info) == 1:
            return run_info["reference_run_number"].iloc[0]
        else:
            return run_info
