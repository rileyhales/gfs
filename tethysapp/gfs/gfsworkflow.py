import logging
import shutil
import xarray
import netCDF4
import requests

from .options import *


def setenvironment():
    """
    Dependencies: os, shutil, datetime, urllib.request, app_settings (options)
    """
    logging.info('\nSetting the Environment for the GFS Workflow')
    # determine the most day and hour of the day timestamp of the most recent GFS forecast
    now = datetime.datetime.utcnow()
    if now.hour > 21:
        timestamp = now.strftime("%Y%m%d") + '18'
    elif now.hour > 15:
        timestamp = now.strftime("%Y%m%d") + '06'
    elif now.hour > 9:
        timestamp = now.strftime("%Y%m%d") + '06'
    elif now.hour > 3:
        timestamp = now.strftime("%Y%m%d") + '00'
    else:
        now = now - datetime.timedelta(days=1)
        timestamp = now.strftime("%Y%m%d") + '18'
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
    for filetype in ('gribs', 'netcdfs'):
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
    elif len(os.listdir(gribsdir)) >= 28:
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
    fc_steps = ['006', '012', '018', '024', '030', '036', '042', '048', '054', '060', '066', '072', '078', '084',
                '090', '096', '102', '108', '114', '120', '126', '132', '138', '144', '150', '156', '162', '168']

    for step in fc_steps:
        url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t' + time + 'z.pgrb2.0p25.f' + step + \
              '&lev_surface=on&all_var=on&&dir=%2Fgfs.' + fc_date + '%2F' + time

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
            errorcode = e.response.status_code
            logging.info('\nHTTPError ' + str(errorcode) + ' downloading ' + filename + ' from\n' + url)
            if errorcode == 404:
                logging.info('The file was not found on the server, trying an older forecast time')
            elif errorcode == 500:
                logging.info('Probably a problem with the URL. Check the log and try the link')
            return False
    logging.info('Finished Downloads')
    return True


def grib_to_netcdf(threddspath, timestamp):
    """
    Description: Intended to make a THREDDS data server compatible netcdf file out of an incorrectly structured
        netcdf file.
    Author: Riley Hales, 2019
    Dependencies: netCDF4, os, datetime
    see github/rileyhales/hydroinformatics for more details
    """
    logging.info('\nStarting Grib Conversions')
    # setting the environment file paths
    gribs = os.path.join(threddspath, timestamp, 'gribs')
    netcdfs = os.path.join(threddspath, timestamp, 'netcdfs')

    # if you already have gfs netcdfs in the netcdfs folder, quit the function
    if not os.path.exists(gribs):
        logging.info('There are no gribs to convert, you must have already run this step. Skipping conversion')
    # otherwise, remove anything in the folder before starting (in case there was a partial conversion)
    else:
        shutil.rmtree(netcdfs)
        os.mkdir(netcdfs)
        os.chmod(netcdfs, 0o777)

    date = datetime.datetime.strptime(timestamp, "%Y%m%d%H")

    files = os.listdir(gribs)
    grib_files = [grib for grib in files if grib.endswith('.grb')]
    logging.info('There are ' + str(len(files)) + ' compatible files.')
    time = 6

    latitudes = [-90 + (i * .25) for i in range(721)]
    longitudes = [-180 + (i * .25) for i in range(1440)]

    for file in grib_files:
        # create the new netcdf
        ncname = file.replace('.grb', '.nc')
        ncpath = os.path.join(netcdfs, ncname)
        logging.info('creating netcdf file' + ncname)
        newnetcdf = netCDF4.Dataset(ncpath, 'w', clobber=True, format='NETCDF4', diskless=False)
        newnetcdf.createDimension('time', 1)
        newnetcdf.createDimension('lat', 721)
        newnetcdf.createDimension('lon', 1440)
        newnetcdf.createVariable(varname='time', datatype='f4', dimensions='time')
        newnetcdf['time'].axis = 'T'
        newnetcdf.createVariable(varname='lat', datatype='f4', dimensions='lat')
        newnetcdf['lat'].axis = 'lat'
        newnetcdf.createVariable(varname='lon', datatype='f4', dimensions='lon')
        newnetcdf['lon'].axis = 'lon'

        begindate = date + datetime.timedelta(hours=time)
        begindate = begindate.strftime("%Y%m%d%H")
        time += 6

        # set the value of the time variable data
        newnetcdf['time'][:] = [time]
        newnetcdf['time'].begin_date = begindate

        # read a file to get the lat/lon variable data
        gribpath = os.path.join(gribs, file)
        obj = xarray.open_dataset(gribpath, engine='cfgrib', backend_kwargs={
            'filter_by_keys': {'typeOfLevel': 'surface', 'cfVarName': 'vis'}})
        # newnetcdf['lat'][:] = obj['latitude'].data
        # newnetcdf['lon'][:] = obj['longitude'].data
        newnetcdf['lat'][:] = latitudes
        newnetcdf['lon'][:] = longitudes
        obj.close()

        for variable in gfs_variables().values():
            logging.info('copying the data for variable ' + variable + ' to the netcdf')
            newnetcdf.createVariable(varname=variable, datatype='f4', dimensions=('time', 'lat', 'lon'))
            newnetcdf[variable].axis = 'lat lon'

            gribpath = os.path.join(gribs, file)
            obj = xarray.open_dataset(gribpath, engine='cfgrib', backend_kwargs={
                'filter_by_keys': {'typeOfLevel': 'surface', 'cfVarName': variable}})
            newnetcdf[variable][:] = obj[variable].data
            newnetcdf[variable].units = obj[variable].units
            newnetcdf[variable].long_name = obj[variable].long_name
            newnetcdf[variable].begin_date = begindate
            obj.close()

        logging.info('finished with this grib file\n')

    # delete the gribs now that you're done with them triggering future runs to skip the download step
    shutil.rmtree(gribs)

    logging.info('Conversion Completed')
    return


def new_ncml(threddspath, timestamp):
    logging.info('\nWriting a new ncml file for this date')
    # create a new ncml file by filling in the template with the right dates and writing to a file
    ncml = os.path.join(threddspath, 'wms.ncml')
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
            '        <scan location="' + timestamp + '/netcdfs/"/>\n'
            '    </aggregation>\n'
            '</netcdf>'
        )
    logging.info('Wrote New .ncml')
    return


def cleanup(threddspath, timestamp):
    # delete anything that isn't the new folder of data (named for the timestamp) or the new wms.ncml file
    logging.info('Getting rid of old data folders')
    files = os.listdir(threddspath)
    files.remove(timestamp)
    files.remove('wms.ncml')
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
    # enable logging to track the progress of the workflow and for debugging
    # logging.basicConfig(filename=app_settings()['logfile'], filemode='w', level=logging.INFO, format='%(message)s')
    # logging.info('Workflow initiated on ' + datetime.datetime.utcnow().strftime("%D at %R"))

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
    new_ncml(threddspath, timestamp)
    cleanup(threddspath, timestamp)

    logging.info('\nAll finished- writing the timestamp used on this run to a txt file')
    with open(os.path.join(wrksppath, 'timestamp.txt'), 'w') as file:
        file.write(timestamp)

    logging.info('\n\nGFS Workflow completed successfully on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    logging.info('If you have configured other models, they will begin processing now.\n\n\n')

    return 'GFS Workflow Completed- Normal Finish'
