import numpy
import datetime
import math
import os
import shutil
import requests

import netCDF4
import xarray

from .options import app_configuration, gfs_variables


def setenvironment():
    """
    Dependencies: os, shutil, datetime, urllib.request, app_configuration (options)
    """
    print('Setting the Environment')
    # determine the most day and hour of the day timestamp of the most recent GFS forecast
    now = datetime.datetime.utcnow()
    if now.hour > 19:
        fc_time = '18'
        timestamp = now.strftime("%Y%m%d") + fc_time
    elif now.hour > 13:
        fc_time = '12'
        timestamp = now.strftime("%Y%m%d") + fc_time
    elif now.hour > 7:
        fc_time = '06'
        timestamp = now.strftime("%Y%m%d") + fc_time
    elif now.hour > 1:
        fc_time = '00'
        timestamp = now.strftime("%Y%m%d") + fc_time
    else:
        fc_time = '18'
        now = now - datetime.timedelta(days=1)
        timestamp = now.strftime("%Y%m%d") + fc_time
    print('determined the timestamp to download: ' + timestamp)

    # set folder paths for the environment
    configuration = app_configuration()
    threddspath = configuration['threddsdatadir']
    wrksp = configuration['app_wksp_path']

    # if the file structure already exists, quit
    if os.path.exists(os.path.join(threddspath, timestamp)):
        return threddspath, timestamp

    print('Creating new file structure')
    newdirectory = os.path.join(threddspath, timestamp)
    os.mkdir(newdirectory)
    os.chmod(newdirectory, 0o777)
    newdirectory = os.path.join(threddspath, timestamp, 'gribs')
    os.mkdir(newdirectory)
    os.chmod(newdirectory, 0o777)
    newdirectory = os.path.join(threddspath, timestamp, 'netcdfs')
    os.mkdir(newdirectory)
    os.chmod(newdirectory, 0o777)
    newdirectory = os.path.join(threddspath, timestamp, 'processed')
    os.mkdir(newdirectory)
    os.chmod(newdirectory, 0o777)

    print('All done, on to do work')
    return threddspath, timestamp


def download_gfs(threddspath, timestamp):
    print('\nStarting GFS Grib Downloads')
    # set filepaths
    gribsdir = os.path.join(threddspath, timestamp, 'gribs')

    # if you already have a folder with data for this timestep, quit this function (you dont need to download it)
    if not os.path.exists(gribsdir):
        print('There is no download folder, you must have already processed the downloads. Skipping download stage.')
        return threddspath, timestamp
    # otherwise, remove anything in the folder before starting (in case there was a partial download)
    else:
        shutil.rmtree(gribsdir)
        os.mkdir(gribsdir)
        os.chmod(gribsdir, 0o777)

    # get the parts of the timestamp to put into the url
    time = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
    time = datetime.datetime.strftime(time, "%H")

    # This is the List of forecast timesteps for 5 days (6-hr increments). download them all
    fc_steps = ['006', '012', '018', '024', '030', '036', '042', '048', '054', '060', '066', '072', '078', '084', '090', '096', '102', '108', '114', '120']

    # this is where the actual downloads happen. set the url, filepath, then download
    for step in fc_steps:
        url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t' + time + 'z.pgrb2.0p25.f' + \
              step + "&all_lev=on&all_var=on&leftlon=-180&rightlon=180&toplat=90&bottomlat=-90&dir=%2Fgfs." + timestamp
        filename = 'gfs_' + timestamp + '_' + step + '.grb'
        print('downloading the file ' + filename)
        filepath = os.path.join(gribsdir, filename)
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)

    print('Finished Downloads')
    return


def grib_to_netcdf(threddspath, timestamp):
    """
    Dependencies: xarray, netcdf4, os, shutil, app_configuration (options)
    """
    print('\nStarting Grib Conversions')
    # setting the environment file paths
    gribs = os.path.join(threddspath, timestamp, 'gribs')
    netcdfs = os.path.join(threddspath, timestamp, 'netcdfs')

    # if you already have gfs netcdfs in the netcdfs folder, quit the function
    if not os.path.exists(gribs):
        print('There are no gribs to convert, you must have already run this step. Skipping conversion')
        return
    # otherwise, remove anything in the folder before starting (in case there was a partial conversion)
    else:
        shutil.rmtree(netcdfs)
        os.mkdir(netcdfs)
        os.chmod(netcdfs, 0o777)

    # for each grib file you downloaded, open it, convert it to a netcdf
    files = os.listdir(gribs)
    files = [grib for grib in files if grib.endswith('.grb')]
    for file in files:
        path = os.path.join(gribs, file)
        print('opening grib file ' + path)
        obj = xarray.open_dataset(path, engine='cfgrib', backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})
        print('converting it to a netcdf')
        ncname = file.replace('gfs_', '').replace('.grb', '')
        ncpath = os.path.join(netcdfs, 'gfs_' + ncname + '.nc')
        obj.to_netcdf(ncpath, mode='w')
        print('converted\n')

    # delete the gribs now that you're done with them triggering future runs to skip the download step
    shutil.rmtree(gribs)

    print('Conversion Completed')
    return


def nc_georeference(threddspath, timestamp):
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
    netcdfs = os.path.join(threddspath, timestamp, 'netcdfs')
    processed = os.path.join(threddspath, timestamp, 'processed')

    # if you already have processed netcdfs files, skip this and quit the function
    if not os.path.exists(netcdfs):
        print('There are no netcdfs to be converted. Skipping netcdf processing.')
        return
    # otherwise, remove anything in the folder before starting (in case there was a partial processing)
    else:
        shutil.rmtree(processed)
        os.mkdir(processed)
        os.chmod(processed, 0o777)

    # list the files that need to be converted
    net_files = os.listdir(netcdfs)
    files = [file for file in net_files if file.endswith('.nc')]
    print('There are ' + str(len(files)) + ' compatible files.')

    # read the first file that we'll copy data from in the next blocks of code
    print('Preparing the reference file')
    path = os.path.join(netcdfs, net_files[0])
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
        openpath = os.path.join(netcdfs, file)
        savepath = os.path.join(processed, 'processed_' + file)
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

            # copy the arrays of data and set the timestamp/properties
            date = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
            date = datetime.datetime.strftime(date, "%Y-%m-%d %H:00:00")
            if variable == 'time':
                duplicate[variable][:] = [hour]
                hour = hour + 6
                duplicate[variable].long_name = original[variable].long_name
                duplicate[variable].units = "hours since " + date
                duplicate[variable].axis = "T"
                # also set the begin date of this data
                duplicate[variable].begin_date = timestamp
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
            duplicate[variable].begin_date = timestamp
            duplicate[variable].units = original[variable].units

        # close the files, delete the one you just did, start again
        original.close()
        duplicate.sync()
        duplicate.close()

    # delete the netcdfs now that we're done with them triggering future runs to skip this step
    shutil.rmtree(netcdfs)

    print('Finished File Conversions')
    return


def new_ncml(threddspath, timestamp):
    print('\nWriting a new ncml file for this date')
    # create a new ncml file by filling in the template with the right dates and writing to a file
    ncml = os.path.join(threddspath, 'gfs.ncml')
    date = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
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
            '        <scan location="' + timestamp + '/processed/"/>\n'
            '    </aggregation>\n'
            '</netcdf>'
        )
    print('Wrote New .ncml')
    return


def cleanup(threddspath, timestamp):
    # write a file with the current timestep triggering the app to start using this data
    config = app_configuration()
    with open(os.path.join(config['app_wksp_path'], 'timestep.txt'), 'w') as file:
        file.write(timestamp)

    # delete anything that isn't the new folder of data or the new gfs.ncml file
    print('\nGetting rid of old data folders')
    files = os.listdir(threddspath)
    files.remove(timestamp)
    files.remove('gfs.ncml')
    for file in files:
        try:
            shutil.rmtree(os.path.join(threddspath, file))
        except:
            os.remove(os.path.join(threddspath, file))

    print('Done')
    return


def set_wmsbounds(threddspath, timestamp):
    """
    Dynamically defines exact boundaries for the legend and wms so that they are synchronized
    Dependencies: netcdf4, os, math, numpy
    """
    print('\nSetting the WMS bounds')
    # get a list of files to
    ncfolder = os.path.join(threddspath, timestamp, 'processed')
    ncs = os.listdir(ncfolder)
    files = [file for file in ncs if file.startswith('processed')][0]

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
