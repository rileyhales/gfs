from django.http import JsonResponse
# from rest_framework.decorators import api_view

from .options import gfs_variables, gfs_forecastlevels, structure_byvars, worldregions, countries
from .utilities import new_id
from .charts import newchart
from .app import Gfs as App


# @api_view(['GET'])
def help(request):
    return JsonResponse({
        'api_calls': ['help', 'gfsTimestamp', 'variableOptions', 'levelOptions', 'variableLevels',
                      'geometryOptions', 'timeseries'],
        'help_url': App.githublink,
        'required_arguments': {
            'variable': 'Short name of a GLDAS variable (see gldas/api/variableOptions for more help)',
            'level': 'Which of the variable\'s measurment levels from which to extract a timeseries',
            'loc_type': 'The area you want a timeseries for. You may choose Point, Polygon (a Bounding Box), or '
                        'VectorGeometry (for countries/regions) (see gldas/api/geometryOptions for more help)',
            'coords': 'REQUIRED IF loc_type is Point or Polygon (see gldas/api/geometryOptions for more help)',
            'vectordata': 'REQUIRED IF loc_type is VectorGeometry (see gldas/api/geometryOptions for more help)',
        }
    })


# @api_view(['GET'])
def timestamp(request):
    # todo add function for checking available time
    dates = {
        'start_time': '',
        'end_time': '',
    }
    return JsonResponse(dates)


# @api_view(['GET'])
def variables(request):
    return JsonResponse({'allvariables': gfs_variables()})


# @api_view(['GET'])
def levels(request):
    return JsonResponse({'all_levels': gfs_forecastlevels()})


# @api_view(['GET'])
def variable_levels(request):
    parameters = request.GET
    try:
        return JsonResponse({'levels': structure_byvars()[parameters['variable']]})
    except KeyError:
        return JsonResponse(structure_byvars())


# @api_view(['GET'])
def geometry(request):
    return JsonResponse({
        'Point': 'Requires coords argument: formatted as a list [longitude, latitude]',
        'Polygon': 'Requires coords argument: formatted as a list [minimum longitude, max longitude, min latitude, '
                   'max latitude]',
        'VectorGeometry': 'Requires region argument: specify the name of a region or country exactly as shown',
        'Regions': [i[0] for i in worldregions() if i[1] != '' and i[1] != 'none'],
        'Countries': countries(),
    })


# @api_view(['GET'])
def timeseries(request):
    parameters = request.GET
    data = {}

    # todo modify the filters to verify they gave the correct parameters

    # use try/except to make the data dictionary because we want to check that each param has been given
    try:
        # try to parse the 3 standard arguments, the 4th comes from validation
        data['time'] = parameters['time']
        data['variable'] = parameters['variable']
        data['loc_type'] = parameters['loc_type']

        if data['loc_type'] == 'VectorGeometry':
            data['vectordata'] = parameters['vectordata']
        else:
            data['coords'] = parameters.getlist('coords')

    except KeyError as e:
        return JsonResponse({'Missing Parameter': str(e).replace('"', '').replace("'", '')})

    def validate_points(data):
        test = data['coords']
        if type(test) is list and len(test) == 2:
            for i in test:
                try:
                    float(i)
                except Exception:
                    return False
            if not 180 > float(test[0]) > -180 and 90 > float(test[1]) > -90:
                return False
        else:
            return False
        return True

    def validate_polygon(data):
        test = data['coords']
        print(test)
        if type(test) is list and len(test) == 4:
            for i in test:
                try:
                    float(i)
                except Exception:
                    return False
            if not float(test[1]) > float(test[0]) and float(test[3]) > float(test[2]):
                return False
            if not 180 > float(test[0]) > -180 and 180 > float(test[1]) > -180:
                return False
            if not 90 > float(test[2]) > -90 and 90 > float(test[3]) > -90:
                return False
        else:
            return False
        return True

    # perform validation for point
    if data['loc_type'] == 'Point':
        if not validate_points(data):
            return JsonResponse({'Invalid coords': 'ask gldas/api/geometryOptions for more help'})

    # perform validation for polygon
    elif data['loc_type'] == 'Polygon':
        if validate_polygon(data):
            data['coords'] = [[[data['coords'][0], data['coords'][2]], [data['coords'][0], data['coords'][3]],
                               [data['coords'][1], data['coords'][3]], [data['coords'][1], data['coords'][2]]]]
        else:
            return JsonResponse({'Invalid coords': 'ask gldas/api/geometryOptions for more help'})

    # perform validation for vectorgeometry
    elif data['loc_type'] == 'VectorGeometry':
        data['vectordata'] = parameters['vectordata']
        if data['vectordata'] in worldregions():
            data['vectordata'] = 'esri-regions-' + data['vectordata']
        elif data['vectordata'] in countries():
            data['vectordata'] = 'esri-countries-' + data['vectordata']
        else:
            return JsonResponse(
                {'Invalid Selection': data['vectordata'] + ' is not a valid region/country, check your spelling'})

    data['instance_id'] = new_id()
    return JsonResponse(newchart(data))
