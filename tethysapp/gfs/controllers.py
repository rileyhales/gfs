from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, RangeSlider

from .app import Gfs as App
from .options import gfs_variables, wms_colors, geojson_colors, currentgfs
from .gfsworkflow import run_gfs_workflow


@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    variables = gfs_variables()
    options = []
    for key in sorted(variables.keys()):
        tuple1 = (key, variables[key])
        options.append(tuple1)
    del tuple1, key, variables

    variables = SelectInput(
        display_text='Select GFS Variable',
        name='variables',
        multiple=False,
        original=True,
        options=options,
    )

    current_gfs_time = currentgfs()

    colorscheme = SelectInput(
        display_text='Raster Color Scheme',
        name='colorscheme',
        multiple=False,
        original=True,
        options=wms_colors(),
        initial='rainbow'
    )

    opacity_raster = RangeSlider(
        display_text='Raster Opacity',
        name='opacity_raster',
        min=.5,
        max=1,
        step=.05,
        initial=1,
    )

    colors_geojson = SelectInput(
        display_text='Boundary Colors',
        name='colors_geojson',
        multiple=False,
        original=True,
        options=geojson_colors(),
        initial='#ffffff'
    )

    opacity_geojson = RangeSlider(
        display_text='Boundary Opacity',
        name='opacity_geojson',
        min=.0,
        max=1,
        step=.1,
        initial=.2,
    )

    context = {
        'variables': variables,
        'current_gfs_time': current_gfs_time,
        'colorscheme': colorscheme,
        'opacity_raster': opacity_raster,
        'colors_geojson': colors_geojson,
        'opacity_geojson': opacity_geojson,
        'youtubelink': App.youtubelink,
        'githublink': App.githublink,
        'gfslink': App.gfslink,
        'version': App.version,
    }

    return render(request, 'gfs/home.html', context)


@login_required()
def update(request):
    status = run_gfs_workflow()
    return JsonResponse({'Workflow Status': status})
