# DQMExplore

This repository hosts `dqmexplore`, a Python software toolkit aimed at facilitating the exploration of CMS DQM data for shifters, shift leaders, and experts. These tools enable the programmatic evaluation of runs at the per-lumisection level by allowing users to make interactive plots of 1D and 2D monitoring elements, as well as trends, using data obtained from the [DIALS Python API](https://github.com/cms-DQM/dials-py). In addition, it provides scripts to facilitate the use of data from sources such as OMS, Run Registry, and CertHelper.

## Setup

The tools provided by `dqmexplore` can be utilized either by installing it as a Python package by running

```
pip3 install git+https://github.com/CMSTrackerDPG/DQMExplore.git
```

or by cloning the repository, adding the `src/` directory to the system path and importing the `dqmexplore` package. Alternatively, you can use the provided setup script by following the instructions below.

### LXPLUS

Connect to the cluster by running:

```bash
ssh -Y rcruzcan@lxplus.cern.ch -L localhost:8080:localhost:8080
```

To run the setup script, execute the following commands:

```bash
wget https://raw.githubusercontent.com/CMSTrackerDPG/DQMExplore/main/setup.sh
chmod +x setup.sh
./setup.sh
```

This script will create a working directory named `DQME`, clone the repository, and install all dependencies into a Python virtual environment. Note that the setup script will prompt you for your CERN SSO client ID  and secret (instructions on how to obtain these are linked in [Relevant Documentation](#relevant-documentation)). This is only necessary if you wish to use the included scripts that fetch data from Run Registry (e.g. [`fetch_golden.py`](src/scripts/fetch_golden.py)). Otherwise, you may press Enter for both prompts and it will generate a template .env file which you can configure later if needed.

## Accessing & Plotting Data

### Notebooks

A number of [notebooks](notebooks/) are included with template workflows for interactive exploration of Tracker monitoring elements. To use any of the notebooks, run:

```
jupyter notebook --no-browser --port=8080
```

and open the provided link in your favorite browser.

### Scripts

Various scripts are located in the [scripts](scripts/) and [src/scripts](src/scripts/) directories. If you are in a virtual environment with `dqmexplore` installed, you can run the scripts in the latter directory directly as commands. For instance, to generate a user-defined golden json using a configuration file `configs/rr_config.json`, run:

```
fetch_golden -l configs/rr_config.json
```

### Using in Your Code

To integrate the tools provided in this repository into your own code, you can install `dqmexplore` into your virtual environment by running:

```python
pip3 install
```

and import it directly. Alternatively, you can append the source directory to your path link so:

```python
import sys
sys.path.append("path/to/dqme/root/dir/src")
import dqmexplore as dqme
```

## Relevant Documentation & Resources

* [CERN SSO registration instructions](https://github.com/CMSTrackerDPG/cernrequests#for-cern-apis-using-the-new-sso)
* [DIALS Python API repository](https://gitlab.cern.ch/cms-dqmdc/libraries/dials-py/-/tree/develop)
* [Run Registry Python API repository](https://gitlab.cern.ch/cms-dqmdc/libraries/runregistry_api_client)
