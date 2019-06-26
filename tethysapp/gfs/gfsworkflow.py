import logging
import shutil
import xarray
import netCDF4
import requests
import numpy
import multiprocessing
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
    for filetype in ('gribs', 'netcdfs'):
        new_dir = os.path.join(threddspath, timestamp, filetype)
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir)
        os.mkdir(new_dir)
        os.chmod(new_dir, 0o777)

    logging.info('All done setting up folders, on to do work')
    return threddspath, wrksppath, timestamp, redundant


def new_download(fc_steps):
    now = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
    time = ''
    if now.hour >= 18:
        time = '18'
    elif now.hour >= 12:
        time = '12'
    elif now.hour >= 6:
        time = '06'
    elif now.hour >= 0:
        time = '00'
    timestamp = now.strftime("%Y%m%d") + time
    fc_date = now.strftime("%Y%m%d")
    configuration = app_settings()
    threddspath = configuration['threddsdatadir']
    gribsdir = os.path.join(threddspath, timestamp, 'gribs')

    for step in fc_steps:
        url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t' + time + 'z.pgrb2.0p25.f' + step + \
              '&all_lev=on&all_var=on&&dir=%2Fgfs.' + fc_date + '%2F' + time

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

    # This is the List of forecast timesteps for 5 days (6-hr increments). download them all
    fc_steps = ['006', '012', '018', '024', '030', '036', '042', '048', '054', '060', '066', '072', '078', '084',
                '090', '096', '102', '108', '114', '120', '126', '132', '138', '144', '150', '156', '162', '168']

    logging.info('ok imma start the multi stuff')
    pool = multiprocessing.Pool(processes=3)
    finished = pool.map(new_download, fc_steps)
    pool.close()
    pool.join()

    if len(finished) == sum(finished):
        # if they're all true (True = 1)
        return True
    else:
        return False


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

    files = os.listdir(gribs)
    grib_files = [grib for grib in files if grib.endswith('.grb')]
    logging.info('There are ' + str(len(files)) + ' compatible files.')

    for levels in gfs_forecastlevels():
        level = levels[1]
        logging.info('Working on converting files at the ' + level + ' level')
        for file in grib_files:
            gribpath = os.path.join(gribs, file)
            obj = xarray.open_dataset(gribpath, engine='cfgrib',
                                      backend_kwargs={'filter_by_keys': {'typeOfLevel': level}})
            ncfile = level + file.replace('.grb', '.nc')
            nc_path = os.path.join(netcdfs, ncfile)
            obj.to_netcdf(nc_path)

        logging.info('finished with this grib file\n')

    # delete the gribs now that you're done with them triggering future runs to skip the download step
    shutil.rmtree(gribs)

    logging.info('Conversion Completed')
    return


def new_ncml(threddspath, timestamp):
    logging.info('\nWriting a new ncml file for this date')
    # create a new ncml file by filling in the template with the right dates and writing to a file
    date = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
    date = datetime.datetime.strftime(date, "%Y-%m-%d %H:00:00")
    for levels in gfs_forecastlevels():
        level = levels[1]
        ncml = os.path.join(threddspath, level + '.ncml')
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
                '           <filter include="' + level + "*"
                '    </aggregation>\n'
                '</netcdf>'
            )
        logging.info('Wrote New .ncml')
    return


def set_wmsbounds(threddspath, timestamp):
    logging.info('\nSetting new WMS bounds')
    # setting the environment file paths
    netcdfs = os.path.join(threddspath, timestamp, 'netcdfs')
    bounds = {}

    for item in gfs_variables():
        variable = item[1]
        logging.info('Checking the variable ' + variable)
        maximum = -10000
        minimum = 10000
        for file in os.listdir(netcdfs):
            path = os.path.join(netcdfs, file)
            nc = netCDF4.Dataset(path, mode='r')
            data = nc[variable][:]
            tmp_max = numpy.amax(data)
            tmp_min = numpy.amin(data)
            if tmp_max > maximum:
                maximum = int(tmp_max)
            if tmp_min < minimum:
                minimum = int(tmp_min)
        bounds[variable] = str(minimum) + ',' + str(maximum)

    boundsfile = os.path.join(os.path.dirname(__file__), 'public', 'js', 'bounds.js')
    logging.info('the js file is at ' + boundsfile)
    with open(boundsfile, 'w') as file:
        file.write('const bounds = ' + str(bounds) + ';')
    logging.info('wrote the js file')
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
    set_wmsbounds(threddspath, timestamp)
    cleanup(threddspath, timestamp)

    logging.info('\nAll finished- writing the timestamp used on this run to a txt file')
    with open(os.path.join(wrksppath, 'timestamp.txt'), 'w') as file:
        file.write(timestamp)

    logging.info('\n\nGFS Workflow completed successfully on ' + datetime.datetime.utcnow().strftime("%D at %R"))
    logging.info('If you have configured other models, they will begin processing now.\n\n\n')

    return 'GFS Workflow Completed- Normal Finish'
