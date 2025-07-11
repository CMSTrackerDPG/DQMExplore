from dqmexplore.utils.datautils import loadJSONasDF, loadFromWeb
from fnmatch import fnmatch
import pandas as pd

chftrs = [
    "run_number",
    "run_reconstruction_type",
    "reference_run_number",
    "reference_run_reconstruction_type",
    "dataset",
]


class CHRunData:
    """
    Certification Helper data manager.
    This class is used to load and manage the Certification Helper data.
    """

    def __init__(
        self,
        JSONFilePath: str,
        goldenJSONFilePath: str | None = None,
    ) -> None:
        self.RunsDF = loadJSONasDF(JSONFilePath)
        self.RunsDF.dropna(inplace=True)
        self._setGolden(goldenJSONFilePath)
        self.RunsDF.sort_values("run_number", inplace=True)

    def _setGolden(self, goldenJSONFilePath: str | None = None) -> None:
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

    def getGoodRuns(self) -> pd.DataFrame:
        return self.RunsDF[self.RunsDF["good_lss"].notnull()]

    def getRuns(self, exclude_bad: bool = False) -> pd.DataFrame:
        if exclude_bad:
            if not hasattr(self, "goldenDF"):
                raise LookupError(
                    "Golden JSON file not set. Cannot filter for good runs."
                )
            return self.getGoodRuns()
        else:
            return self.RunsDF

    def getRun(self, runnb: int, reco_type: str | None = None) -> pd.DataFrame:
        if reco_type not in [None, "express", "prompt"]:
            raise ValueError("Unexpected value for reconstruction type given.")
        if reco_type is None:
            return self.RunsDF[self.RunsDF["run_number"] == runnb]
        else:
            return self.RunsDF[
                (self.RunsDF["run_number"] == runnb)
                & (self.RunsDF["run_reconstruction_type"] == reco_type)
            ]

    def applyFilter(
        self, filters: dict = {}, exclude_bad: bool = False, return_df: bool = True
    ) -> pd.DataFrame | list:
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

    def getruns(self, **kwargs) -> pd.DataFrame:
        """
        Get runs based on the provided keyword arguments.

        Args:
            **kwargs: Keyword arguments to filter runs. Valid keys are:
                - run_number
                - run_reconstruction_type
                - reference_run_number
                - reference_run_reconstruction_type
                - dataset
        Returns:
            pd.DataFrame: DataFrame containing the filtered runs.
        """
        runs = self.RunsDF
        for key, value in kwargs.items():
            if key in chftrs:
                runs = runs[runs[key] == value]
            else:
                print(f"Warning: Unexpected key '{key}' in input filter.")
        return runs

    def getRefRun(self, runnb: int, **kwargs) -> int:
        """
        Uses getruns to get the reference run number for a given run number.
        Fails if multiple reference runs are found.
        """
        runs = self.getRuns(run_number=runnb, **kwargs)

        if len(runs) > 1:
            raise LookupError(
                f"Multiple runs found for run number {runnb}. Please refine your search."
            )

        if len(runs) == 0:
            return -1

        return int(runs["reference_run_number"].values[0])

    def searchRuns(self, runnbs: int | list, ref: bool = False) -> pd.DataFrame:
        if not isinstance(runnbs, list):
            runnbs = [runnbs]
        return self.RunsDF[
            self.RunsDF["reference_run_number" if ref else "run_number"].isin(runnbs)
        ]
