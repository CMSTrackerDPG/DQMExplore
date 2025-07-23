import pandas as pd
import os


class Anomaly:
    def __init__(self) -> None:
        self.anomaly_keys: set[str] = [
            "run_number",
            "start_ls",
            "end_ls",
            "anomaly_desc",
        ]
        self.anomalies: dict[int, pd.DataFrame] = {}

    def addMethod(
        self,
        method: str,
        anomalies: list[dict[str, any]] | dict[str, any] | None = None,
    ) -> pd.DataFrame:
        """
        Add a new method to the anomaly dictionary if it does not already exist.
        """
        if method not in self.anomalies:
            self.anomalies[method] = pd.DataFrame(columns=list(self.anomaly_keys))
            if anomalies is not None:
                self.addEntries(
                    method=method,
                    anomalies=anomalies if isinstance(anomalies, list) else [anomalies],
                )
        else:
            raise ValueError("Run number already exists.")
        return self.anomalies[method]

    def addEntry(
        self,
        method: str,
        anomaly: dict[str, any] | None = None,
    ) -> pd.DataFrame | None:
        """
        Add entries to anomaly DataFrame for a given run. If the run does not exist, it will create a new one.
        """

        if method not in self.anomalies:
            self.addMethod(method, anomaly)
            return

        if anomaly is None:
            print(
                f"No anomalies provided for method {method}. Adding empty method entry."
            )
            self.addMethod(method)
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
            self.anomalies[method] = pd.concat(
                [self.anomalies[method], pd.DataFrame([anomaly])], ignore_index=True
            )

        return self.anomalies[method]

    def addEntries(self, method: str, anomalies: list[dict]) -> pd.DataFrame:
        """
        Add multiple entries to the anomaly DataFrame of a particular run.
        Each entry should be a dictionary with keys matching the DataFrame columns.
        """

        for anomaly in anomalies:
            self.addEntry(method, anomaly)

        return self.anomalies[method]

    def rmEntries(
        self,
        method: str,
        run_number: int,
    ) -> None:
        """
        Remove an entry from the anomaly DataFrame based on run_number, method, or anomaly_desc.
        """

        anomaly_df = self.anomalies.get(method, None)
        if anomaly_df is None:
            raise ValueError(f"Method {method} does not exist in anomalies.")

        if run_number is None:
            # Remove all entries for the specified method
            self.anomalies[method] = pd.DataFrame(columns=self.anomaly_keys)
        else:
            # Filter out the entries for the specified run_number
            filtered_df = anomaly_df[anomaly_df["run_number"] != run_number]
            if len(filtered_df) == len(anomaly_df):
                raise ValueError(
                    f"No entries found for run number {run_number} in method {method}."
                )
            self.anomalies[method] = filtered_df.reset_index(drop=True)

    def rmMethod(self, method: str) -> None:
        """
        Remove a run from the anomaly DataFrame.
        """
        if method in self.anomalies:
            del self.anomalies[method]
        else:
            raise ValueError(f"Method {method} does not exist in anomalies.")

    def to_json(self, fname: str = "anomalies.json", path: str = ".") -> str:
        """
        Save the anomalies DataFrame to a JSON file.
        """
        import json

        anomalies_dict = {
            method: df.to_dict(orient="records")
            for method, df in self.anomalies.items()
        }

        with open(os.path.join(path, fname), "w") as f:
            json.dump(anomalies_dict, f, indent=4)

    def __str__(self):
        return self.anomalies.__str__()

    def __repr__(self):
        return self.anomalies.__repr__()

    def __len__(self):
        return len(self.anomalies)

    def __getitem__(self, method: str) -> pd.DataFrame:
        """
        Get the anomaly DataFrame for a specific run number.
        """
        if method in self.anomalies:
            return self.anomalies[method]
        else:
            raise KeyError(f"Method {method} does not exist in anomalies.")
