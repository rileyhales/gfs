import ast

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .tools import shpchart, pointchart, polychart
from .options import *


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
    for option in variables:
        if option[1] == data['variable']:
            data['name'] = option[0]
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
    for option in variables:
        if option[1] == data['variable']:
            data['name'] = option[0]
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
    for option in variables:
        if option[1] == data['variable']:
            data['name'] = option[0]
            break
    return JsonResponse(data)


def get_levels_for_variable(request):
    data = ast.literal_eval(request.body.decode('utf-8'))
    variable = data['variable']
    levels = structure_byvars()[variable]
    return JsonResponse({'levels': levels})
