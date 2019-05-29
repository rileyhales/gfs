from .app import Gfs as App
import os
import datetime


def app_configuration():
    """
    Gets the settings for the app for use in other functions and ajax for leaflet
    Dependencies: os, App (app)
    """
    return {
        'app_wksp_path': os.path.join(App.get_app_workspace().path, ''),
        'threddsdatadir': App.get_custom_setting("Local Thredds Folder Path"),
        'threddsurl': App.get_custom_setting("Thredds WMS URL"),
        'geoserverurl': App.get_custom_setting("Geoserver Workspace URL"),
    }


def gfs_variables():
    """
    List of the plottable variables from the GFS model
    """
    return {
        'Albedo': 'al',
        'Best (4-layer) lifted index': '4lftx',
        'Categorical freezing rain': 'cfrzr',
        'Categorical ice pellets': 'cicep',
        'Categorical rain': 'crain',
        'Categorical snow': 'csnow',
        'Convective available potential energy': 'cape',
        'Convective inhibition': 'cin',
        'Convective precipitation (water)': 'acpcp',
        'Convective precipitation rate': 'cprat',
        'Downward long-wave radiation flux': 'dlwrf',
        'Downward short-wave radiation flux': 'dswrf',
        'Field capacity': 'fldcp',
        'Land-sea coverage (nearest neighbor) [land=1,sea=0]': 'landn',
        'Land-sea mask': 'lsm',
        'Latent heat net flux': 'lhtfl',
        'Meridional flux of gravity wave stress': 'v-gwd',
        'Momentum flux, u component': 'uflx',
        'Momentum flux, v component': 'vflx',
        'Orography': 'orog',
        'Percent frozen precipitation': 'cpofp',
        'Planetary boundary layer height': 'hpbl',
        'Potential evaporation rate': 'pevpr',
        'Precipitation rate': 'prate',
        'Sea ice area fraction': 'siconc',
        'Sensible heat net flux': 'shtfl',
        'Snow depth': 'sde',
        'Sunshine duration': 'SUNSD',
        'Surface lifted index': 'lftx',
        'Surface pressure': 'sp',
        'Temperature': 't',
        'Total precipitation': 'tp',
        'Upward long-wave radiation flux': 'ulwrf',
        'Upward short-wave radiation flux': 'uswrf',
        'Visibility': 'vis',
        'Water equivalent of accumulated snow depth': 'sdwe',
        'Water runoff': 'watr',
        'Wilting point': 'wilt',
        'Wind speed (gust)': 'gust',
        'Zonal flux of gravity wave stress': 'u-gwd'
        # 'Initial time of forecast': 'time',
        # 'Ground heat flux': 'gflux',
        # 'Haines index': 'hindex',
        # 'Original grib coordinate for key: level(surface)': 'surface',
        # 'Time': 'valid_time',
        # 'Time since forecast reference time': 'step',
        # 'Latitude': 'latitude',
        # 'Longitude': 'longitude',
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
    gfspath = App.get_custom_setting("Local Thredds Folder Path")
    gfs = os.listdir(os.path.join(gfspath))
    gfs = [n for n in gfs if n.startswith('20')]
    if len(gfs) > 0:
        gfs = datetime.datetime.strptime(gfs[0], "%Y%m%d%H")
        return "This GFS data from " + datetime.datetime.strftime(gfs, "%b %d, %I%p UTC")  # Month Day at Hour am/pm
    return "No GFS data detected"
