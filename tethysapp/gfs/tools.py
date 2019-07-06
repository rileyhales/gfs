import calendar
import datetime
import os
import shutil

import rasterio
import rasterstats
import netCDF4
import numpy

from .app import Gfs as App
from .options import app_configuration


def pointchart(data):
    """
    Description: generates a timeseries for a given point and given variable defined by the user.
    Arguments: A dictionary object from the AJAX-ed JSON object that contains coordinates and the variable name.
    Author: Riley Hales
    Dependencies: netcdf4, numpy, datetime, os, calendar, app_configuration (options)
    Last Updated: Oct 11 2018
    """
    # input parameters
    var = str(data['variable'])
    coords = data['coords']
    level = data['level']

    # environment settings
    configs = app_configuration()
    path = configs['threddsdatadir']
    path = os.path.join(path, configs['timestamp'], 'netcdfs')

    # return items
    values = []

    # list the netcdfs to be processed
    allfiles = os.listdir(path)
    files = [nc for nc in allfiles if nc.startswith(level) and nc.endswith('.nc')]
    files.sort()

    # get a list of the latitudes and longitudes and the units
    dataset = netCDF4.Dataset(os.path.join(path, str(files[0])), 'r')
    nc_lons = dataset['lon'][:]
    nc_lats = dataset['lat'][:]
    data['units'] = dataset[var].__dict__['units']
    # get the index number of the lat/lon for the point
    adj_lon_ind = (numpy.abs(nc_lons - coords[0])).argmin()
    adj_lat_ind = (numpy.abs(nc_lats - coords[1])).argmin()
    dataset.close()

    # extract values at each timestep
    for nc in files:
        # get the time value for each file
        dataset = netCDF4.Dataset(os.path.join(path, nc), 'r')
        t_value = dataset['time'].__dict__['begin_date']
        t_value = datetime.datetime.strptime(t_value, "%Y%m%d%H")
        t_value = calendar.timegm(t_value.utctimetuple()) * 1000
        # slice the array at the area you want
        val = float(dataset[var][0, adj_lat_ind, adj_lon_ind].data)
        values.append((t_value, val))
        dataset.close()

    values.sort()
    data['values'] = values
    return data


def polychart(data):
    """
    Description: generates a timeseries for a given point and given variable defined by the user.
    Arguments: A dictionary object from the AJAX-ed JSON object that contains coordinates and the variable name.
    Author: Riley Hales
    Dependencies: netcdf4, numpy, datetime, os, calendar, app_configuration (options)
    Last Updated: May 14 2019
    """
    # input parameters
    var = str(data['variable'])
    coords = data['coords'][0]  # 5x2 array 1 row/[lat,lon]/corner (1st repeated), clockwise from bottom-left
    level = data['level']

    # environment settings
    configs = app_configuration()
    path = configs['threddsdatadir']
    path = os.path.join(path, configs['timestamp'], 'netcdfs')

    # return items
    values = []

    # list the netcdfs to be processed
    allfiles = os.listdir(path)
    files = [nc for nc in allfiles if nc.startswith(level) and nc.endswith('.nc')]
    files.sort()

    # get a list of the latitudes and longitudes and the units
    dataset = netCDF4.Dataset(os.path.join(path, str(files[0])), 'r')
    nc_lons = dataset['lon'][:]
    nc_lats = dataset['lat'][:]
    data['units'] = dataset[var].__dict__['units']
    # get a bounding box of the rectangle in terms of the index number of their lat/lons
    minlon = (numpy.abs(nc_lons - coords[1][0])).argmin()
    maxlon = (numpy.abs(nc_lons - coords[3][0])).argmin()
    maxlat = (numpy.abs(nc_lats - coords[1][1])).argmin()
    minlat = (numpy.abs(nc_lats - coords[3][1])).argmin()
    dataset.close()

    # extract values at each timestep
    for nc in files:
        # get the time value for each file
        dataset = netCDF4.Dataset(os.path.join(path, nc), 'r')
        t_value = dataset['time'].__dict__['begin_date']
        t_value = datetime.datetime.strptime(t_value, "%Y%m%d%H")
        t_value = calendar.timegm(t_value.utctimetuple()) * 1000
        # slice the array at the area you want
        array = dataset[var][0, minlat:maxlat, minlon:maxlon].data
        array[array < -9000] = numpy.nan  # If you have fill values, change the comparator to git rid of it
        array = array.flatten()
        array = array[~numpy.isnan(array)]
        values.append((t_value, float(array.mean())))
        dataset.close()

    values.sort()
    data['values'] = values
    return data


def shpchart(data):
    """
    Description: This script accepts a netcdf file in a geographic coordinate system, specifically the NASA GLDAS
        netcdfs, and extracts the data from one variable and the lat/lon steps to create a geotiff of that information.
    Dependencies: netCDF4, numpy, rasterio, rasterstats, os, shutil, calendar, datetime, app_configuration (options)
    Params: View README.md
    Returns: Creates a geotiff named 'geotiff.tif' in the directory specified
    Author: Riley Hales, RCH Engineering, March 2019
    """
    # input parameters
    var = str(data['variable'])
    region = data['region']
    level = data['level']
    user = data['user']

    # environment settings
    configs = app_configuration()
    path = configs['threddsdatadir']
    path = os.path.join(path, configs['timestamp'], 'netcdfs')
    wrkpath = configs['app_wksp_path']

    # return items
    values = []

    # list the netcdfs to be processed
    allfiles = os.listdir(path)
    files = [nc for nc in allfiles if nc.startswith(level) and nc.endswith('.nc')]
    files.sort()

    # Remove old geotiffs before filling it
    geotiffdir = os.path.join(App.get_app_workspace().path, 'geotiffs')
    if os.path.isdir(geotiffdir):
        shutil.rmtree(geotiffdir)
    os.mkdir(geotiffdir)

    # read netcdf, create geotiff, zonal statistics, format outputs for highcharts plotting
    for i in range(len(files)):
        # open the netcdf and get metadata
        nc_obj = netCDF4.Dataset(os.path.join(path, str(files[i])), 'r')
        lat = nc_obj.variables['lat'][:]
        lon = nc_obj.variables['lon'][:]
        data['units'] = nc_obj[var].__dict__['units']

        # get the variable's data array
        var_data = nc_obj.variables[var][:]  # this is the array of values for the dataset
        array = numpy.asarray(var_data)[0, :, :]  # converting the data type
        array[array < -9000] = numpy.nan  # use the comparator to drop nodata fills
        array = array[::-1]  # vertically flip array so tiff orientation is right (you just have to, try it)

        # create the timesteps for the highcharts plot
        t_value = (nc_obj['time'].__dict__['begin_date'])
        t_value = datetime.datetime.strptime(t_value, "%Y%m%d%H")
        t_value = calendar.timegm(t_value.utctimetuple()) * 1000

        # file paths and settings
        if region == 'customshape':
            shppath = App.get_user_workspace(user).path
            shp = [i for i in os.listdir(shppath) if i.endswith('.shp')]
            shppath = os.path.join(shppath, shp[0])
        else:
            region = data['region']
            shppath = os.path.join(wrkpath, 'shapefiles', region, region.replace(' ', '') + '.shp')

        gtiffpath = os.path.join(wrkpath, 'geotiffs', 'geotiff.tif')
        geotransform = rasterio.transform.from_origin(lon.min(), lat.max(), lat[1] - lat[0], lon[1] - lon[0])

        with rasterio.open(gtiffpath, 'w', driver='GTiff', height=len(lat), width=len(lon), count=1, dtype='float32',
                           nodata=numpy.nan, crs='+proj=latlong', transform=geotransform) as newtiff:
            newtiff.write(array, 1)
        stats = rasterstats.zonal_stats(shppath, gtiffpath, stats="mean")
        values.append((t_value, stats[0]['mean']))

    if os.path.isdir(geotiffdir):
        shutil.rmtree(geotiffdir)

    values.sort()
    data['values'] = values
    return data
