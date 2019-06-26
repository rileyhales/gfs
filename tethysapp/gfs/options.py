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


def gfs_forecastlevels():
    return [
        # ('Height Above Ground', 'heightAboveGround'),
        ('Height Above Sea', 'heightAboveSea'),
        ('Hybrid', 'hybrid'),
        # ('Isobaric (hPa)', 'isobaricInhPa'),
        ('Isotherm Zero', 'isothermZero'),
        ('Max Wind', 'maxWind'),
        ('Mean Sea Level', 'meanSea'),
        ('Other', 'unknown'),
        ('Potential Vorticity', 'potentialVorticity'),
        # ('Pressure From Ground Layer', 'pressureFromGroundLayer'),
        ('Sigma', 'sigma'),
        ('Sigma Layer', 'sigmaLayer'),
        ('Surface', 'surface'),
        ('Tropopause', 'tropopause'),
    ]


def gfs_variables():
    return [
        ('Best (4-layer) lifted index', '4lftx'), ('Convective available potential energy', 'cape'),
        ('Convective inhibition', 'cin'), ('Cloud mixing ratio', 'clwmr'), ('Cloud water', 'cwat'),
        ('Geopotential Height', 'gh'), ('Graupel (snow pellets)', 'grle'), ('hybrid level', 'hybrid'),
        ('ICAO Standard Atmosphere reference height', 'icaht'), ('Ice water mixing ratio', 'icmr'),
        ('Surface lifted index', 'lftx'), ('Mean Sea Level Pressure (Eta model reduction)', 'mslet'),
        ('Orography', 'orog'), ('Precipitation rate', 'prate'), ('Pressure', 'pres'),
        ('Pressure reduced to MSL', 'prmsl'), ('Potential temperature', 'pt'), ('Precipitable water', 'pwat'),
        ('Relative humidity', 'r'), ('Rain mixing ratio', 'rwmr'), ('Snow mixing ratio', 'snmr'),
        ('Surface pressure', 'sp'), ('Temperature', 't'), ('Total ozone', 'tozne'), ('U component of wind', 'u'),
        ('V component of wind', 'v'), ('Vertical speed shear', 'vwsh'), ('Vertical velocity', 'w')
    ]


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


def structure():
    return {
        'heightAboveSea': [('Temperature', 't'), ('U component of wind', 'u'), ('V component of wind', 'v')],
        'hybrid': [('Cloud mixing ratio', 'clwmr'), ('Graupel (snow pellets)', 'grle'), ('hybrid level', 'hybrid'),
                   ('Ice water mixing ratio', 'icmr'), ('Rain mixing ratio', 'rwmr'), ('Snow mixing ratio', 'snmr')],
        'isothermZero': [('Geopotential Height', 'gh'), ('Relative humidity', 'r')],
        'maxWind': [('Geopotential Height', 'gh'), ('ICAO Standard Atmosphere reference height', 'icaht'),
                    ('Pressure', 'pres'), ('Temperature', 't'), ('U component of wind', 'u'),
                    ('V component of wind', 'v')],
        'meanSea': [('Mean Sea Level Pressure (Eta model reduction)', 'mslet'), ('Pressure reduced to MSL', 'prmsl')],
        'potentialVorticity': [('Geopotential Height', 'gh'), ('Pressure', 'pres'), ('Temperature', 't'),
                               ('U component of wind', 'u'), ('V component of wind', 'v'),
                               ('Vertical speed shear', 'vwsh')],
        'sigma': [('Potential temperature', 'pt'), ('Relative humidity', 'r'), ('Temperature', 't'),
                  ('U component of wind', 'u'), ('V component of wind', 'v'), ('Vertical velocity', 'w')],
        'sigmaLayer': [('Relative humidity', 'r')],
        'surface': [('Best (4-layer) lifted index', '4lftx'), ('Convective available potential energy', 'cape'),
                    ('Convective inhibition', 'cin'), ('Surface lifted index', 'lftx'), ('Orography', 'orog'),
                    ('Precipitation rate', 'prate'), ('Surface pressure', 'sp')],
        'tropopause': [('Geopotential Height', 'gh'), ('ICAO Standard Atmosphere reference height', 'icaht'),
                       ('Pressure', 'pres'), ('Temperature', 't'), ('U component of wind', 'u'),
                       ('V component of wind', 'v'), ('Vertical speed shear', 'vwsh')],
        'unknown': [('Cloud water', 'cwat'), ('Geopotential Height', 'gh'), ('Precipitable water', 'pwat'),
                    ('Relative humidity', 'r'), ('Total ozone', 'tozne')]}
