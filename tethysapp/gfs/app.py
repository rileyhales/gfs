from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import CustomSetting


class Gfs(TethysAppBase):
    """
    Tethys app class for GFS Visualization Tool.
    """

    name = 'GFS Visualization Tool'
    index = 'gfs:home'
    icon = 'gfs/images/gfs.png'
    package = 'gfs'
    root_url = 'gfs'
    color = '#013220'
    description = 'Downloads the most recent GFS forecast and processes it from grib to WMS compliant netCDF.\n' \
                  'Visualizes the GFS forecasts through time-animated maps.\n' \
                  'Generates timeseries charts and datasets at points or averaged over polygons.\n'
    tags = ''
    enable_feedback = False
    feedback_emails = []
    githublink = 'https://github.com/rileyhales/gfs'
    datawebsite = 'https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/global-forcast-system-gfs'
    version = 'v2 7/2019'

    def url_maps(self):
        """
        Add controllers
        """
        urlmap = url_map_maker(self.root_url)

        # url maps to navigable pages
        url_maps = (
            urlmap(
                name='home',
                url='gfs',
                controller='gfs.controllers.home'
            ),

            # url maps for data processing workflow
            urlmap(
                name='runWorkflows',
                url='gfs/runWorkflows',
                controller='gfs.controllers.run_workflows'
            ),

            # url maps for ajax calls
            urlmap(
                name='getLevelsForVar',
                url='gfs/ajax/getLevelsForVar',
                controller='gfs.ajax.get_levels_for_variable'
            ),
            urlmap(
                name='getChart',
                url='gfs/ajax/getChart',
                controller='gfs.ajax.getchart',
            ),
            urlmap(
                name='uploadShapefile',
                url='gfs/ajax/uploadShapefile',
                controller='gfs.ajax.uploadshapefile',
            ),

            # url maps for api calls
            urlmap(
                name='getcapabilities',
                url='gfs/api/getcapabilities',
                controller='gfs.api.getcapabilities',
            ),
            urlmap(
                name='timeseries',
                url='gfs/api/timeseries',
                controller='gfs.api.timeseries',
            ),
            urlmap(
                name='gfslevels',
                url='gfs/api/gfslevels',
                controller='gfs.api.gfslevels',
            ),
            urlmap(
                name='gfsdates',
                url='gfs/api/gfsdates',
                controller='gfs.api.gfsdates',
            ),
        )
        return url_maps

    def custom_settings(self):
        CustomSettings = (
            CustomSetting(
                name='Local Thredds Folder Path',
                type=CustomSetting.TYPE_STRING,
                description="Local file path to datasets (same as used by Thredds) (e.g. /home/thredds/myDataFolder/)",
                required=True,
            ),
            CustomSetting(
                name='Thredds WMS URL',
                type=CustomSetting.TYPE_STRING,
                description="URL to the GLDAS folder on the thredds server (e.g. http://[host]/thredds/gfs/)",
                required=True,
            ),
            CustomSetting(
                name='GeoserverURL',
                type=CustomSetting.TYPE_STRING,
                description="Include http or https but no '/' after /geoserver, ex: https://tethys.byu.edu/geoserver",
                required=False,
            ),
            CustomSetting(
                name='Geoserver user/pass',
                type=CustomSetting.TYPE_STRING,
                description="Admin credentials for uploading shapefiles to geoserver in the format username/password",
                required=False,
            ),
        )
        return CustomSettings

