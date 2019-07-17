#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd $DIR/tethysapp/gfs
t
echo $1
python gfsworkflow.py $1
#/home/tethys/apps/gfs
#/opt/tomcat/content/thredds/public/testdata/gfs
# every day at 4am run the workflow
# 0 4 * * * run_the_workflow