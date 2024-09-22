#DIALS API
from cmsdials import Dials
import cmsdials
from cmsdials.auth.bearer import Credentials
from cmsdials.filters import LumisectionHistogram1DFilters, FileIndexFilters, RunFilters, LumisectionHistogram2DFilters
creds = Credentials.from_creds_file()
dials = Dials(creds)
##################################
# OMS API
import json
import os

with open("../clientid.json", "r") as file:
    secrets = json.load(file)

os.environ["API_CLIENT_ID"] = secrets["API_CLIENT_ID"]
os.environ["API_CLIENT_SECRET"] = secrets["API_CLIENT_SECRET"]

import oms

oms_fetch = oms.oms_fetch()
###################################
import argparse

import utils
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
import utils
import plotly.express as px
import plotly.graph_objects as go
import math
from statistics import mean
from statistics import stdev
import plotly.io as pio

#%%matplotlib notebook

# Argument Parsing
def parse_arguments():
    parser = argparse.ArgumentParser(description="Script to process and plot 1D MEs")
    parser.add_argument('me_name', type=str, help='ME name')
    parser.add_argument('run_number', type=int, help='Run number')
    parser.add_argument('ref_run', type=int, help='Reference run number')
    return parser.parse_args()

#me_name = "PixelPhase1/Tracks/PXBarrel/charge_PXLayer_1"
#run_number = 380238 
#ref_run = 379765

# Main Function
def main(me_name, run_number, ref_run):

    regex = "StreamExpress"
    print('Current run: ', run_number)
    print('Reference run: ', ref_run)
    data_current, ls, x_min, x_max, x_bin, y_min, y_max = utils.data_1d_me(run_number, me_name, regex)
    print("Loaded current run...")
    data_ref, ls_ref, x_min_ref, x_max_ref, x_bin_ref, y_min_ref, y_max_ref = utils.data_1d_me(ref_run, me_name, regex)
    print("Loaded ref run...")

    utils.plot_1d_me(data_current, data_ref, me_name, run_number, ref_run, x_min, x_max, x_bin, write=True )
    print("Plotted 1D ME......")
    utils.plot_1d_me_ref_overlay(data_current, data_ref, me_name, run_number, ref_run, x_min, x_max, x_bin, write=True )
    print("Plotted 1D ME with ref overlayed......")

    trigger_rate = utils.get_oms_info(run_number)
    trigger_rate_ref = utils.get_oms_info(ref_run)
    print("Got trigger rates....")

    utils.plot_1d_me_normTrig(data_current, data_ref, trigger_rate, trigger_rate_ref, me_name, run_number, ref_run, x_min, x_max, x_bin, write=True )
    print("Plotted 1D ME norm Trig......")
    utils.plot_1d_me_normTrig_ref_overlay(data_current, data_ref, trigger_rate, trigger_rate_ref, me_name, run_number, ref_run, x_min, x_max, x_bin, write=True )
    print("Plotted 1D ME norm Trig with ref overlayed......")
    utils.plot_1d_me_normTrig_ref_overlay_approval(data_current, data_ref, trigger_rate, trigger_rate_ref, me_name, run_number, ref_run, x_min, x_max, x_bin, write=True )

    title = 'TriggerRate'
    y_axis ='Rate: Zero Bias'
    x_axis = 'LS'
    utils.plot_rate(trigger_rate, trigger_rate_ref, run_number, ref_run, x_axis, y_axis, title, me_name, write=True)
    print("Saved plots for trigger rates...")


    # Calculate Mean, Std Error on Mean and empty LS list
    max_value_charge = x_max 
    list_means, list_std, list_good_ls, empty_ls = utils.calc_trends(data_current, ls, max_value_charge, trigger_rate)
    list_means_norm, list_std_norm, list_good_ls, empty_ls = utils.calc_trends(data_current, ls, max_value_charge, trigger_rate, norm=True)
    print("Calculated means std etc....")

    print('Empty LS for Current Run:', empty_ls)

    title='MeanValue'
    x_axis = 'LS'
    utils.plot_trends(list_means, list_means_norm, list_good_ls, title, x_axis, me_name, run_number, write=True)
    print("Plotted means for current run...")
    utils.plot_trends_approval(list_means, list_means_norm, list_good_ls, title, x_axis, me_name, run_number, write=True)
    print("Plotted means for current run for approval...")

    title='Standard_Error_on_Mean'
    utils.plot_trends(list_std, list_std_norm, list_good_ls, title, x_axis, me_name, run_number, write=True)
    print("Plotted standard error on mean...")

    # Calculate Mean, Std Error on Mean and empty LS list for reference run
    max_value_charge = x_max 
    list_means_ref, list_std_ref, list_good_ls_ref, empty_ls_ref = utils.calc_trends(data_ref, ls_ref, max_value_charge, trigger_rate_ref)
    list_means_norm_ref, list_std_norm_ref, list_good_ls_ref, empty_ls_ref = utils.calc_trends(data_ref, ls_ref, max_value_charge, trigger_rate_ref, norm=True)

    title='MeanValue_Reference'
    x_axis = 'LS'
    utils.plot_trends(list_means_ref, list_means_norm_ref, list_good_ls_ref, title, x_axis, me_name, ref_run, write=True)
    print("Saved means trend plot for reference run...")

    title='Standard_Error_on_Mean_Reference'
    x_axis = 'LS'
    utils.plot_trends(list_std_ref, list_std_norm_ref, list_good_ls, title, x_axis, me_name, ref_run, write=True)
    print("Saved Plot for standard error on mean for reference run...")
    
    inf_indices = [index for index, value in enumerate(list_means_norm_ref) if math.isinf(value)]
    print('Indices with inf:', inf_indices)

    print('Means in those bins:')
    print([list_means_ref[i] for i in inf_indices])
        
if __name__ == "__main__":
    args = parse_arguments()
    main(args.me_name, args.run_number, args.ref_run)
