import ast

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .options import app_configuration, gldas_variables
from .tools import shpchart, pointchart, polychart, makestatplots


@login_required()
def get_pointseries(request):
    """
    Used to make a timeseries of a variable at a user drawn point
    Dependencies: gldas_variables (options), pointchart (tools), ast, makestatplots (tools)
    """
    data = ast.literal_eval(request.body.decode('utf-8'))
    data = pointchart(data)
    data['type'] = '(Values at a Point)'
    data = makestatplots(data)

    variables = gldas_variables()
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
    data = makestatplots(data)

    variables = gldas_variables()
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
    data = makestatplots(data)

    variables = gldas_variables()
    for key in variables:
        if variables[key] == data['variable']:
            name = key
            data['name'] = name
            break
    return JsonResponse(data)


@login_required()
def get_customsettings(request):
    """
    returns the paths to the data/thredds services taken from the custom settings and gives it to the javascript
    Dependencies: app_configuration (options)
    """
    return JsonResponse(app_configuration())
