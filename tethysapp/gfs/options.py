from .app import Gfs as App
import os
import datetime


def app_settings():
    """
    Gets the settings for the app for use in other functions and ajax for leaflet
    Dependencies: os, App (app)
    """
    return {
        'app_wksp_path': os.path.join(App.get_app_workspace().path, ''),
        'threddsdatadir': App.get_custom_setting("Local Thredds Folder Path"),
        'threddsurl': App.get_custom_setting("Thredds WMS URL"),
        'geoserverurl': App.get_custom_setting("Geoserver Workspace URL"),
        'timestamp': gettimestamp(),
        'logfile': os.path.join(App.get_app_workspace().path, 'workflow.log')
    }


def gettimestamp():
    with open(os.path.join(App.get_app_workspace().path, 'timestamp.txt'), 'r') as file:
        return file.read()


def gfs_variables():
    """
    List of the plottable variables from the GFS model
    """
    return {
        'Temperature': 't',
        'Albedo': 'al',
        'Convective precipitation (water)': 'acpcp',
        'Convective precipitation rate': 'cprat',
        'Latent heat net flux': 'lhtfl',
        'Momentum flux, u component': 'uflx',
        'Momentum flux, v component': 'vflx',
        'Percent frozen precipitation': 'cpofp',
        'Sea ice area fraction': 'siconc',
        'Sensible heat net flux': 'shtfl',
        'Snow depth': 'sde',
        'Surface pressure': 'sp',
        'Visibility': 'vis',
        'Water equivalent of accumulated snow depth': 'sdwe',
        'Water runoff': 'watr',
        'Wind speed (gust)': 'gust',
    }


def wms_colors():
    """
    Color options usable by thredds wms
    """
    return [
        ('SST-36', 'sst_36'),
        ('Greyscale', 'greyscale'),
        ('Rainbow', 'rainbow'),
        ('OCCAM', 'occam'),
        ('OCCAM Pastel', 'occam_pastel-30'),
        ('Red-Blue', 'redblue'),
        ('NetCDF Viewer', 'ncview'),
        ('ALG', 'alg'),
        ('ALG 2', 'alg2'),
        ('Ferret', 'ferret'),
    ]


def geojson_colors():
    return [
        ('Transparent', 'rgb(0,0,0,0)'),
        ('White', '#ffffff'),
        ('Red', '#ff0000'),
        ('Green', '#00ff00'),
        ('Blue', '#0000ff'),
        ('Black', '#000000'),
        ('Pink', '#ff69b4'),
        ('Orange', '#ffa500'),
        ('Teal', '#008080'),
        ('Purple', '#800080'),
    ]


def currentgfs():
    # if there is actually data in the app, then read the file with the timestamp on it
    path = App.get_custom_setting("Local Thredds Folder Path")
    timestamp = gettimestamp()
    path = os.path.join(path, timestamp)
    if os.path.exists(path):
        timestamp = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
        return "This GFS data from " + datetime.datetime.strftime(timestamp, "%b %d, %I%p UTC")
    return "No GFS data detected"
