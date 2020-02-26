import string
import random
from .app import Gfs as App
import os
import datetime


def get_gfsdate():
    thredds = App.get_custom_setting("thredds_path")
    file = os.path.join(thredds, 'last_run.txt')
    if os.path.exists(file):
        with open(os.path.join(thredds, 'last_run.txt'), 'r') as file:
            return file.read()
    else:
        return 'none'


def currentgfs():
    # if there is actually data in the app, then read the file with the timestamp on it
    thredds = App.get_custom_setting("thredds_path")
    timestamp = get_gfsdate()
    path = os.path.join(thredds, timestamp)
    if os.path.exists(path):
        timestamp = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
        return "This GFS data from " + timestamp.strftime("%b %d, %I%p UTC")
    return "No GFS data detected"


def new_id(length=10):
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for i in range(length))
