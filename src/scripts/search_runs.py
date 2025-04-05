from dqmexplore.certhelper import CHRunData
import argparse
import os
from tabulate import tabulate
import warnings


def main():
    parser = argparse.ArgumentParser(
        description="Script to search for runs/reference runs given a set of run numbers"
    )
    parser.add_argument(
        "-r",
        "--runnbs",
        nargs="*",
        type=int,
        required=True,
        help="Run numbers to search for",
    )
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        default="run",
        choices=["run", "ref"],
        help="Search for run numbers or reference run numbers. Default: 'run'",
    )
    parser.add_argument(
        "-f", "--fname", type=str, default="", help="Name and path of output file."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default="./jsons/ch_refruns.json",
        help="Name and path of input file.",
    )
    parser.add_argument("-p", "--print", action="store_false", help="Print the results")
    parser.add_argument(
        "-t",
        "--reco_type",
        type=str,
        choices=["express", "prompt"],
        default="all",
        help="Reconstruction type to filter by. Default: 'all'",
    )
    args = parser.parse_args()

    if not os.path.exists(args.input):
        raise FileNotFoundError(
            f"Input file {args.input} does not exist. Please download the CertHelper data first."
        )

    ch_data = CHRunData(args.input)
    search_results = ch_data.searchRuns(args.runnbs, ref=(args.mode == "ref"))

    if args.reco_type != "all":
        search_results = search_results[
            search_results[
                (
                    "run_reconstruction_type"
                    if args.mode == "run"
                    else "reference_run_reconstruction_type"
                )
            ]
            == args.reco_type
        ]

    if len(args.fname) == 0:
        print("No output file specified. Printing results to console only.")
        print(
            tabulate(search_results, headers="keys", tablefmt="grid", showindex=False)
        )
        return

    if args.print:
        print(
            tabulate(search_results, headers="keys", tablefmt="grid", showindex=False)
        )

    if args.fname.endswith(".json"):
        search_results.to_json(args.fname, orient="records", lines=True)
    elif args.fname.endswith(".csv"):
        search_results.to_csv(args.fname, index=False)
    else:
        raise ValueError("Output file must be either a JSON or CSV file.")
