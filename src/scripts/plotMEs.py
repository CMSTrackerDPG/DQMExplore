import dqmexplore as dqme
import argparse
import json


def main():
    parser = argparse.ArgumentParser(description="A script to get a Run Registry JSON")
    parser.add_argument(
        "-p", "--plot_config", type=str, help="Path to the plot configuration file."
    )
    parser.add_argument(
        "-f", "--fig_config", type=str, help="Path to the figure configuration file."
    )
    parser.add_argument("-r", "--runnb", type=int, help="Run number to plot.")
    parser.add_argument(
        "-e",
        "--ref_runnb",
        type=int,
        default=0,
        help="Reference run number for comparison.",
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Output file name for the plot."
    )
    args = parser.parse_args()

    with open(args.plot_config) as f:
        plot_config = json.load(f)

    trig_rate = None
    for val in plot_config.values():
        if val.get("norm", None) == "trignorm":
            trig_rate = dqme.oms.get_rate(args.runnb)
            break

    me_names = list(plot_config.keys())
    print("[NOTE] MEs to plot:")
    for me_name in me_names:
        print(f"  - {me_name}")

    print("[NOTE] Fetching data from CMS Dials...")
    query_rslt = dqme.utils.datautils.fetch_data(args.runnb, me_names)
    data = dqme.medata.MEData(query_rslt)

    if args.ref_runnb != 0:
        ref_query_rslt = dqme.utils.datautils.fetch_data(args.ref_runnb, me_names)
        ref_data = dqme.medata.MEData(ref_query_rslt)

    print("[NOTE] Plotting data...")
    fig = dqme.interplt.plotMEs(
        data,
        plots_config=args.plot_config,
        figure_config=args.fig_config,
        ref_data=ref_data if args.ref_runnb != 0 else None,
        trigger_rates=trig_rate,
        show=False,
    )

    print("[NOTE] Saving plot to HTML file...")
    fig.write_html(args.output)


if __name__ == "__main__":
    main()
