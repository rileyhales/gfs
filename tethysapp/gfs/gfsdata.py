import os
import shutil
import datetime
import urllib.request

from .options import app_configuration


def download_gfs(request):
    """

    :param request:
    :return:
    """
    # todo add a check here that determines if you have the most recent data by checking the times and folder name

    # download the most recently made gfs forecast
    threddsdir = app_configuration()['threddsdatadir']
    now = datetime.datetime.now()
    if now.hour > 1:
        forecastnumber = '00'
        forecast_date = str(now.strftime("%Y%m%d")) + forecastnumber
    elif now.hour > 7:
        forecastnumber = '06'
        forecast_date = str(now.strftime("%Y%m%d")) + forecastnumber
    elif now.hour > 13:
        forecastnumber = '12'
        forecast_date = str(now.strftime("%Y%m%d")) + forecastnumber
    elif now.hour > 19:
        forecastnumber = '18'
        forecast_date = str(now.strftime("%Y%m%d")) + forecastnumber
    else:
        # todo make this go back to the previous day's 18 forecast with timedelta
        forecastnumber = '00'
        forecast_date = str(now.strftime("%Y%m%d")) + forecastnumber



    # delete directory of old downloaded files, remake the directories
    shutil.rmtree(os.path.join(threddsdir, 'gribdownloads'))
    os.mkdir(os.path.join(threddsdir, 'gribdownloads'))
    downloadpath = os.path.join(threddsdir, 'gribdownloads', forecast_date)
    os.mkdir(downloadpath)

    # This is the List of forecast timesteps for 3 days (6-hr increments)
    t_steps = ['006', '012', '018', '024', '030', '036', '042', '048', '054', '060', '066', '072']
    for t_step in t_steps:
        # download each of the
        data_url = "https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t" + forecastnumber +"z.pgrb2.0p25.f" + t_step +\
                   "&all_lev=on&var_APCP=on&subregion=&leftlon=-180&rightlon=180&toplat=90&bottomlat=-90&dir=%2Fgfs." + forecast_date
        filename = "gfs_apcp_" + forecast_date + "_f" + t_step + ".grb"
        filepath = os.path.join(downloadpath, filename)
        urllib.request.urlretrieve(data_url, filepath)

    return


def grib_to_netcdf():
    # todo convert to netcdfs, set the wms bounds js
    files = app_configuration()['threddsdatadir']
    files = os.listdir(os.path.join(files, 'grib'))

    return
