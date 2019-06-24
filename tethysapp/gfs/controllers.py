from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, RangeSlider
from django.contrib.auth.models import User

import logging
import datetime
import os
from .app import Gfs as App
from .options import gfs_variables, wms_colors, geojson_colors, currentgfs, app_settings
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

    context = {
        'variables': variables,
        'current_gfs_time': current_gfs_time,
        'colorscheme': colorscheme,
        'opacity_raster': opacity_raster,
        'colors_geojson': colors_geojson,
        'youtubelink': App.youtubelink,
        'githublink': App.githublink,
        'gfslink': App.gfslink,
        'version': App.version,
    }

    return render(request, 'gfs/home.html', context)


@login_required()
def run_workflows(request):
    """
    The controller for running the workflow to download and process data
    """
    # Check for user permissions here rather than with a decorator so that we can log the failure
    if not User.is_superuser:
        logging.basicConfig(filename=app_settings()['logfile'], filemode='a', level=logging.INFO, format='%(message)s')
        logging.info('A non-superuser tried to run this workflow on ' + datetime.datetime.utcnow().strftime("%D at %R"))
        logging.info('The user was ' + str(request.user))
        return JsonResponse({'Unauthorized User': 'You do not have permission to run the workflow. Ask a superuser.'})

    # enable logging to track the progress of the workflow and for debugging
    logging.basicConfig(filename=app_settings()['logfile'], filemode='w', level=logging.INFO, format='%(message)s')
    logging.info('Workflow initiated on ' + datetime.datetime.utcnow().strftime("%D at %R"))

    # Set the clobber option so that the right folders get deleted/regenerated in the set_environment functions
    if 'clobber' in request.GET:
        clobber = request.GET['clobber'].lower()
        if clobber in ['yes', 'true']:
            logging.info('You chose the clobber option so the timestamps and all the data folders will be overwritten')
            wrksp = App.get_app_workspace().path
            timestamps = os.listdir(wrksp)
            timestamps = [stamp for stamp in timestamps if stamp.endswith('timestamp.txt')]
            for stamp in timestamps:
                with open(os.path.join(wrksp, stamp), 'w') as file:
                    file.write('clobbered')
            logging.info('Clobber complete. Files marked for execution')

    gfs_status = run_gfs_workflow()

    return JsonResponse({'gfs status': gfs_status})
