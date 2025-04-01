from dqmexplore.utils.datautils import loadFromWeb
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="A script to get CertHelper data downloaded into a JSON file"
    )
    parser.add_argument(
        "-f",
        "--fname",
        type=str,
        default="./jsons/ch_refruns.json",
        help="Name and path of output file.",
    )
    args = parser.parse_args()

    print(f"Downloading CH run data and storing it in {args.fname}")
    url = "https://certhelper.web.cern.ch/certify/allRunsRefRuns/"
    loadFromWeb(url, args.fname)


if __name__ == "__main__":
    main()
