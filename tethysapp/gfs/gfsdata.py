import numpy
import datetime
import math
import os
import shutil
import urllib.request

import netCDF4
import xarray

from .options import app_configuration, gfs_variables


def download_gfs():
    """
    Dependencies: os, shutil, datetime, urllib.request, app_configuration (options)
    """
    print('Downloading new grib data')
    # determine the most day and hour of the day timestamp of the most recent GFS forecast
    threddsdir = app_configuration()['threddsdatadir']
    now = datetime.datetime.now()
    if now.hour > 19:
        fc_time = '18'
        fc_tstamp = now.strftime("%Y%m%d") + fc_time
    elif now.hour > 13:
        fc_time = '12'
        fc_tstamp = now.strftime("%Y%m%d") + fc_time
    elif now.hour > 7:
        fc_time = '06'
        fc_tstamp = now.strftime("%Y%m%d") + fc_time
    elif now.hour > 1:
        fc_time = '00'
        fc_tstamp = now.strftime("%Y%m%d") + fc_time
    else:
        fc_time = '18'
        now = now - datetime.timedelta(days=1)
        fc_tstamp = now.strftime("%Y%m%d") + fc_time
    print('determined the timestamp to download: ' + fc_tstamp)

    # if you already have a folder of data for this timestep, quit this function (you dont need to download it)
    if os.path.exists(os.path.join(threddsdir, 'gribs', fc_tstamp)):
        print('You already have the most recent data. Skipping download')
        return fc_tstamp

    # delete directory of old downloaded files, remake the directories
    print('deleting old data')
    shutil.rmtree(os.path.join(threddsdir, 'gribs'))
    os.mkdir(os.path.join(threddsdir, 'gribs'))
    downloadpath = os.path.join(threddsdir, 'gribs', fc_tstamp)
    os.mkdir(downloadpath)

    # This is the List of forecast timesteps for 2 days (6-hr increments). download them all
    t_steps = ['006', '012', '018', '024', '030', '036', '042', '048', '054', '060', '066', '072',
               '078', '084', '090', '096', '102', '108', '114', '120']
    for step in t_steps:
        url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t' + fc_time + 'z.pgrb2.0p25.f' + \
              step + "&all_lev=on&all_var=on&leftlon=-180&rightlon=180&toplat=90&bottomlat=-90&dir=%2Fgfs." + fc_tstamp
        filename = 'gfs_' + fc_tstamp + '_' + step + '.grb'
        print('downloading the file ' + filename)
        filepath = os.path.join(downloadpath, filename)
        urllib.request.urlretrieve(url, filepath)

    return fc_tstamp


def grib_to_netcdf(fc_tstamp):
    """
    Dependencies: xarray, netcdf4, os, shutil, app_configuration (options)
    """
    print('\nStarting grib conversions')
    # setting the environment file paths
    thredds = app_configuration()['threddsdatadir']
    gribs = os.path.join(thredds, 'gribs', fc_tstamp)
    ncfolder = os.path.join(thredds, 'netcdfs')

    # if you already have gfs netcdfs in the netcdfs folder, quit the function
    files = os.listdir(ncfolder)
    ncs = [file for file in files if file.endswith('.nc') and file.startswith('gfs')]
    if len(ncs) > 10:
        print('You already converted the gribs to netcdfs. Skipping conversion')
        return
    # delete the old data and remake the folder
    shutil.rmtree(ncfolder)
    os.mkdir(ncfolder)

    # for each grib file you downloaded, open it, convert it to a netcdf
    files = os.listdir(gribs)
    files = [grib for grib in files if grib.endswith('.grb')]
    for file in files:
        path = os.path.join(gribs, file)
        print('opening grib file ' + path)
        obj = xarray.open_dataset(path, engine='cfgrib', backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})
        print('converting it to a netcdf')
        ncname = file.replace('gfs_', '').replace('.grb', '')
        ncpath = os.path.join(ncfolder, 'gfs_' + ncname + '.nc')
        obj.to_netcdf(ncpath, mode='w')
        print('converted\n')

    # delete everything in the gribs directory (not just the .grb files in case other things are there)
    # print('deleting the old grib files')
    # files = os.listdir(gribs)
    # for file in files:
    #     os.remove(os.path.join(gribs, file))
    # print('finished')

    return


def nc_georeference(fc_tstamp):
    """
    Description: Intended to make a THREDDS data server compatible netcdf file out of an incorrectly structured
        netcdf file.
    Author: Riley Hales, 2019
    Dependencies: netCDF4, os, datetime
    THREDDS Documentation specifies that an appropriately georeferenced file should
    1. 2 Coordinate Dimensions, lat and lon. Their size is the number of steps across the grid.
    2. 2 Coordinate Variables, lat and lon, whose arrays contain the lat/lon values of the grid points.
        These variables only require the corresponding lat or lon dimension.
    3. 1 time dimension whose length is the number of time steps
    4. 1 time variable whose array contains the difference in time between steps using the units given in the metadata.
    5. Each variable requires the the time and Coordinate Dimensions, in that order (time, lat, lon)
    6. Each variable has the long_name, units, standard_name property values correct
    7. The variable property coordinates = "lat lon" or else is blank/doesn't exist
    """
    print('\nProcessing the netCDF files')

    # setting the environment file paths
    ncfolder = app_configuration()['threddsdatadir']
    ncfolder = os.path.join(ncfolder, 'netcdfs')
    files = os.listdir(ncfolder)

    # if you already have processed netcdfs files, skip this and quit the function
    files = [file for file in files if file.endswith('.nc') and file.startswith('process')]
    if len(files) > 0:
        print('There are already processed netcdfs here. Skipping netcdf processing.')
        return

    # list the files that need to be converted
    files = os.listdir(ncfolder)
    files = [file for file in files if file.endswith('.nc') and not file.startswith('process')]
    print('There are ' + str(len(files)) + ' compatible files. They are:')

    # read the first file that we'll copy data from in the next blocks of code
    print('Preparing the reference file')
    path = os.path.join(ncfolder, files[0])
    netcdf_obj = netCDF4.Dataset(path, 'r', clobber=False, diskless=True)

    # get a dictionary of the dimensions and their size and rename the north/south and east/west ones
    dimensions = {}
    for dimension in netcdf_obj.dimensions.keys():
        dimensions[dimension] = netcdf_obj.dimensions[dimension].size
    dimensions['lat'] = dimensions['latitude']
    dimensions['lon'] = dimensions['longitude']
    dimensions['time'] = 1
    del dimensions['latitude'], dimensions['longitude']

    # get a list of the variables and remove the one's i'm going to 'manually' correct
    variables = netcdf_obj.variables
    del variables['valid_time'], variables['step'], variables['latitude'], variables['longitude'], variables['surface']
    variables = variables.keys()

    # min lat and lon and the interval between values (these are static values
    lat_min = -90
    lon_min = -180
    lat_step = .25
    lon_step = .25
    netcdf_obj.close()

    # this is where the files start getting copied
    for file in files:
        print('Working on file ' + str(file))
        openpath = os.path.join(ncfolder, file)
        savepath = os.path.join(ncfolder, 'processed_' + file)
        # open the file to be copied
        original = netCDF4.Dataset(openpath, 'r', clobber=False, diskless=True)
        duplicate = netCDF4.Dataset(savepath, 'w', clobber=True, format='NETCDF4', diskless=False)
        # set the global netcdf attributes - important for georeferencing
        duplicate.setncatts(original.__dict__)

        # specify dimensions from what we copied before
        for dimension in dimensions:
            duplicate.createDimension(dimension, dimensions[dimension])

        # 'Manually' create the dimensions that need to be set carefully
        duplicate.createVariable(varname='lat', datatype='f4', dimensions='lat')
        duplicate.createVariable(varname='lon', datatype='f4', dimensions='lon')

        # create the lat and lon values as a 1D array
        lat_list = [lat_min + i * lat_step for i in range(dimensions['lat'])]
        lon_list = [lon_min + i * lon_step for i in range(dimensions['lon'])]
        duplicate['lat'][:] = lat_list
        duplicate['lon'][:] = lon_list

        # set the attributes for lat and lon (except fill value, you just can't copy it)
        for attr in original['latitude'].__dict__:
            if attr != "_FillValue":
                duplicate['lat'].setncattr(attr, original['latitude'].__dict__[attr])
        for attr in original['longitude'].__dict__:
            if attr != "_FillValue":
                duplicate['lon'].setncattr(attr, original['longitude'].__dict__[attr])

        # copy the rest of the variables
        hour = 6
        for variable in variables:
            # check to use the lat/lon dimension names
            dimension = original[variable].dimensions
            if 'latitude' in dimension:
                dimension = list(dimension)
                dimension.remove('latitude')
                dimension.append('lat')
                dimension = tuple(dimension)
            if 'longitude' in dimension:
                dimension = list(dimension)
                dimension.remove('longitude')
                dimension.append('lon')
                dimension = tuple(dimension)
            if len(dimension) == 2:
                dimension = ('time', 'lat', 'lon')
            if variable == 'time':
                dimension = ('time',)

            # create the variable
            duplicate.createVariable(varname=variable, datatype='f4', dimensions=dimension)

            # copy the arrays of data and set the metadata/properties
            date = datetime.datetime.strptime(fc_tstamp, "%Y%m%d%H")
            date = datetime.datetime.strftime(date, "%Y-%m-%d %H:00:00")
            if variable == 'time':
                duplicate[variable][:] = [hour]
                hour = hour + 6
                duplicate[variable].long_name = original[variable].long_name
                duplicate[variable].units = "hours since " + date
                duplicate[variable].axis = "T"
                # also set the begin date of this data
                duplicate[variable].begin_date = fc_tstamp
            if variable == 'lat':
                duplicate[variable][:] = original[variable][:]
                duplicate[variable].axis = "Y"
            if variable == 'lon':
                duplicate[variable][:] = original[variable][:]
                duplicate[variable].axis = "X"
            else:
                duplicate[variable][:] = original[variable][:]
                duplicate[variable].axis = "lat lon"
            duplicate[variable].long_name = original[variable].long_name
            duplicate[variable].begin_date = fc_tstamp
            duplicate[variable].units = original[variable].unit

        # close the files, delete the one you just did, start again
        original.close()
        duplicate.sync()
        duplicate.close()
        os.remove(openpath)

    return


def new_ncml(fc_tstamp):
    print('\nWriting a new ncml file for this date')
    ncfolder = app_configuration()['threddsdatadir']
    ncml = os.path.join(ncfolder, 'gfs.ncml')
    date = datetime.datetime.strptime(fc_tstamp, "%Y%m%d%H")
    date = datetime.datetime.strftime(date, "%Y-%m-%d %H:00:00")
    with open(ncml, 'w') as file:
        file.write(
            '<netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">\n'
            '    <variable name="time" type="int" shape="time">\n'
            '        <attribute name="units" value="hours since ' + date + '"/>\n'
            '        <attribute name="_CoordinateAxisType" value="Time" />\n'
            '        <values start="0" increment="6" />\n'
            '    </variable>\n'
            '    <aggregation dimName="time" type="joinExisting" recheckEvery="1 hour">\n'
            '        <scan location="netcdfs/"/>\n'
            '    </aggregation>\n'
            '</netcdf>'
        )
    print('completed ncml')
    return


def set_wmsbounds():
    """
    Dynamically defines exact boundaries for the legend and wms so that they are synchronized
    Dependencies: netcdf4, os, math, numpy
    """
    print('\nSetting the WMS bounds')
    boundsfile = os.path.join(os.path.dirname(__file__), 'public', 'js', 'bounds.js')
    print(boundsfile)
    ncfolder = app_configuration()['threddsdatadir']
    ncfolder = os.path.join(ncfolder, 'netcdfs')
    files = os.listdir(ncfolder)
    files = [file for file in files if file.endswith('.nc') and file.startswith('process')][0]

    # setup the dictionary of values to return
    bounds = {}
    variables = gfs_variables()
    for variable in variables:
        bounds[variables[variable]] = ''

    path = os.path.join(ncfolder, files)
    dataset = netCDF4.Dataset(path, 'r')
    print('working on file ' + path)

    for variable in variables:
        print('checking for variable ' + variable)
        array = dataset[variables[variable]][:]
        array = array.flatten()
        array = array[~numpy.isnan(array)]
        maximum = math.ceil(max(array))
        if maximum == numpy.nan:
            maximum = 0
        print('max is ' + str(maximum))

        minimum = math.floor(min(array))
        if minimum == numpy.nan:
            minimum = 0
        print('min is ' + str(minimum))

        bounds[variables[variable]] = str(minimum) + ',' + str(maximum)
    dataset.close()

    print('\ndone checking for max/min. writing the file')
    boundsfile = os.path.join(os.path.dirname(__file__), 'public', 'js', 'bounds.js')
    with open(boundsfile, 'w') as file:
        file.write('const bounds = ' + str(bounds) + ';')
    print('wrote the file. all done')
    return
