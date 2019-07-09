import datetime
import os

from django.http import JsonResponse
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes

from .options import app_settings, get_gfsdate,  gfs_forecastlevels
from .charts import newchart


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def getcapabilities(request):
    return JsonResponse({
        'api_calls': ['getcapabilities', 'gfsdates', 'gfslevels','timeseries']
    })


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def gfslevels(request):
    return JsonResponse({'levels': gfs_forecastlevels()})


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def gfsdates(request):
    threddspath = app_settings()['threddsdatadir']
    timestamp = get_gfsdate()
    if not timestamp == 'clobbered':
        gfs_time = datetime.datetime.strptime(timestamp, "%Y%m%d%H")
        gfs_time = gfs_time.strftime("%b %d, %I%p UTC")
    else:
        gfs_time = 'You attempted to overwrite existing data'

    path = os.path.join(threddspath, 'gfs', timestamp, 'netcdfs')
    files = os.listdir(path)
    files = [i for i in files if i.endswith('.nc')]
    files.sort()
    num_files = len(files)
    if num_files != 0:
        gfs_files = num_files

        gfs_start = files[0].split('_')[1]
        gfs_start = gfs_start.replace('.nc', '')
        gfs_start = datetime.datetime.strptime(gfs_start, '%Y%m%d%H')
        gfs_start = gfs_start.strftime("%B %d %Y at %H")

        gfs_end = files[-1].split('_')[1]
        gfs_end = gfs_end.replace('.nc', '')
        gfs_end = datetime.datetime.strptime(gfs_end, '%Y%m%d%H')
        gfs_end = gfs_end.strftime("%B %d %Y at %H")
    else:
        gfs_files = 'No available data'
        gfs_start = 'No available data'
        gfs_end = 'No available data'
    return JsonResponse({
        'gfs_time': gfs_time,
        'gfs_files': gfs_files,
        'gfs_start': gfs_start,
        'gfs_end': gfs_end,
    })


@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
def timeseries(request):
    parameters = request.GET
    data = {}

    # use try/except to make data dictionary because we want to check that all params have been given
    try:
        data['variable'] = parameters['variable']
        data['coords'] = parameters.getlist('coords')
        data['loc_type'] = parameters['loc_type']
        data['level'] = parameters['level']

        if data['loc_type'] == 'Shapefile':
            data['region'] = parameters['region']
    except KeyError as e:
        return JsonResponse({'Missing Parameter': str(e).replace('"', '').replace("'", '')})
    return JsonResponse(newchart(data))
