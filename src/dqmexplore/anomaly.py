import pandas as pd


class Anomaly:
    def __init__(self) -> None:
        """
        anomalydf will only contain rows (indexed by run_number and ls) which correspond to lss which were found to be anomalous
        "method" refers to the ml model or analytical method that was used to determine its anomalous state
        There can be multiple entries for the same lumisection and even the same model
        """
        self.anomalydf = pd.DataFrame(
            {"run_number": [], "ls": [], "method": [], "anomaly": []}
        )
        self.anomalydf.set_index(["run_number", "ls"], inplace=True)

    def addEntry(self, anomalylog: dict[str, int | str]):
        pass  # basically adds rows to anomalydf

    def getEntry(self, runnb=None, ls=None):
        pass
