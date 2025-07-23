import pandas as pd
import os
import json


class Anomaly:
    def __init__(self) -> None:
        self.anomaly_keys: set[str] = ["start_ls", "end_ls", "method", "anomaly_desc"]
        self.anomalies: dict[int, pd.DataFrame] = {}

    def addRun(
        self,
        run_number: int,
        anomalies: list[dict[str, any]] | dict[str, any] | None = None,
    ) -> pd.DataFrame:
        """
        Add a new run to the anomaly dictionary if it does not already exist.
        """
        if run_number not in self.anomalies:
            self.anomalies[run_number] = pd.DataFrame(columns=list(self.anomaly_keys))
            if anomalies is not None:
                self.addEntries(
                    run_number=run_number,
                    anomalies=anomalies if isinstance(anomalies, list) else [anomalies],
                )
        else:
            raise ValueError("Run number already exists.")
        return self.anomalies[run_number]

    def addEntry(
        self,
        run_number: int,
        anomaly: dict[str, any] | None = None,
    ) -> pd.DataFrame | None:
        """
        Add entries to anomaly DataFrame for a given run. If the run does not exist, it will create a new one.
        """

        if run_number not in self.anomalies:
            self.addRun(run_number, anomaly)
            return

        if anomaly is None:
            print(
                f"No anomalies provided for run {run_number}. Adding empty run entry."
            )
            self.addRun(run_number)
            return
        if isinstance(anomaly, dict):
            # Make sure the anomaly has all required keys and no extra keys using set operations
            extra_keys = set(anomaly.keys()) - set(self.anomaly_keys)
            missing_keys = set(self.anomaly_keys) - set(anomaly.keys())
            if extra_keys:
                raise ValueError(
                    f"Anomaly contains extra keys: {extra_keys}. Expected keys: {self.anomaly_keys}."
                )
            if missing_keys:
                raise ValueError(
                    f"Anomaly is missing keys: {missing_keys}. Expected keys: {self.anomaly_keys}."
                )
            self.anomalies[run_number] = pd.concat(
                [self.anomalies[run_number], pd.DataFrame([anomaly])], ignore_index=True
            )

        return self.anomalies[run_number]

    def addEntries(self, run_number: int, anomalies: list[dict]) -> pd.DataFrame:
        """
        Add multiple entries to the anomaly DataFrame of a particular run.
        Each entry should be a dictionary with keys matching the DataFrame columns.
        """

        for anomaly in anomalies:
            self.addEntry(run_number, anomaly)

        return self.anomalies[run_number]

    def rmEntries(
        self,
        run_number: int,
        method: str | None = None,
        anomaly_desc: str | None = None,
    ) -> None:
        """
        Remove an entry from the anomaly DataFrame based on run_number, method, or anomaly_desc.
        """

        anomaly_df = self.anomalies.get(run_number, None)
        if anomaly_df is None:
            raise ValueError(f"Run number {run_number} does not exist in anomalies.")

        if method is not None:
            filtered_df = anomaly_df[anomaly_df["method"] != method]
            if len(filtered_df) == len(anomaly_df):
                raise ValueError(
                    f"No entries found for method {method} in run {run_number}."
                )
            self.anomalies[run_number] = filtered_df.reset_index(drop=True)
        if anomaly_desc is not None:
            filtered_df = anomaly_df[anomaly_df["anomaly_desc"] != anomaly_desc]
            if len(filtered_df) == len(anomaly_df):
                raise ValueError(
                    f"No entries found for anomaly_desc {anomaly_desc} in run {run_number}."
                )
            self.anomalies[run_number] = filtered_df.reset_index(drop=True)

    def rmRun(self, run_number: int) -> None:
        """
        Remove a run from the anomaly DataFrame.
        """
        if run_number in self.anomalies:
            del self.anomalies[run_number]
        else:
            raise ValueError(f"Run number {run_number} does not exist in anomalies.")

    def to_json(self, fname: str = "anomalies.json", path: str = ".") -> str:
        """
        Save the anomalies DataFrame to a JSON file.
        """

        anomalies_dict = {
            run_number: df.to_dict(orient="records")
            for run_number, df in self.anomalies.items()
        }

        with open(os.path.join(path, fname), "w") as f:
            json.dump(anomalies_dict, f, indent=4)

    def __str__(self):
        return self.anomalies.__str__()

    def __repr__(self):
        return self.anomalies.__repr__()

    def __len__(self):
        return len(self.anomalies)

    def __getitem__(self, run_number: int) -> pd.DataFrame:
        """
        Get the anomaly DataFrame for a specific run number.
        """
        if run_number in self.anomalies:
            return self.anomalies[run_number]
        else:
            raise KeyError(f"Run number {run_number} does not exist in anomalies.")
