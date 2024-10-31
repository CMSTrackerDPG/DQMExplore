This directory containes scripts that can be run to create 1D ME distributions and trend plots.  

The file utils.py contains the relevant functions. 
You need the clientid.json in the root directory of the repo in order to run the OMS API. The json file contains the client ID (API_CLIENT_ID) and secret (API_CLIENT_SECRET). For more information on how to obtain these, you can take a look at these slides: https://indico.cern.ch/event/997758/contributions/4191705/attachments/2173881/3670409/OMS%20CERN%20OpenID%20migration%20-%20update.pdf

You can either run 
python 1D_ME_Explore.py "ME_Name" <current_run> <ref_run>
to create html plots for one ME at a time, or edit the run_all.py to run the script for more than one ME.

The html files are saved in the plots/ dir if write=True in 1D_ME_Explore.py. This dir will be created if it doesn't already exist.
