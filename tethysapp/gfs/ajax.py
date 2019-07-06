import ast
import shutil

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
    data['user'] = request.user
    data = shpchart(data)
    del data['user']
    if data['region'] == 'customshape':
        data['type'] = '(Averaged over user uploaded shapefile)'
    else:
        data['type'] = '(Average for ' + data['region'] + ')'

    variables = gfs_variables()
    for option in variables:
        if option[1] == data['variable']:
            data['name'] = option[0]
            break
    return JsonResponse(data)


@login_required()
def get_levels_for_variable(request):
    data = ast.literal_eval(request.body.decode('utf-8'))
    variable = data['variable']
    levels = structure_byvars()[variable]
    return JsonResponse({'levels': levels})


@login_required()
def uploadshapefile(request):
    files = request.FILES.getlist('files')
    user_workspace = App.get_user_workspace(request.user).path
    for i in request.POST:
        print(i)

    for n, file in enumerate(files):
        if file.name.endswith('.shp'):
            filename = file.name
        with open(os.path.join(user_workspace, file.name), 'wb') as dst:
            for chunk in files[n].chunks():
                dst.write(chunk)

    return JsonResponse({'customshp': os.path.join(user_workspace, filename)})
