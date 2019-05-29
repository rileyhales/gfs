from tethys_sdk.base import TethysAppBase, url_map_maker
from tethys_sdk.app_settings import CustomSetting


class Gfs(TethysAppBase):
    """
    Tethys app class for GFS Visualizer Tool.
    """

    name = 'GFS Visualizer Tool'
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
    youtubelink = 'https://youtube.com'
    githublink = 'https://github.com/rileyhales/gfs'
    gfslink = 'https://www.ncdc.noaa.gov/data-access/model-data/model-datasets/global-forcast-system-gfs'
    version = 'v1.1 - 29 May 2019'

    def url_maps(self):
        """
        Add controllers
        """
        UrlMap = url_map_maker(self.root_url)

        # url maps to navigable pages
        url_maps = (
            UrlMap(
                name='home',
                url='gfs',
                controller='gfs.controllers.home'
            ),

            # url maps for ajax calls
            UrlMap(
                name='getCustomSettings',
                url='gfs/ajax/getCustomSettings',
                controller='gfs.ajax.get_customsettings'
            ),
            UrlMap(
                name='getPointSeries',
                url='gfs/ajax/getPointSeries',
                controller='gfs.ajax.get_pointseries',
            ),
            UrlMap(
                name='getPolygonAverage',
                url='gfs/ajax/getPolygonAverage',
                controller='gfs.ajax.get_polygonaverage',
            ),
            UrlMap(
                name='getShapeAverage',
                url='gfs/ajax/getShapeAverage',
                controller='gfs.ajax.get_shapeaverage',
            ),
            UrlMap(
                name='updateGFS',
                url='gfs/update',
                controller='gfs.ajax.get_newgfsdata'
            )

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
                name='Geoserver Workspace URL',
                type=CustomSetting.TYPE_STRING,
                description="URL (wfs) of the workspace on geoserver (e.g. https://[host]/geoserver/gfs/ows). \n"
                            "Enter geojson instead of a url if you experience GeoServer problems.",
                required=True,
            ),
        )
        return CustomSettings

