import calendar
import datetime
import os
import shutil

import rasterio
import rasterstats
import netCDF4
import numpy

from .options import app_settings, gfs_variables
from .app import Gfs as App


def newchart(data):
    """
    Determines the environment for generating a timeseries chart
    :param data: a JSON object with params from the UI/API call
    :return:
    """
    # input parameters
    var = str(data['variable'])
    loc_type = data['loc_type']

    # environment settings
    configs = app_settings()
    path = configs['threddsdatadir']
    timestamp = configs['timestamp']

    # list the netcdfs to be processed
    path = os.path.join(path, timestamp, 'netcdfs')
    allfiles = os.listdir(path)
    files = [nc for nc in allfiles if nc.startswith(data['level']) and nc.endswith('.nc')]
    files.sort()

    variables = gfs_variables()
    for option in variables:
        if option[1] == data['variable']:
            name = option[0]
            break

    if loc_type == 'Point':
        values, units = pointchart(var, data['coords'], path, files)
        type = 'Values at a Point'
    elif loc_type == 'Polygon':
        values, units = polychart(var, data['coords'], path, files)
        type = 'Averaged over a Polygon'
    elif loc_type == 'Shapefile':
        values, units = shpchart(var, path, files, data['region'], data['user'])
        if data['region'] == 'customshape':
            type = 'Average for user\'s shapefile'
        else:
            type = 'Average for ' + data['region']

    values.sort(key=lambda tup: tup[0])
    resp = {'values': values, 'units': units, 'variable': var, 'type': type, 'name': name}

    return resp


def pointchart(var, coords, path, files):
    """
    Description: generates a timeseries for a given point and given variable defined by the user.
    Arguments: A dictionary object from the AJAX-ed JSON object that contains coordinates and the variable name.
    Author: Riley Hales
    Dependencies: netcdf4, numpy, datetime, os, calendar, app_settings (options)
    Last Updated: Oct 11 2018
    """
    # return items
    values = []

    # get a list of the lat/lon and units using a reference file
    nc_obj = netCDF4.Dataset(os.path.join(path, files[0]), 'r')
    nc_lons = nc_obj['lon'][:]
    nc_lats = nc_obj['lat'][:]
    units = nc_obj[var].__dict__['units']
    # get the index number of the lat/lon for the point
    lon_indx = (numpy.abs(nc_lons - int(coords[0]))).argmin()
    lat_indx = (numpy.abs(nc_lats - int(coords[1]))).argmin()
    nc_obj.close()

    # extract values at each timestep
    for nc in files:
        # get the time value for each file
        nc_obj = netCDF4.Dataset(path + '/' + nc, 'r')
        t_val = nc_obj['time'].__dict__['begin_date']
        try:
            t_val = datetime.datetime.strptime(t_val, "%Y%m%d")
        except ValueError:
            t_val = datetime.datetime.strptime(t_val, "%Y%m%d%H")
        time = calendar.timegm(t_val.utctimetuple()) * 1000
        # slice the array at the area you want
        val = float(nc_obj[var][0, lat_indx, lon_indx].data)
        values.append((time, val))
        nc_obj.close()

    return values, units


def polychart(var, coords, path, files):
    """
    Description: generates a timeseries for a given point and given variable defined by the user.
    Arguments: A dictionary object from the AJAX-ed JSON object that contains coordinates and the variable name.
    Author: Riley Hales
    Dependencies: netcdf4, numpy, datetime, os, calendar, app_settings (options)
    Last Updated: May 14 2019
    """
    # return items
    values = []

    # get a list of the latitudes and longitudes and the units
    nc_obj = netCDF4.Dataset(os.path.join(path, str(files[0])), 'r')
    nc_lons = nc_obj['lon'][:]
    nc_lats = nc_obj['lat'][:]
    units = nc_obj[var].__dict__['units']
    # get a bounding box of the rectangle in terms of the index number of their lat/lons
    minlon = (numpy.abs(nc_lons - int(coords[0][1][0]))).argmin()
    maxlon = (numpy.abs(nc_lons - int(coords[0][3][0]))).argmin()
    maxlat = (numpy.abs(nc_lats - int(coords[0][1][1]))).argmin()
    minlat = (numpy.abs(nc_lats - int(coords[0][3][1]))).argmin()
    nc_obj.close()

    # extract values at each timestep
    for nc in files:
        # set the time value for each file
        nc_obj = netCDF4.Dataset(path + '/' + nc, 'r')
        t_val = nc_obj['time'].__dict__['begin_date']
        try:
            t_val = datetime.datetime.strptime(t_val, "%Y%m%d")
        except ValueError:
            t_val = datetime.datetime.strptime(t_val, "%Y%m%d%H")
        time = calendar.timegm(t_val.utctimetuple()) * 1000
        # slice the array, drop nan values, get the mean, append to list of values
        array = nc_obj[var][0, minlat:maxlat, minlon:maxlon].data
        array[array < -5000] = numpy.nan  # If you have fill values, change the comparator to git rid of it
        array = array.flatten()
        array = array[~numpy.isnan(array)]
        values.append((time, float(array.mean())))
        nc_obj.close()

    return values, units


def shpchart(var, path, files, region, user):
    """
    Description: This script accepts a netcdf file in a geographic coordinate system, specifically the NASA GLDAS
        netcdfs, and extracts the data from one variable and the lat/lon steps to create a geotiff of that information.
    Dependencies: netCDF4, numpy, rasterio, rasterstats, os, shutil, calendar, datetime, app_settings (options)
    Params: View README.md
    Returns: Creates a geotiff named 'geotiff.tif' in the directory specified
    Author: Riley Hales, RCH Engineering, March 2019
    """
    # return items
    values = []

    # Remove old geotiffs before filling it
    wrkpath = App.get_app_workspace().path
    geotiffdir = os.path.join(wrkpath, 'geotiffs')
    if os.path.isdir(geotiffdir):
        shutil.rmtree(geotiffdir)
    os.mkdir(geotiffdir)

    # open the netcdf and get metadata
    nc_obj = netCDF4.Dataset(os.path.join(path, files[0]), 'r')
    lat = nc_obj.variables['lat'][:]
    lon = nc_obj.variables['lon'][:]
    units = nc_obj[var].__dict__['units']
    geotransform = rasterio.transform.from_origin(lon.min(), lat.max(), lat[1] - lat[0], lon[1] - lon[0])
    nc_obj.close()

    # read netcdf, create geotiff, zonal statistics, format outputs for highcharts plotting
    for file in files:
        # open the netcdf and get the data array
        nc_obj = netCDF4.Dataset(os.path.join(path, file), 'r')
        var_data = nc_obj.variables[var][:]  # this is the array of values for the nc_obj
        array = numpy.asarray(var_data)[0, :, :]  # converting the data type
        array[array < -9000] = numpy.nan  # use the comparator to drop nodata fills
        array = array[::-1]  # vertically flip array so tiff orientation is right (you just have to, try it)

        # create the timesteps for the highcharts plot
        t_val = nc_obj['time'].__dict__['begin_date']
        t_val = datetime.datetime.strptime(t_val, "%Y%m%d%H")
        time = calendar.timegm(t_val.utctimetuple()) * 1000

        # file paths and settings
        if region == 'customshape':
            shppath = App.get_user_workspace(user).path
            shp = [i for i in os.listdir(shppath) if i.endswith('.shp')]
            shppath = os.path.join(shppath, shp[0])
        else:
            shppath = os.path.join(wrkpath, 'shapefiles', region, region.replace(' ', '') + '.shp')
        gtiffpath = os.path.join(wrkpath, 'geotiffs', 'geotiff.tif')

        with rasterio.open(gtiffpath, 'w', driver='GTiff', height=len(lat), width=len(lon), count=1, dtype='float32',
                           nodata=numpy.nan, crs='+proj=latlong', transform=geotransform) as newtiff:
            newtiff.write(array, 1)  # data, band number

        stats = rasterstats.zonal_stats(shppath, gtiffpath, stats="mean")
        values.append((time, stats[0]['mean']))

    if os.path.isdir(geotiffdir):
        shutil.rmtree(geotiffdir)

    return values, units
