from django.shortcuts import render
from django.http import JsonResponse
from tethys_sdk.gizmos import SelectInput, RangeSlider
from django.contrib.auth.decorators import login_required

from .options import *
from .utilities import *
from .app import Gfs as App
from .utilities import new_id


def home(request):
    """
    Controller for the app home page.
    """

    gfsdate = currentgfs()

    variables = SelectInput(
        display_text='Select GFS Variable',
        name='variables',
        multiple=False,
        original=True,
        options=gfs_variables(),
    )

    levels = SelectInput(
        display_text='Available Forecast Levels',
        name='levels',
        multiple=False,
        original=True,
        options=variable_levels()['al'],
    )

    regions = SelectInput(
        display_text='Pick A World Region (ESRI Living Atlas)',
        name='regions',
        multiple=False,
        original=True,
        options=list(worldregions())
    )

    colorscheme = SelectInput(
        display_text='GFS Color Scheme',
        name='colorscheme',
        multiple=False,
        original=True,
        options=wms_colors(),
        initial='rainbow'
    )

    opacity = RangeSlider(
        display_text='GFS Layer Opacity',
        name='opacity',
        min=.5,
        max=1,
        step=.05,
        initial=1,
    )

    gj_color = SelectInput(
        display_text='Boundary Border Colors',
        name='gjClr',
        multiple=False,
        original=True,
        options=geojson_colors(),
        initial='#ffffff'
    )

    gj_opacity = RangeSlider(
        display_text='Boundary Border Opacity',
        name='gjOp',
        min=0,
        max=1,
        step=.1,
        initial=1,
    )

    gj_weight = RangeSlider(
        display_text='Boundary Border Thickness',
        name='gjWt',
        min=1,
        max=5,
        step=1,
        initial=2,
    )

    gj_fillcolor = SelectInput(
        display_text='Boundary Fill Color',
        name='gjFlClr',
        multiple=False,
        original=True,
        options=geojson_colors(),
        initial='rgb(0,0,0,0)'
    )

    gj_fillopacity = RangeSlider(
        display_text='Boundary Fill Opacity',
        name='gjFlOp',
        min=0,
        max=1,
        step=.1,
        initial=.5,
    )

    context = {
        # data options
        'variables': variables,
        'levels': levels,
        'gfsdate': gfsdate,
        'regions': regions,

        # display options
        'colorscheme': colorscheme,
        'opacity': opacity,
        'gjClr': gj_color,
        'gjOp': gj_opacity,
        'gjWt': gj_weight,
        'gjFlClr': gj_fillcolor,
        'gjFlOp': gj_fillopacity,

        # metadata
        'app': App.package,
        'githublink': App.githublink,
        'datawebsite': App.datawebsite,
        'version': App.version,
        'thredds_url': App.get_custom_setting('thredds_url'),
        'instance_id': new_id(),
    }

    return render(request, 'gfs/home.html', context)


@login_required()
def checkworkflowstatus(request):
    threddspath = os.path.join(App.get_custom_setting('thredds_path'))
    fail = os.path.join(threddspath, 'last_run_failed.txt')
    run = os.path.join(threddspath, 'running.txt')
    last = os.path.join(threddspath, 'last_run.txt')
    if os.path.isfile(last):
        with open(last, 'r') as f:
            return JsonResponse({'succeeded': f.readlines()})
    elif os.path.isfile(run):
        return JsonResponse({'running': 'running'})
    elif os.path.isfile(fail):
        with open(fail, 'r') as f:
            return JsonResponse({'failed': f.readlines()})
    else:
        return JsonResponse({'unknown': 'no indicator files were found'})
