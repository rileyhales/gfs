#!/usr/bin/env bash

source /home/tethys/tethys/miniconda/etc/profile.d/conda.sh; conda activate tethys
python /home/tethys/apps/gfs/tethysapp/gfs/gfsworkflow.py /opt/tomcat/content/thredds/public/testdata/gfs
# 0 4 * * * bash /home/tethys/apps/gfs/workflow.sh