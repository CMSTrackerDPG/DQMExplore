import json
import argparse
import runregistry

runregistry.setup("production")


def main():
    parser = argparse.ArgumentParser(description="A script to get a Run Registry JSON")
    parser.add_argument(
        "-l", "--logic", type=str, help="Path to json containing RR fetching logic."
    )
    parser.add_argument(
        "-d", "--dataset", type=str, default="/Express/Collisions2024/DQM"
    )
    parser.add_argument(
        "-f",
        "--fname",
        type=str,
        default="./jsons/rr_output.json",
        help="Name and path of output file.",
    )
    parser.add_argument(
        "-m", "--meta", action="store_true", help="Include metadata in the output JSON."
    )
    args = parser.parse_args()

    with open(args.logic) as f:
        json_logic = json.load(f)

    rr_data = runregistry.create_json(
        json_logic=json_logic,
        dataset_name_filter=args.dataset,
    )

    with open(args.fname, "w") as file:
        json.dump(rr_data if args.meta else rr_data["generated_json"], file, indent=4)


if __name__ == "__main__":
    main()
