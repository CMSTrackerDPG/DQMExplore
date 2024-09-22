import pandas as pd
from cmsdials import Dials
import cmsdials
from cmsdials.auth.bearer import Credentials
from cmsdials.filters import LumisectionHistogram1DFilters, FileIndexFilters, RunFilters, LumisectionHistogram2DFilters
creds = Credentials.from_creds_file()
dials = Dials(creds)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display
import plotly.express as px
import plotly.graph_objects as go
import math
from statistics import mean
from statistics import stdev
import plotly.io as pio
import os
import json

with open("../clientid.json", "r") as file:
    secrets = json.load(file)

os.environ["API_CLIENT_ID"] = secrets["API_CLIENT_ID"]
os.environ["API_CLIENT_SECRET"] = secrets["API_CLIENT_SECRET"]

import oms
oms_fetch = oms.oms_fetch()

if not os.path.exists("plots"):
    os.mkdir("plots")

def data_1d_me(run_number, me, regex):
    """
    Filters data by parameters below, sorts by ls_number, and converts it into numpy arrays
    
    Parameters:
    run_number, me, regex
    
    Returns:
    data, ls, x_min, x_max, x_bin, y_min, y_max
    """
    
    #do we want to keep saving runs? I am doing it to save time when testing things
    if not os.path.exists("saved_runs"):
        os.mkdir("saved_runs")
    file_name = f'saved_runs/{me.replace("/", "_")}_{run_number}.pkl'
    if os.path.exists(file_name):
        sorted_df = pd.read_pickle(file_name)


    else:
        data = dials.h1d.list_all(
            LumisectionHistogram1DFilters(
                run_number=run_number,
                dataset__regex=regex,
                me=me,
            )
        )
        df = pd.DataFrame([x.__dict__ for x in data.results])
        sorted_df = df.sort_values(by='ls_number')

        sorted_df.to_pickle(file_name)


    ls = sorted_df['ls_number']
    histbins = sorted_df["data"].to_numpy(dtype=np.ndarray)
    histbins = np.array([np.array(x) for x in histbins])

    x_min = sorted_df["x_min"][0]
    x_max = sorted_df["x_max"][0]
    x_bin = sorted_df["x_bin"][0]
    y_min = histbins.min()
    y_max = histbins.max()

    return histbins, ls, x_min, x_max, x_bin, y_min, y_max

def calc_peak(histbins):
    """
    Find the maximum height of the histogram 
    """
    peak = max(np.max(np.histogram(hist)[1]) for hist in histbins)
    
    return peak

def plot_1d_me(histbins, histbins_ref, me_name, run_number, ref_run, x_min, x_max, x_bin, write=False):
    """
    Plot the 1D ME , with a dropdown menu to switch between current and ref run
    
    Parameters:
    histbins: data array for current run
    histbins_ref: data array for ref run
    run_number: current run
    ref_run: reference run
    write: Boolean (choose to save the plot to an html file or not)
    
    Returns:
    plots figure
    writes it to an html file if write=True
    """
    
    max_peak = max(calc_peak(histbins), calc_peak(histbins_ref))

    # Create initial figure
    fig = go.Figure()

    # Add initial traces
    fig.add_trace(go.Bar(
        x=np.linspace(x_min, x_max, int(x_bin)),
        y=histbins[0],
        name='Current Run',
        visible=True
    ))

    fig.add_trace(go.Bar(
        x=np.linspace(x_min, x_max, int(x_bin)),
        y=histbins_ref[0],
        name='Reference Run',
        visible=False
    ))

    # Function to create slider steps
    def create_steps(data):
        steps = []
        for i in range(len(data)):
            step = dict(
                method="update",
                args=[{"y": [data[i]]}],
                label=str(i)
            )
            steps.append(step)
        return steps

    # Create sliders for both datasets
    slider_histbins = [dict(
        active=0,
        currentvalue={"prefix": "LS: "},
        pad={"t": 50},
        steps=create_steps(histbins)
    )]

    slider_histbins_ref = [dict(
        active=0,
        currentvalue={"prefix": "LS: "},
        pad={"t": 50},
        steps=create_steps(histbins_ref)
    )]


    y_axis_range = [0, max_peak]


    # Initial slider configuration
    fig.update_layout(
        sliders=slider_histbins,
        title=me_name,
        xaxis_title=me_name.split('/')[-1],
        yaxis_title='',
        yaxis_range=y_axis_range
    )

    # Add dropdown to switch between Current Run and Reference Run
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=list([
                    dict(
                        args=[{'visible': [True, False]}, {'sliders': slider_histbins}],
                        label="Current Run "+str(run_number),
                        method="update"
                    ),
                    dict(
                        args=[{'visible': [False, True]}, {'sliders': slider_histbins_ref}],
                        label="Reference Run "+str(ref_run),
                        method="update"
                    )
                ]),
                direction="down",
                showactive=True,
            ),
        ]
    )

    fig.show()
    
    if write:
        html_content = pio.to_html(fig, include_plotlyjs='cdn')

        # Write the HTML content to a file
        name_hist = 'plots/'+str(run_number)+'_'+me_name.split('/')[-1]+'.html' 
        with open(name_hist, 'w') as f:
            f.write(html_content)


def plot_1d_me_ref_overlay(histbins, histbins_ref, me_name, run_number, ref_run, x_min, x_max, x_bin, write=False):
    """
    Plot the 1D ME with averaged ref run overlayed
    
    Parameters:
    histbins: data array for current run
    histbins_ref: data array for ref run
    run_number: current run
    ref_run: reference run
    write: Boolean (choose to save the plot to an html file or not)
    
    Returns:
    plots figure
    writes it to an html file if write=True
    """
    
    max_peak = max(calc_peak(histbins), calc_peak(histbins_ref))

    #calculate average of the ref:
    avg_histbins_ref = np.mean(histbins_ref, axis=0)
    
    # Create initial figure
    fig = go.Figure()

    # Add initial traces
    fig.add_trace(go.Bar(
        x=np.linspace(x_min, x_max, int(x_bin)),
        y=histbins[0],
        name='Current Run'+str(run_number),
        visible=True
    ))

    # Add reference trace
    fig.add_trace(go.Scatter(
        x=np.linspace(x_min, x_max, int(x_bin)),
        y=avg_histbins_ref,
        name='Averaged Reference Run'+str(ref_run),
        visible=True,
        line=dict(color='red', width=1)  
    ))

    # Function to create slider steps
    def create_steps(data):
        steps = []
        for i in range(len(data)):
            step = dict(
                method="update",
                args=[{"y": [data[i], avg_histbins_ref]}],
                label=str(i)
            )
            steps.append(step)
        return steps

    # Create sliders for current dataset
    slider_histbins = [dict(
        active=0,
        currentvalue={"prefix": "LS: "},
        pad={"t": 50},
        steps=create_steps(histbins)
    )]


    y_axis_range = [0, max_peak]


    # Initial slider configuration
    fig.update_layout(
        sliders=slider_histbins,
        title=me_name,
        xaxis_title=me_name.split('/')[-1],
        yaxis_title='',
        yaxis_range=y_axis_range
    )

    #overlay ref
    

    fig.show()
    
    if write:
        html_content = pio.to_html(fig, include_plotlyjs='cdn')

        # Write the HTML content to a file
        name_hist = 'plots/'+str(run_number)+'_'+me_name.split('/')[-1]+'_overlay.html' 
        with open(name_hist, 'w') as f:
            f.write(html_content)

def plot_1d_me_normTrig(histbins, histbins_ref, trigger_rate, trigger_rate_ref, me_name, run_number, ref_run, x_min, x_max, x_bin, write=False):
    """
    Plot the 1D ME , with a dropdown menu to switch between current and ref run
    Normalised with trigger rate
    
    Parameters:
    histbins: data array for current run
    histbins_ref: data array for ref run
    run_number: current run
    ref_run: reference run
    write: Boolean (choose to save the plot to an html file or not)
    
    Returns:
    plots figure
    writes it to an html file if write=True
    """
    
    histbins_norm = [np.array(hist)/rate for hist, rate in zip(histbins, trigger_rate)]
    histbins_norm_ref = [np.array(hist)/rate for hist, rate in zip(histbins_ref, trigger_rate_ref)]
    
    #histbins_norm = [remove_infinities(hist) for hist in histbins_norm]
    #histbins_norm_ref = [remove_infinities(hist) for hist in histbins_norm_ref]
    
    
    #max_peak = max(calc_peak(histbins_norm), calc_peak(histbins_norm_ref))
    #print(max_peak)
    max_peak = 1000  #need a way to calculate this 
    
    # Create initial figure
    fig = go.Figure()
    
    # Add initial traces
    fig.add_trace(go.Bar(
        x=np.linspace(x_min, x_max, int(x_bin)),
        y=histbins_norm[0],
        name='Current Run',
        visible=True
    ))
    
    fig.add_trace(go.Bar(
        x=np.linspace(x_min, x_max, int(x_bin)),
        y=histbins_norm_ref[0],
        name='Reference Run',
        visible=False
    ))

    # Function to create slider steps
    def create_steps(data):
        steps = []
        for i in range(len(data)):
            step = dict(
                method="update",
                args=[{"y": [data[i]]}],
                label=str(i)
            )
            steps.append(step)
        return steps

    # Create sliders for both datasets
    slider_histbins = [dict(
        active=0,
        currentvalue={"prefix": "LS: "},
        pad={"t": 50},
        steps=create_steps(histbins_norm)
    )]

    slider_histbins_ref = [dict(
        active=0,
        currentvalue={"prefix": "LS: "},
        pad={"t": 50},
        steps=create_steps(histbins_norm_ref)
    )]


    y_axis_range = [0, max_peak]


    # Initial slider configuration
    fig.update_layout(
        sliders=slider_histbins,
        title=me_name,
        xaxis_title=me_name.split('/')[-1],
        yaxis_title='',
        yaxis_range=y_axis_range
    )

    # Add dropdown to switch between Current Run and Reference Run
    fig.update_layout(
        updatemenus=[
            dict(
                buttons=list([
                    dict(
                        args=[{'visible': [True, False]}, {'sliders': slider_histbins}],
                        label="Current Run "+str(run_number),
                        method="update"
                    ),
                    dict(
                        args=[{'visible': [False, True]}, {'sliders': slider_histbins_ref}],
                        label="Reference Run "+str(ref_run),
                        method="update"
                    )
                ]),
                direction="down",
                showactive=True,
            ),
        ]
    )

    fig.show()
    
    if write:
        html_content = pio.to_html(fig, include_plotlyjs='cdn')

        # Write the HTML content to a file
        name_hist = 'plots/'+str(run_number)+'_'+me_name.split('/')[-1]+'_normTrig.html' 
        with open(name_hist, 'w') as f:
            f.write(html_content)

def plot_1d_me_normTrig_ref_overlay(histbins, histbins_ref, trigger_rate, trigger_rate_ref, me_name, run_number, ref_run, x_min, x_max, x_bin, write=False):
    """
    Plot the 1D ME , normalised by trigger rate
    
    Parameters:
    histbins: data array for current run
    histbins_ref: data array for ref run
    run_number: current run
    ref_run: reference run
    write: Boolean (choose to save the plot to an html file or not)
    
    Returns:
    plots figure
    writes it to an html file if write=True
    """
    
    histbins_norm = [np.array(hist)/rate for hist, rate in zip(histbins, trigger_rate)]
    histbins_norm_ref = [np.array(hist)/rate for hist, rate in zip(histbins_ref, trigger_rate_ref)]
    
    #histbins_norm = [remove_infinities(hist) for hist in histbins_norm]
    #histbins_norm_ref = [remove_infinities(hist) for hist in histbins_norm_ref]
    
    #calculate average of the normalised ref:
    avg_histbins_ref = np.mean(histbins_norm_ref, axis=0)
    
    
    #max_peak = max(calc_peak(histbins_norm), calc_peak(histbins_norm_ref))
    #print(max_peak)
    max_peak = 1000 #need a way to calculate this
    
    # Create initial figure
    fig = go.Figure()
    
    # Add initial traces
    fig.add_trace(go.Bar(
        x=np.linspace(x_min, x_max, int(x_bin)),
        y=histbins_norm[0],
        name='Current Run'+str(run_number),
        visible=True
    ))
    
    # Add reference trace
    fig.add_trace(go.Scatter(
        x=np.linspace(x_min, x_max, int(x_bin)),
        y=avg_histbins_ref,
        name='Averaged Reference Run'+str(ref_run),
        visible=True,
        line=dict(color='red', width=1)  
    ))

    # Function to create slider steps
    def create_steps(data):
        steps = []
        for i in range(len(data)):
            step = dict(
                method="update",
                args=[{"y": [data[i], avg_histbins_ref]}],
                label=str(i)
            )
            steps.append(step)
        return steps

    # Create sliders for both datasets
    slider_histbins = [dict(
        active=0,
        currentvalue={"prefix": "LS: "},
        pad={"t": 50},
        steps=create_steps(histbins_norm)
    )]


    y_axis_range = [0, max_peak]


    # Initial slider configuration
    fig.update_layout(
        sliders=slider_histbins,
        title=me_name+', Run '+str(run_number)+', Ref: '+str(ref_run),
        xaxis_title=me_name.split('/')[-1],
        yaxis_title='',
        yaxis_range=y_axis_range
    )


    fig.show()
    
    if write:
        html_content = pio.to_html(fig, include_plotlyjs='cdn')

        # Write the HTML content to a file
        name_hist = 'plots/'+str(run_number)+'_'+me_name.split('/')[-1]+'_normTrig_overlay.html' 
        with open(name_hist, 'w') as f:
            f.write(html_content)
            
def plot_1d_me_normTrig_ref_overlay_approval(histbins, histbins_ref, trigger_rate, trigger_rate_ref, me_name, run_number, ref_run, x_min, x_max, x_bin, write=False):
    """
    Plot the 1D ME , normalised by trigger rate, with better labels
    
    Parameters:
    histbins: data array for current run
    histbins_ref: data array for ref run
    run_number: current run
    ref_run: reference run
    write: Boolean (choose to save the plot to an html file or not)
    
    Returns:
    plots figure
    writes it to an html file if write=True
    """
    
    histbins_norm = [np.array(hist)/rate for hist, rate in zip(histbins, trigger_rate)]
    histbins_norm_ref = [np.array(hist)/rate for hist, rate in zip(histbins_ref, trigger_rate_ref)]
    
    #histbins_norm = [remove_infinities(hist) for hist in histbins_norm]
    #histbins_norm_ref = [remove_infinities(hist) for hist in histbins_norm_ref]
    
    #calculate average of the normalised ref:
    avg_histbins_ref = np.mean(histbins_norm_ref, axis=0)
    
    
    #max_peak = max(calc_peak(histbins_norm), calc_peak(histbins_norm_ref))
    #print(max_peak)
    max_peak = 700 #need a way to calculate this
    
    # Create initial figure
    fig = go.Figure()
    font_size=24
    
    # Add initial traces
    fig.add_trace(go.Bar(
        x=np.linspace(x_min, x_max, int(x_bin)),
        y=histbins_norm[0],
        name='Current Run',
        visible=True
    ))
    
    # Add reference trace
    fig.add_trace(go.Scatter(
        x=np.linspace(x_min, x_max, int(x_bin)),
        y=avg_histbins_ref,
        name='Averaged Reference Run '+ str(ref_run),
        visible=True,
        line=dict(color='black', width=1)  
    ))

    # Function to create slider steps
    def create_steps(data):
        steps = []
        for i in range(len(data)):
            step = dict(
                method="update",
                args=[{"y": [data[i], avg_histbins_ref]}],
                label=str(i)
            )
            steps.append(step)
        return steps

    # Create sliders for both datasets
    slider_histbins = [dict(
        active=0,
        currentvalue={"prefix": "LS: "},
        pad={"t": 50},
        steps=create_steps(histbins_norm)
    )]


    y_axis_range = [0, max_peak]


    # Initial slider configuration
    fig.update_layout(
        sliders=slider_histbins,
        #title='On-Track Cluster Charge (Normalized)',
        xaxis_title='On-Track Cluster Charge (electrons)',
        yaxis_title='A.U.',
        yaxis_range=y_axis_range,

        #for styling
        legend=dict(
            x=0.94,  # X coordinate of the legend (from 0 to 1)
            y=0.98,  # Y coordinate of the legend (from 0 to 1)
            xanchor='right',  # Horizontal anchor point of the legend
            yanchor='top',   # Vertical anchor point of the legend
            font=dict(
                size=font_size+8
            ),
        ),

        annotations=[
            dict(
                x=0,
                y=1.09,
                xref='paper',
                yref='paper',
                text='<b>CMS</b> <i>Preliminary</i>',
                showarrow=False,
                font=dict(size=font_size+10)
            ),
            dict(
                x=1,
                y=1.09,
                xref='paper',
                yref='paper',
                text='2024 (13.6 TeV)',
                showarrow=False,
                font=dict(size=font_size+10)
            ),
            dict(
                x=0.72,
                y=0.6,
                xref='paper',
                yref='paper',
                text='BPIX L'+str(me_name[-1]),
                showarrow=False,
                font=dict(size=font_size+8)
            )
        ],
        xaxis=dict(
            #tickvals=tickvals,
            #ticktext=ticktext,
            title_font=dict(size=font_size+4),   # Adjust the font size for x-axis title
            gridcolor='lightgray'
        ),
        yaxis=dict(
            title_font=dict(size=font_size+4),  # Adjust the font size for y-axis title
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',  
        paper_bgcolor='white',
        width=1400,
        height=800
    )
    
    fig.update_xaxes(showline=True, mirror=True, linewidth=2, linecolor='black')
    fig.update_yaxes(showline=True, mirror=True, linewidth=2, linecolor='black')

    #end styling

    fig.show()
    
    if write:
        html_content = f"""
        <div style="text-align: left; font-size: 18px; width: 1400px; margin: auto;">
            {pio.to_html(fig, include_plotlyjs='cdn')}
        </div>
        """

        # Write the HTML content to a file
        name_hist = '/eos/user/s/sharmari/public/DIALS_Plots/approval/'+str(run_number)+'_'+me_name.split('/')[-1]+'.html' 
        with open(name_hist, 'w') as f:
            f.write(html_content)
            
def plot_rate(hist, hist_ref, run_number, ref_run, x_axis, y_axis, title, me_name, write=False):
    
    plot = go.Figure()
    custom_ticks = [x+1 for x in range(len(hist))]
    custom_ticks_ref = [x+1 for x in range(len(hist_ref))]

    plot.add_trace(go.Scatter(
        x = list(range(len(hist))),
        y = hist,
        visible=True
    ))

    plot.add_trace(go.Scatter(
        x = list(range(len(hist_ref))),
        y = hist_ref,
        visible=False
    ))

    tickvals, ticktext = get_x_labels(custom_ticks)
    tickvals_ref, ticktext_ref = get_x_labels(custom_ticks_ref)

    # Add dropdown
    plot.update_layout(
        
        title=title,
        xaxis_title=x_axis,
        yaxis_title=y_axis,
        xaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext
        ),
        updatemenus=[
            dict(
                buttons=list([
                    dict(
                        args=[{'visible':[True, False]},
                             {'xaxis': {
                                 'tickvals': tickvals,
                                 'ticktext': ticktext,
                                 'title_text': x_axis
                              }}
                             ],
                        label="Current Run "+ str(run_number),
                        method="update"
                    ),
                    dict(
                        args=[{'visible':[False, True]},
                             {'xaxis': {
                                'tickvals': tickvals_ref,
                                'ticktext': ticktext_ref,
                                'title_text': x_axis
                             }}
                             ],
                        label="Reference Run "+ str(ref_run),
                        method="update"
                    )
                ]),
                direction="down",
            ),
        ]
    )

    plot.show()
    
    if write:
        html_content = pio.to_html(plot, include_plotlyjs='cdn')

        # Write the HTML content to a file
        #name_hist = 'plots/'+str(run_number)+'_'+me_name.split('/')[-1]+'_'+title+'.html' 
        name_hist = 'plots/'+str(run_number)+title+'.html' 
        with open(name_hist, 'w') as f:
            f.write(html_content)
        #pio.write_html(fig, name_hist)
        
def get_oms_info(run_number):
    """
    Get trigger rate from OMS as a df and convert it to numpy array
    
    Parameters:
    run_number
    
    Returns:
    trigger_rate: ZeroBias trigger rate
    """
    extrafilter = dict(
        attribute_name="dataset_name",
        value="ZeroBias",
        operator="EQ",
    )

    attributes = [
        'start_time', 
        'last_lumisection_number', 
        'rate', 
        'run_number',
        'last_lumisection_in_run', 
        'first_lumisection_number', 
        'dataset_name',
        'cms_active', 
        'events'
    ]

    omstrigger_json = oms.get_oms_data(
        oms_fetch.omsapi, 
        'datasetrates', 
        run_number,
        extrafilters=[extrafilter],
        limit_entries = 4000
    )

    omstrigger_df = oms.oms_utils.makeDF(omstrigger_json)
    trigger_rate = np.array(omstrigger_df["rate"])

    return trigger_rate


def calc_trends(histbins, ls, max_value, trigger_rate, norm = False):
    """
    Calculates ~peak value, std error on mean, and list of empty LS.
    Also normalises by trigger rate if norm=True
    
    Parameters:
    histbins: data in the form of numpy array
    ls: list of lumisections
    max_value: maximum value of the quantity being measured along x-axis
    trigger_rate: np array obtained from oms
    norm: Boolean (default False)
    
    Returns:
    list_means: position of peak. It's not precise because the distributions are not Gaussian
    list_std: standard error on mean
    list_good_ls: non-zero LS
    empty_ls: 
    """
    list_means = [] #peak
    list_std= []
    list_good_ls = []
    empty_ls = []
    good_trigger = []
    for i in range(len(histbins)):
        ls_num = ls[i]
        # Calculate Mean and Std Error on Mean
        
        if any(histbins[i]):
            n_bins = len(histbins[i])
            actual_values = np.linspace(0, max_value, n_bins, endpoint=True) 
            
            peak_value = np.average(actual_values, weights=histbins[i]) #needs modification to get actual peak?? Fit a Landau/Langaus and get the MPV
            std_dev = stdev(histbins[i])
            sem = std_dev / np.sqrt(n_bins) # standard error on mean = (standard deviation)/sqrt(n)
            
            list_good_ls.append(ls_num)
            list_means.append(peak_value)
            list_std.append(sem) 
            good_trigger.append(trigger_rate[i])
        else:
            peak_value =0
            std_dev = 0
            empty_ls.append(ls_num)
        
    if norm:
        
        list_means = np.divide(list_means, good_trigger)
        list_std = np.divide(list_std, good_trigger) 
        

    return list_means, list_std, list_good_ls, empty_ls

def plot_trends(list_raw, list_norm, list_good_ls, title, x_axis, me_name, run_number, write=False):

    plot = go.Figure()
    custom_ticks = [x for x in list_good_ls]
    plot.add_trace(go.Scatter(
        x = list(range(len(list_raw))),
        y = list_raw,
        visible=True
    ))

    plot.add_trace(go.Scatter(
        x = list(range(len(list_norm))),
        y = list_norm,
        visible=False
    ))

    tickvals, ticktext = get_x_labels(custom_ticks)

    # Add dropdown
    plot.update_layout(
        title=title+", "+me_name+", Run: "+str(run_number),
        xaxis_title='LS',
        xaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext
        ),
        updatemenus=[
            dict(
                buttons=list([
                    dict(
                        args=[{'visible':[True, False]},
                             {'xaxis': {
                                'tickvals': tickvals,
                                'ticktext': ticktext,
                                'title_text': x_axis
                             }}
                             ],
                        label="Raw",
                        method="restyle"
                    ),
                    dict(
                        args=[{'visible':[False, True]},
                             {'xaxis': {
                                'tickvals': tickvals,
                                'ticktext': ticktext,
                                'title_text': x_axis
                             }}
                             ],
                        label="Normalised",
                        method="restyle"
                    )
                ]),
                direction="down",
            ),
        ]
    )
    
    plot.show()
    
    if write:
        html_content = pio.to_html(plot, include_plotlyjs='cdn')

        # Write the HTML content to a file
        name_hist = 'plots/'+str(run_number)+'_'+me_name.split('/')[-1]+'_'+title+'.html' 
        print('Writing:',name_hist)
        with open(name_hist, 'w') as f:
            f.write(html_content)
        #pio.write_html(fig, name_hist)
        
def plot_trends_approval(list_raw, list_norm, list_good_ls, title, x_axis, me_name, run_number, write=False):

    plot = go.Figure()
    font_size=24
    custom_ticks = [x for x in list_good_ls]
    plot.add_trace(go.Scatter(
        x = list(range(len(list_raw))),
        y = list_raw,
        visible=True
    ))

    tickvals, ticktext = get_x_labels(custom_ticks)

    # Add text to display, no dropdown
    plot.update_layout(
        #title=title+", "+me_name+", Run: "+str(run_number),
        annotations=[
            dict(
                x=0,
                y=1.08,
                xref='paper',
                yref='paper',
                text='<b>CMS</b> <i>Preliminary</i>',
                showarrow=False,
                font=dict(size=font_size+10)
            ),
            dict(
                x=1,
                y=1.08,
                xref='paper',
                yref='paper',
                text='2024 (13.6 TeV)',
                showarrow=False,
                font=dict(size=font_size+10)
            ),
            dict(
                x=0.9,
                y=0.55,
                xref='paper',
                yref='paper',
                text='BPIX L'+str(me_name[-1]),
                showarrow=False,
                font=dict(size=font_size+10)
            )
        ],
        xaxis_title='Lumisection',
        yaxis_title='Mean Value of On-Track Cluster Charge',
        xaxis=dict(
            tickvals=tickvals,
            ticktext=ticktext,
            title_font=dict(size=font_size+4)
        ),
        yaxis=dict(
            title_font=dict(size=font_size+4),  # Adjust the font size for y-axis title
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',  
        paper_bgcolor = 'white',
        width=1400,  
        height=800,  
    )
    
    plot.update_xaxes(showline=True, mirror=True, linewidth=2, linecolor='black')
    plot.update_yaxes(showline=True, mirror=True, linewidth=2, linecolor='black')

    plot.show()

    if write:
        if not os.path.exists("png_plots"):
            os.mkdir("png_plots")
    
        #plot.write_image("png_plots/"+str(run_number)+'_'+me_name.split('/')[-1]+'_'+title+'_approval.png')

        html_content = f"""
        <div style="text-align: left; font-size: 18px; width: 1400px; margin: auto;">
            {pio.to_html(plot, include_plotlyjs='cdn')}

        </div>
        """

        # Write the HTML content to a file
        #name_hist = '/eos/user/s/sharmari/public/DIALS_Plots/approval/'+str(run_number)+'_'+me_name.split('/')[-1]+'_'+title+'.html' 
        name_hist = 'plots/'+str(run_number)+'_'+me_name.split('/')[-1]+'_'+title+'.html' 
        print('Writing:',name_hist)
        with open(name_hist, 'w') as f:
            f.write(html_content)
        #pio.write_html(fig, name_hist)
        
def get_x_labels(custom_ticks):
    """
    Print a maximum of 40 x-labels in the rate plot. 
    
    Parameters: custom_ticks
    Returns: tickvals, ticktext
    """
    
    interval = max(1, len(custom_ticks) // 40)
    tickvals = list(range(0, len(custom_ticks), interval))
    ticktext = [custom_ticks[i] for i in tickvals]
    
    return tickvals, ticktext

