"""
Author: Riley Hales, 2018
Copyright: Riley Hales, RCH Engineering, 2019
Description: Functions for generating timeseries and simple statistical
    charts for netCDF data for point, bounding box, or shapefile geometries
"""
import os
import glob
import json

import netCDF4 as nc
import geomatics as gm

from .options import gfs_variables
from .utilities import get_gfsdate
from .app import Gfs as App


def newchart(data):
    """
    Determines the environment for generating a timeseries chart. Call this function
    """
    # response metadata items
    meta = {
        'variable': data['variable'],
        'loc_type': data['loc_type']
    }
    for item in gfs_variables():
        if item[1] == data['variable']:
            meta['name'] = item[0]
            break

    user_workspace = os.path.join(os.path.dirname(__file__), 'workspaces', 'user_workspaces', data['instance_id'])
    date_pattern = data['level'] + '_%Y%m%d%H.nc'

    # list the netcdfs to be processed
    path = App.get_custom_setting('thredds_path')
    timestamp = get_gfsdate()
    path = os.path.join(path, timestamp, 'netcdfs')
    files = [n for n in os.listdir(path) if n.startswith(data['level']) and n.endswith('.nc')]
    files = [os.path.join(path, file) for file in files]
    files.sort()

    meta['units'] = nc.Dataset(files[0], 'r')[data['variable']].__dict__['units']

    # get the timeseries, units, and message based on location type
    if data['loc_type'] == 'Point':
        timeseries = gm.netcdfs.point_series(files, data['variable'], data['coords'], date_pattern)
        meta['seriesmsg'] = 'At a Point'

    elif data['loc_type'] == 'Polygon':
        coords = data['coords'][0]
        coords = (
            float(coords[0][0]),
            float(coords[0][1]),
            float(coords[2][0]),
            float(coords[2][1]),
        )
        timeseries = gm.netcdfs.box_series(files, data['variable'], coords, date_pattern)
        meta['seriesmsg'] = 'In a Bounding Box'

    elif data['loc_type'] == 'Shapefile':
        shp = [i for i in os.listdir(user_workspace) if i.endswith('.shp')]
        shp = shp.remove('usergj.shp')
        shp = os.path.join(shp[0])
        timeseries = gm.netcdfs.shp_series(files, data['variable'], shp, date_pattern)
        meta['seriesmsg'] = 'In User\'s Shapefile'

    elif data['loc_type'] == 'GeoJSON':
        shp = os.path.join(user_workspace, '__tempgj.shp')
        with open(os.path.join(user_workspace, 'usergj.geojson')) as f:
            gm.geojsons.geojson_to_shp(json.loads(f.read()), shp)
        timeseries = gm.netcdfs.shp_series(files, data['variable'], shp, date_pattern)
        for file in glob.glob(os.path.join(user_workspace, '__tempgj.*')):
            os.remove(file)
        meta['seriesmsg'] = 'In User\'s GeoJSON'

    elif data['loc_type'].startswith('esri-'):
        esri_location = data['loc_type'].replace('esri-', '')
        geojson = gm.geojsons.request_livingatlas_geojson(esri_location)
        shp = os.path.join(user_workspace, '___esri.shp')
        gm.geojsons.geojson_to_shp(geojson, shp)
        timeseries = gm.netcdfs.shp_series(files, data['variable'], shp, date_pattern)
        for file in glob.glob(os.path.join(user_workspace, '___esri.*')):
            os.remove(file)
        meta['seriesmsg'] = 'Within ' + esri_location

    dates = timeseries.index.strftime('%Y-%m-%d %H')
    dates = dates.tolist()

    return {
        'meta': meta,
        'timeseries': list(zip(dates, timeseries['values'].tolist())),
    }
