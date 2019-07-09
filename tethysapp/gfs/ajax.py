import ast

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .charts import newchart
from .options import *


@login_required()
def getchart(request):
    """
    Used to make a timeseries of a variable at a user drawn point
    Dependencies: gldas_variables (options), pointchart (tools), ast, makestatplots (tools)
    """
    data = ast.literal_eval(request.body.decode('utf-8'))
    data['user'] = request.user
    data = newchart(data)
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

    for n, file in enumerate(files):
        with open(os.path.join(user_workspace, file.name), 'wb') as dst:
            for chunk in files[n].chunks():
                dst.write(chunk)
    return JsonResponse({'status': 'succeeded'})
