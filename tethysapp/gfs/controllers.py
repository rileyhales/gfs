from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, RangeSlider
from django.contrib.auth.models import User

import logging
from .options import *
import datetime
import os
from .app import Gfs as App
from .gfsworkflow import run_gfs_workflow


@login_required()
def home(request):
    """
    Controller for the app home page.
    """

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
        options=structure_byvars()['al'],
    )

    gfsdate = currentgfs()

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
        'model': 'gfs',
        'variables': variables,
        'levels': levels,
        'gfsdate': gfsdate,

        # display options
        'colorscheme': colorscheme,
        'opacity': opacity,
        'gjClr': gj_color,
        'gjOp': gj_opacity,
        'gjWt': gj_weight,
        'gjFlClr': gj_fillcolor,
        'gjFlOp': gj_fillopacity,

        # metadata
        'githublink': App.githublink,
        'datawebsite': App.datawebsite,
        'version': App.version,
        'settings': app_settings(),
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
