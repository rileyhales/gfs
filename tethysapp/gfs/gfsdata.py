import datetime
import os
import shutil
import urllib.request
import xarray

from .options import app_configuration


def download_gfs():
    """
    Dependencies: os, shutil, datetime, urllib.request, app_configuration (options)
    """
    # download the most recently made gfs forecast (fc = forecast)
    threddsdir = app_configuration()['threddsdatadir']
    now = datetime.datetime.now()
    if now.hour > 19:
        fc_time = '18'
        fc_tstamp = str(now.strftime("%Y%m%d")) + fc_time
    elif now.hour > 13:
        fc_time = '12'
        fc_tstamp = str(now.strftime("%Y%m%d")) + fc_time
    elif now.hour > 7:
        fc_time = '06'
        fc_tstamp = str(now.strftime("%Y%m%d")) + fc_time
    elif now.hour > 1:
        fc_time = '00'
        fc_tstamp = str(now.strftime("%Y%m%d")) + fc_time
    else:
        # todo make this go back to the previous day's 18 forecast with timedelta
        fc_time = '00'
        fc_tstamp = str(now.strftime("%Y%m%d")) + fc_time
    print('determined the timestamp to download. it is ' + fc_tstamp)

    # if you already have a folder of data for this timestep, quit this function (you dont need to download it)
    if os.path.exists(os.path.join(threddsdir, 'gribs', fc_tstamp)):
        print('you already have the most recent data. skipping downloads')
        return fc_tstamp

    # delete directory of old downloaded files, remake the directories
    print('deleting old data')
    shutil.rmtree(os.path.join(threddsdir, 'gribs'))
    os.mkdir(os.path.join(threddsdir, 'gribs'))
    downloadpath = os.path.join(threddsdir, 'gribs', fc_tstamp)
    os.mkdir(downloadpath)

    # This is the List of forecast timesteps for 2 days (6-hr increments)
    t_steps = ['006', '012', '018', '024']
    for step in t_steps:
        url = 'https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t' + fc_time + 'z.pgrb2.0p25.f' + step +\
              "&all_lev=on&all_var=on&subregion=&leftlon=-180&rightlon=180&toplat=90&bottomlat=-90&dir=%2Fgfs." + fc_tstamp
        filename = 'gfs_' + fc_tstamp + '_' + step + '.grb'
        print('downloading the file ' + filename)
        filepath = os.path.join(downloadpath, filename)
        urllib.request.urlretrieve(url, filepath)

    return fc_tstamp


def grib_to_netcdf(fc_tstamp):
    # todo convert to netcdfs, set the wms bounds js
    thredds = app_configuration()['threddsdatadir']
    gribs = os.path.join(thredds, 'gribs', fc_tstamp)
    ncfolder = os.path.join(thredds, 'netcdfs')
    if os.path.exists(os.path.join(ncfolder, fc_tstamp)):
        print('you already converted them to nc files. skipping this step')
        return
    shutil.rmtree(ncfolder)
    os.mkdir(ncfolder)
    os.mkdir(os.path.join(ncfolder, fc_tstamp))

    files = os.listdir(gribs)
    files = [grib for grib in files if grib.endswith('.grb')]
    for file in files:
        path = os.path.join(gribs, file)
        print('opening grib file ' + path)
        obj = xarray.open_dataset(path, engine='cfgrib', backend_kwargs={'filter_by_keys': {'typeOfLevel': 'surface'}})
        print('converting it to a netcdf')
        ncname = file.replace('gfs_', '').replace('.grb', '')
        ncpath = os.path.join(ncfolder, fc_tstamp, 'gfs_' + ncname + '.nc')
        obj.to_netcdf(ncpath, mode='w')
        print('converted. next file...')
    print('finished')

    return
