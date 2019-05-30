import ast

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .options import *
from .tools import shpchart, pointchart, polychart
from .gfsdata import *


@login_required()
def get_pointseries(request):
    """
    Used to make a timeseries of a variable at a user drawn point
    Dependencies: gldas_variables (options), pointchart (tools), ast, makestatplots (tools)
    """
    data = ast.literal_eval(request.body.decode('utf-8'))
    data = pointchart(data)
    data['type'] = '(Values at a Point)'

    variables = gfs_variables()
    for key in variables:
        if variables[key] == data['variable']:
            name = key
            data['name'] = name
            break
    return JsonResponse(data)


@login_required()
def get_polygonaverage(request):
    """
    Used to do averaging of a variable over a user drawn box of area
    Dependencies: polychart (tools), gldas_variables (options), ast, makestatplots (tools)
    """
    data = ast.literal_eval(request.body.decode('utf-8'))
    data = polychart(data)
    data['type'] = '(Averaged over a Polygon)'

    variables = gfs_variables()
    for key in variables:
        if variables[key] == data['variable']:
            name = key
            data['name'] = name
            break
    return JsonResponse(data)


@login_required()
def get_shapeaverage(request):
    """
    Used to do averaging of a variable over a shapefile over a world region
    Dependencies: nc_to_gtiff (tools), rastermask_average_gdalwarp (tools), gldas_variables (options), ast,
        makestatplots (tools)
    """
    data = ast.literal_eval(request.body.decode('utf-8'))
    data = shpchart(data)
    data['type'] = '(Average for ' + data['region'] + ')'

    variables = gfs_variables()
    for key in variables:
        if variables[key] == data['variable']:
            name = key
            data['name'] = name
            break
    return JsonResponse(data)


@login_required()
def get_newgfsdata(request):
    """
    gets called when you press the update gfs button on the main page
    Dependencies: from .gfsdata import *
    """
    threddspath, timestamp = setenvironment()
    download_gfs(threddspath, timestamp)
    grib_to_netcdf(threddspath, timestamp)
    nc_georeference(threddspath, timestamp)
    new_ncml(threddspath, timestamp)
    cleanup(threddspath, timestamp)
    set_wmsbounds(threddspath, timestamp)

    return JsonResponse({'Finished': 'Finished'})


@login_required()
def get_customsettings(request):
    """
    returns the paths to the data/thredds services taken from the custom settings and gives it to the javascript
    Dependencies: app_configuration (options)
    """
    return JsonResponse(app_configuration())
