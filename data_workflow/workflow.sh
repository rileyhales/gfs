#!/usr/bin/env bash
# activate the python environment containing the dependencies to run the workflow
source /home/tethys/tethys/miniconda/etc/profile.d/conda.sh; conda activate tethys
# exectue the workflow using the path to the gfsworkflow.py file and the path to save the data
python /home/tethys/apps/gfs/tethysapp/gfs/gfsworkflow.py /opt/tomcat/content/thredds/public/testdata/gfs
# then run this command from crontab with a command like:
# 0 4 * * * bash /home/tethys/apps/gfs/workflow.sh