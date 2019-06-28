import logging
import shutil
import pygrib
import netCDF4
import requests
import numpy
import time as Time
from .options import *


def setenvironment():
    """
    Dependencies: os, shutil, datetime, urllib.request, app_settings (options)
    """
    logging.info('\nSetting the Environment for the GFS Workflow')
    # determine the most day and hour of the day timestamp of the most recent GFS forecast
    now = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
    if now.hour >= 18:
        timestamp = now.strftime("%Y%m%d") + '18'
    elif now.hour >= 12:
        timestamp = now.strftime("%Y%m%d") + '12'
    elif now.hour >= 6:
        timestamp = now.strftime("%Y%m%d") + '06'
    elif now.hour >= 0:
        timestamp = now.strftime("%Y%m%d") + '00'
    logging.info('determined the timestamp to download: ' + timestamp)

    # set folder paths for the environment
    configuration = app_settings()
    threddspath = configuration['threddsdatadir']
    wrksppath = configuration['app_wksp_path']

    # perform a redundancy check, if the last timestamp is the same as current, abort the workflow
    timefile = os.path.join(wrksppath, 'timestamp.txt')
    with open(timefile, 'r') as file:
        lasttime = file.readline()
        if lasttime == timestamp:
            # use the redundant check to skip the function because its already been run
            redundant = True
            logging.info('The last recorded timestamp is the timestamp we determined, aborting workflow')
            return threddspath, wrksppath, timestamp, redundant
        elif lasttime == 'clobbered':
            # if you marked clobber is true, dont check for old folders from partially completed workflows
            redundant = False
        else:
            # check to see if there are remnants of partially completed runs and dont destroy old folders
            redundant = False
            test = os.path.join(threddspath, timestamp, 'netcdfs')
            if os.path.exists(test):
                logging.info('There are directories for this timestep but the workflow wasn\'t finished. Analyzing...')
                return threddspath, wrksppath, timestamp, redundant

    # create the file structure and their permissions for the new data
    logging.info('Creating THREDDS file structure')
    new_dir = os.path.join(threddspath)
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.mkdir(new_dir)
    os.chmod(new_dir, 0o777)
    new_dir = os.path.join(threddspath, timestamp)
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.mkdir(new_dir)
    os.chmod(new_dir, 0o777)
    for filetype in ('gribs', 'netcdfs', 'processed'):
        new_dir = os.path.join(threddspath, timestamp, filetype)
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        os.mkdir(new_dir)
        os.chmod(new_dir, 0o777)

    logging.info('All done setting up folders, on to do work')
    return threddspath, wrksppath, timestamp, redundant


def download_gfs(threddspath, timestamp):
    logging.info('\nStarting GFS grib Downloads')
    # set filepaths
    gribsdir = os.path.join(threddspath, timestamp, 'gribs')

    # if you already have a folder with data for this timestep, quit this function (you dont need to download it)
    if not os.path.exists(gribsdir):
        logging.info('There is no download folder, you must have already processed them. Skipping download stage.')
        return True
    elif len(os.listdir(gribsdir)) >= 5:
        logging.info('There are already 28 forecast steps in here. Dont need to download them')
        return True
    # otherwise, remove anything in the folder before starting (in case there was a partial download)
    else:
        shutil.rmtree(gribsdir)
        os.mkdir(gribsdir)
        os.chmod(gribsdir, 0o777)

    # # get the parts of the timestamp to put into the url
    time = datetime.datetime.strptime(timestamp, "%Y%m%d%H").strftime("%H")
    fc_date = datetime.datetime.strptime(timestamp, "%Y%m%d%H").strftime("%Y%m%d")

    # This is the List of forecast timesteps for 5 days (6-hr increments). download them all
    fc_steps = ['006', '012', '018', '024', '030']  # , '036', '042', '048', '054', '060', '066', '072', '078', '084']
    # '090', '096', '102', '108', '114', '120', '126', '132', '138', '144', '150', '156', '162', '168']

    for step in fc_steps:
        url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t' + time + 'z.pgrb2.0p25.f' + step + \
              '&all_lev=on&all_var=on&dir=%2Fgfs.' + fc_date + '%2F' + time
        fc_timestamp = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
        file_timestep = fc_timestamp + datetime.timedelta(hours=int(step))
        filename_timestep = datetime.datetime.strftime(file_timestep, "%Y%m%d%H")

        filename = filename_timestep + '.grb'
        logging.info('downloading ' + filename + ' (step ' + step + ' of 084)')
        filepath = os.path.join(gribsdir, filename)
        start = Time.time()
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=10240):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
        except requests.HTTPError as e:
            errorcode = e.response.status_code
            logging.info('\nHTTPError ' + str(errorcode) + ' downloading ' + filename + ' from\n' + url)
            if errorcode == 404:
                logging.info('The file was not found on the server, trying an older forecast time')
            elif errorcode == 500:
                logging.info('Probably a problem with the URL. Check the log and try the link')
            return False
        logging.info('  Download took ' + str(Time.time() - start))
    logging.info('Finished Downloads')
    return True


def grib_to_netcdf(threddspath, timestamp):
    """
    Dependencies: xarray, netcdf4, os, shutil, app_configuration (options)
    """
    logging.info('\nStarting Grib Conversions')
    # setting the environment file paths
    gribs = os.path.join(threddspath, timestamp, 'gribs')
    netcdfs = os.path.join(threddspath, timestamp, 'netcdfs')

    # if you already have gfs netcdfs in the netcdfs folder, quit the function
    if not os.path.exists(gribs):
        logging.info('There are no gribs to convert, you must have already run this step. Skipping conversion')
        return
    # otherwise, remove anything in the folder before starting (in case there was a partial conversion)
    else:
        shutil.rmtree(netcdfs)
        os.mkdir(netcdfs)
        os.chmod(netcdfs, 0o777)

    # for each grib file you downloaded, open it, convert it to a netcdf
    files = os.listdir(gribs)
    files = [grib for grib in files if grib.endswith('.grb')]
    for level in gfs_forecastlevels():
        logging.info('\nworking on level ' + level)
        time = 6
        latitudes = [-90 + (i * .25) for i in range(721)]
        longitudes = [-180 + (i * .25) for i in range(1440)]
        for file in files:
            # create the new netcdf
            logging.info('converting ' + file)
            ncname = level + '_' + file.replace('.grb', '.nc')
            ncpath = os.path.join(netcdfs, ncname)
            new_nc = netCDF4.Dataset(ncpath, 'w', clobber=True, format='NETCDF4', diskless=False)

            new_nc.createDimension('time', 1)
            new_nc.createDimension('lat', 721)
            new_nc.createDimension('lon', 1440)

            new_nc.createVariable(varname='time', datatype='f4', dimensions='time')
            new_nc['time'].axis = 'T'
            new_nc.createVariable(varname='lat', datatype='f4', dimensions='lat')
            new_nc['lat'].axis = 'lat'
            new_nc.createVariable(varname='lon', datatype='f4', dimensions='lon')
            new_nc['lon'].axis = 'lon'

            # set the value of the time variable data
            new_nc['time'][:] = [time]
            time += 6

            # read a file to get the lat/lon variable data
            new_nc['lat'][:] = latitudes
            new_nc['lon'][:] = longitudes

            gribpath = os.path.join(gribs, file)
            gribfile = pygrib.open(gribpath)
            gribfile.seek(0)
            filtered_grib = gribfile(typeOfLevel=level)
            for variable in filtered_grib:
                short = variable.shortName
                if short not in ['time', 'lat', 'lon']:
                    try:
                        new_nc.createVariable(varname=short, datatype='f4', dimensions=('time', 'lat', 'lon'))
                        new_nc[short][:] = variable.values
                        new_nc[short].units = variable.units
                        new_nc[short].long_name = variable.name
                        new_nc[short].gfs_level = level
                        new_nc[short].begin_date = timestamp
                        new_nc[short].axis = 'lat lon'
                    except:
                        pass
            new_nc.close()
            gribfile.close()

    # delete the gribs now that you're done with them triggering future runs to skip the download step
    shutil.rmtree(gribs)

    logging.info('Conversion Completed')
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
    logging.info('\nProcessing the netCDF files')

    # setting the environment file paths
    netcdfs = os.path.join(threddspath, timestamp, 'netcdfs')
    processed = os.path.join(threddspath, timestamp, 'processed')

    # if you already have processed netcdfs files, skip this and quit the function
    if not os.path.exists(netcdfs):
        logging.info('There are no netcdfs to be converted. Skipping netcdf processing.')
        return
    # otherwise, remove anything in the folder before starting (in case there was a partial processing)
    else:
        shutil.rmtree(processed)
        os.mkdir(processed)
        os.chmod(processed, 0o777)

    # list the files that need to be converted
    net_files = os.listdir(netcdfs)
    files = [file for file in net_files if file.endswith('.nc')]
    logging.info('There are ' + str(len(files)) + ' compatible files.')

    # read the first file that we'll copy data from in the next blocks of code
    logging.info('Preparing the reference file')
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
        logging.info('Working on file ' + str(file))
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

    logging.info('Finished File Conversions')
    return


def new_ncml(threddspath, timestamp):
    logging.info('\nWriting a new ncml file for this date')
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
    logging.info('Wrote New .ncml')
    return


# def grib_to_netcdf(threddspath, timestamp):
#     """
#     Description: Intended to make a THREDDS data server compatible netcdf file out of an incorrectly structured
#         netcdf file.
#     Author: Riley Hales, 2019
#     Dependencies: netCDF4, os, datetime
#     see github/rileyhales/hydroinformatics for more details
#     """
#     logging.info('\nStarting Grib Conversions')
#     # setting the environment file paths
#     gribs = os.path.join(threddspath, timestamp, 'gribs')
#     netcdfs = os.path.join(threddspath, timestamp, 'netcdfs')
#
#     # if you already have gfs netcdfs in the netcdfs folder, quit the function
#     if not os.path.exists(gribs):
#         logging.info('There are no gribs to convert, you must have already run this step. Skipping conversion')
#     # otherwise, remove anything in the folder before starting (in case there was a partial conversion)
#     else:
#         shutil.rmtree(netcdfs)
#         os.mkdir(netcdfs)
#         os.chmod(netcdfs, 0o777)
#
#     date = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
#
#     files = os.listdir(gribs)
#     grib_files = [grib for grib in files if grib.endswith('.grb')]
#     logging.info('There are ' + str(len(files)) + ' compatible files.')
#     time = 6
#
#     latitudes = [-90 + (i * .25) for i in range(721)]
#     longitudes = [-180 + (i * .25) for i in range(1440)]
#
#     for file in grib_files:
#         # create the new netcdf
#         ncname = file.replace('.grb', '.nc')
#         ncpath = os.path.join(netcdfs, ncname)
#         logging.info('creating netcdf file' + ncname)
#         newnetcdf = netCDF4.Dataset(ncpath, 'w', clobber=True, format='NETCDF4', diskless=False)
#         newnetcdf.createDimension('time', 1)
#         newnetcdf.createDimension('lat', 721)
#         newnetcdf.createDimension('lon', 1440)
#         newnetcdf.createVariable(varname='time', datatype='f4', dimensions='time')
#         newnetcdf['time'].axis = 'T'
#         newnetcdf.createVariable(varname='lat', datatype='f4', dimensions='lat')
#         newnetcdf['lat'].axis = 'lat'
#         newnetcdf.createVariable(varname='lon', datatype='f4', dimensions='lon')
#         newnetcdf['lon'].axis = 'lon'
#
#         begindate = date + datetime.timedelta(hours=time)
#         begindate = begindate.strftime("%Y%m%d%H")
#         time += 6
#
#         # set the value of the time variable data
#         newnetcdf['time'][:] = [time]
#         newnetcdf['time'].begin_date = begindate
#
#         # read a file to get the lat/lon variable data
#         gribpath = os.path.join(gribs, file)
#         obj = xarray.open_dataset(gribpath, engine='cfgrib', backend_kwargs={
#             'filter_by_keys': {'typeOfLevel': 'surface', 'cfVarName': 'vis'}})
#         # newnetcdf['lat'][:] = obj['latitude'].data
#         # newnetcdf['lon'][:] = obj['longitude'].data
#         newnetcdf['lat'][:] = latitudes
#         newnetcdf['lon'][:] = longitudes
#         obj.close()
#
#         for variable in gfs_variables().values():
#             logging.info('copying the data for variable ' + variable + ' to the netcdf')
#             newnetcdf.createVariable(varname=variable, datatype='f4', dimensions=('time', 'lat', 'lon'))
#             newnetcdf[variable].axis = 'lat lon'
#
#             gribpath = os.path.join(gribs, file)
#             obj = xarray.open_dataset(gribpath, engine='cfgrib', backend_kwargs={
#                 'filter_by_keys': {'typeOfLevel': 'surface', 'cfVarName': variable}})
#             newnetcdf[variable][:] = obj[variable].data
#             newnetcdf[variable].units = obj[variable].units
#             newnetcdf[variable].long_name = obj[variable].long_name
#             newnetcdf[variable].begin_date = begindate
#             obj.close()
#
#         logging.info('finished with this grib file\n')
#
#     # delete the gribs now that you're done with them triggering future runs to skip the download step
#     shutil.rmtree(gribs)
#
#     logging.info('Conversion Completed')
#     return


def new_ncml(threddspath, timestamp):
    logging.info('\nWriting a new ncml file for this date')
    # create a new ncml file by filling in the template with the right dates and writing to a file
    for level in gfs_forecastlevels():
        ncml = os.path.join(threddspath, level + '_wms.ncml')
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
                '        <scan location="' + timestamp + '/netcdfs/">\n'
                '           <filter wildcard="' + level + '_*"/>\n'
                '        </scan>\n'
                '    </aggregation>\n'
                '</netcdf>'
            )
        logging.info('Wrote New .ncml')
    return


# def set_wmsbounds(threddspath, timestamp):
#     logging.info('\nSetting new WMS bounds')
#     # setting the environment file paths
#     netcdfs = os.path.join(threddspath, timestamp, 'netcdfs')
#     bounds = {}
#
#     for item in gfs_variables():
#         variable = item[1]
#         logging.info('Checking the variable ' + variable)
#         maximum = -10000
#         minimum = 10000
#         for file in os.listdir(netcdfs):
#             path = os.path.join(netcdfs, file)
#             nc = netCDF4.Dataset(path, mode='r')
#             data = nc[variable][:]
#             tmp_max = numpy.amax(data)
#             tmp_min = numpy.amin(data)
#             if tmp_max > maximum:
#                 maximum = int(tmp_max)
#             if tmp_min < minimum:
#                 minimum = int(tmp_min)
#         bounds[variable] = str(minimum) + ',' + str(maximum)
#
#     boundsfile = os.path.join(os.path.dirname(__file__), 'public', 'js', 'bounds.js')
#     logging.info('the js file is at ' + boundsfile)
#     with open(boundsfile, 'w') as file:
#         file.write('const bounds = ' + str(bounds) + ';')
#     logging.info('wrote the js file')
#     return


def cleanup(threddspath, timestamp):
    # delete anything that isn't the new folder of data (named for the timestamp) or the new wms.ncml file
    logging.info('Getting rid of old data folders')
    files = os.listdir(threddspath)
    files.remove(timestamp)
    files = [file for file in files if not file.endswith('.ncml')]
    for file in files:
        try:
            shutil.rmtree(os.path.join(threddspath, file))
        except:
            os.remove(os.path.join(threddspath, file))
    logging.info('Done')
    return


def run_gfs_workflow():
    """
    The controller for running the workflow to download and process data
    """
    # start the workflow by setting the environment
    threddspath, wrksppath, timestamp, redundant = setenvironment()

    # if this has already been done for the most recent forecast, abort the workflow
    if redundant:
        logging.info('\nWorkflow aborted on ' + datetime.datetime.utcnow().strftime("%D at %R"))
        return 'Workflow Aborted- already run for most recent data'

    # run the workflow
    logging.info('\nBeginning to process on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    # download each forecast model, convert them to netcdfs
    succeeded = download_gfs(threddspath, timestamp)
    if not succeeded:
        return 'Workflow Aborted- Downloading Errors Occurred'
    grib_to_netcdf(threddspath, timestamp)
    nc_georeference(threddspath, timestamp)
    new_ncml(threddspath, timestamp)
    # set_wmsbounds(threddspath, timestamp)
    cleanup(threddspath, timestamp)

    logging.info('\nAll finished- writing the timestamp used on this run to a txt file')
    with open(os.path.join(wrksppath, 'timestamp.txt'), 'w') as file:
        file.write(timestamp)

    logging.info('\n\nGFS Workflow completed successfully on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    logging.info('If you have configured other models, they will begin processing now.\n\n\n')

    return 'GFS Workflow Completed- Normal Finish'
