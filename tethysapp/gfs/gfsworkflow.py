import logging
import shutil

import netCDF4
import requests

from .options import *


def setenvironment():
    """
    Dependencies: os, shutil, datetime, urllib.request, app_configuration (options)
    """
    logging.info('\nSetting the Environment')
    # determine the most day and hour of the day timestamp of the most recent GFS forecast
    now = datetime.datetime.utcnow()
    if now.hour > 19:
        timestamp = now.strftime("%Y%m%d") + '06'
    elif now.hour > 13:
        timestamp = now.strftime("%Y%m%d") + '12'
    elif now.hour > 7:
        timestamp = now.strftime("%Y%m%d") + '06'
    elif now.hour > 1:
        timestamp = now.strftime("%Y%m%d") + '00'
    else:
        now = now - datetime.timedelta(days=1)
        timestamp = now.strftime("%Y%m%d") + '18'
    logging.info('determined the timestamp to download: ' + timestamp)

    # set folder paths for the environment
    configuration = app_configuration()
    threddspath = configuration['threddsdatadir']
    wrksppath = configuration['app_wksp_path']

    # perform a redundancy check, if the last timestamp is the same as current, abort the workflow
    timefile = os.path.join(wrksppath, 'timestamp.txt')
    with open(timefile, 'r') as file:
        lasttime = file.readline()
        if lasttime == timestamp:
            redundant = True
            logging.info('The last recorded timestamp is the timestamp we determined, aborting workflow')
            return threddspath, wrksppath, timestamp, redundant
        else:
            redundant = False

    # if the file structure already exists, quit
    chk = os.path.join(wrksppath, 'global', 'GeoTIFFs_resampled')
    if os.path.exists(chk):
        logging.info('You have a file structure for this timestep but didnt complete the workflow, analyzing...')
        return threddspath, wrksppath, timestamp, redundant

    # create the file structure and their permissions for the new data
    logging.info('Creating APP WORKSPACE (GeoTIFF) file structure for ' )
    new_dir = os.path.join(wrksppath, 'GeoTIFFs')
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.mkdir(new_dir)
    os.chmod(new_dir, 0o777)
    new_dir = os.path.join(wrksppath, 'GeoTIFFs_resampled')
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.mkdir(new_dir)
    os.chmod(new_dir, 0o777)
    logging.info('Creating THREDDS file structure for ' )
    new_dir = os.path.join(threddspath, 'gfs')
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.mkdir(new_dir)
    os.chmod(new_dir, 0o777)
    new_dir = os.path.join(threddspath, 'gfs', timestamp)
    if os.path.exists(new_dir):
        shutil.rmtree(new_dir)
    os.mkdir(new_dir)
    os.chmod(new_dir, 0o777)
    for filetype in ('gribs', 'netcdfs', 'processed'):
        new_dir = os.path.join(threddspath, 'gfs', timestamp, filetype)
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        os.mkdir(new_dir)
        os.chmod(new_dir, 0o777)

    logging.info('All done setting up folders, on to do work')
    return threddspath, wrksppath, timestamp, redundant


def download_gfs(threddspath, timestamp):
    logging.info('\nStarting GFS Grib Downloads for ' )
    # set filepaths
    gribsdir = os.path.join(threddspath, 'gfs', timestamp, 'gribs')

    # if you already have a folder with data for this timestep, quit this function (you dont need to download it)
    if not os.path.exists(gribsdir):
        logging.info('There is no download folder, you must have already processed them. Skipping download stage.')
        return
    elif len(os.listdir(gribsdir)) >= 40:
        logging.info('There are already 40 forecast steps in here. Dont need to download them')
        return
    # otherwise, remove anything in the folder before starting (in case there was a partial download)
    else:
        shutil.rmtree(gribsdir)
        os.mkdir(gribsdir)
        os.chmod(gribsdir, 0o777)

    # # get the parts of the timestamp to put into the url
    time = datetime.datetime.strptime(timestamp, "%Y%m%d%H").strftime("%H")
    fc_date = datetime.datetime.strptime(timestamp, "%Y%m%d%H").strftime("%Y%m%d")

    # This is the List of forecast timesteps for 5 days (6-hr increments). download them all
    fc_steps = ['006', '012', '018', '024', '030', '036', '042', '048', '054', '060', '066', '072', '078', '084',
                '090', '096', '102', '108', '114', '120', '126', '132', '138', '144', '150', '156', '162', '168']

    # this is where the actual downloads happen. set the url, filepath, then download
    subregions = {
        'global': 'subregion=&leftlon=-180&rightlon=180&toplat=90&bottomlat=-90',
    }
    for step in fc_steps:
        url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t' + time + 'z.pgrb2.0p25.f' + step + \
              '&all_lev=on&all_var=on&' + subregions['global'] + '&dir=%2Fgfs.' + fc_date + '%2F' + time

        fc_timestamp = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
        file_timestep = fc_timestamp + datetime.timedelta(hours=int(step))
        filename_timestep = datetime.datetime.strftime(file_timestep, "%Y%m%d%H")

        filename = filename_timestep + '.grb'
        logging.info('downloading the file ' + filename)
        filepath = os.path.join(gribsdir, filename)
        try:
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
        except requests.HTTPError as e:
            logging.info('\nHTTPError ' + str(e.response.status_code) + ' downloading ' + filename + ' from\n' + url)
            return False

    logging.info('Finished Downloads')
    return


def nc_georeference(threddspath, timestamp):
    """
    Description: Intended to make a THREDDS data server compatible netcdf file out of an incorrectly structured
        netcdf file.
    Author: Riley Hales, 2019
    Dependencies: netCDF4, os, datetime
    see github/rileyhales/datatools for more details
    """
    logging.info('\nProcessing the netCDF files')

    # setting the environment file paths
    netcdfs = os.path.join(threddspath, 'gfs', timestamp, 'netcdfs')
    processed = os.path.join(threddspath, 'gfs', timestamp, 'processed')

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
        duplicate['lat'][:] = original['latitude'][:]
        duplicate['lon'][:] = original['longitude'][:]

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
    ncml = os.path.join(threddspath, 'gfs', 'wms.ncml')
    date = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
    date = datetime.datetime.strftime(date, "%Y-%m-%d %H:00:00")
    with open(ncml, 'w') as file:
        file.write(
            '<netcdf xmlns="http://www.unidata.ucar.edu/namespaces/netcdf/ncml-2.2">\n'
            '    <variable name="time" type="int" shape="time">\n'
            '        <attribute name="units" value="hours since ' + date + '"/>\n'
                                                                           '        <attribute name="_CoordinateAxisType" value="Time" />\n'
                                                                           '        <values start="6" increment="6" />\n'
                                                                           '    </variable>\n'
                                                                           '    <aggregation dimName="time" type="joinExisting" recheckEvery="1 hour">\n'
                                                                           '        <scan location="' + timestamp + '/processed/"/>\n'
                                                                                                                    '    </aggregation>\n'
                                                                                                                    '</netcdf>'
        )
    logging.info('Wrote New .ncml')
    return


def cleanup(threddspath, timestamp):
    # write a file with the current timestep triggering the app to start using this data

    # delete anything that isn't the new folder of data (named for the timestamp) or the new wms.ncml file
    logging.info('Getting rid of old gfs data folders')
    path = os.path.join(threddspath, 'gfs')
    files = os.listdir(path)
    files.remove(timestamp)
    files.remove('wms.ncml')
    for file in files:
        try:
            shutil.rmtree(os.path.join(path, file))
        except:
            os.remove(os.path.join(path, file))

    logging.info('Done')
    return


def run_gfs_workflow():
    """
    The controller for running the workflow to download and process data
    """
    # enable logging to track the progress of the workflow and for debugging
    logging.basicConfig(filename=app_configuration()['logfile'], filemode='w', level=logging.INFO, format='%(message)s')
    logging.info('Workflow initiated on ' + datetime.datetime.utcnow().strftime("%D at %R"))

    # start the workflow by setting the environment
    threddspath, wrksppath, timestamp, redundant = setenvironment()

    # if this has already been done for the most recent forecast, abort the workflow
    if redundant:
        logging.info('\nWorkflow aborted on ' + datetime.datetime.utcnow().strftime("%D at %R"))
        return 'Workflow Aborted: already run for most recent data'

    # run the workflow
    logging.info('\nBeginning to process '  + ' on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    # download each forecast model, convert them to netcdfs and tiffs
    succeed = download_gfs(threddspath, timestamp)
    if not succeed:
        return 'Workflow Aborted: errors occurred downloading files, consult the log'
    nc_georeference(threddspath, timestamp)
    # generate color scales and ncml aggregation files
    new_ncml(threddspath, timestamp)
    # cleanup the workspace by removing old files
    cleanup(threddspath, wrksppath, timestamp)

    logging.info('\n        All regions and models finished- writing the timestamp used on this run to a txt file')
    with open(os.path.join(wrksppath, 'timestamp.txt'), 'w') as file:
        file.write(timestamp)

    logging.info('\nWorkflow completed successfully on ' + datetime.datetime.utcnow().strftime("%D at %R"))

    return 'Workflow Completed: Normal Finish'
