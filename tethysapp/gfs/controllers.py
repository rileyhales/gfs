from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, RangeSlider
from django.contrib.auth.models import User

import logging
import datetime
import os
from .app import Gfs as App
from .options import gfs_forecastlevels, gfs_variables, wms_colors, geojson_colors, currentgfs, app_settings, structure
from .gfsworkflow import run_gfs_workflow


@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    layers = SelectInput(
        display_text='GFS Forecast Layers',
        name='layers',
        multiple=False,
        original=True,
        options=gfs_forecastlevels,
        initial='surface'
    )

    reference = structure()

    heightAboveSea_vars = SelectInput(
        display_text='Height Above Sea GFS Variables',
        name='heightAboveSea_vars',
        multiple=False,
        original=True,
        options=reference['heightAboveSea'],
    )

    hybrid_vars = SelectInput(
        display_text='Hybrid GFS Variables',
        name='hybrid_vars',
        multiple=False,
        original=True,
        options=reference['hybrid'],
    )

    isothermZero_vars = SelectInput(
        display_text='Isotherm GFS Variables',
        name='isothermZero_vars',
        multiple=False,
        original=True,
        options=reference['isothermZero'],
    )

    maxWind_vars = SelectInput(
        display_text='Wind GFS Variables',
        name='maxWind_vars',
        multiple=False,
        original=True,
        options=reference['maxWind'],
    )

    meanSea_vars = SelectInput(
        display_text='Mean Sea GFS Variables',
        name='meansea_vars',
        multiple=False,
        original=True,
        options=reference['meanSea'],
    )

    potentialVorticity_vars = SelectInput(
        display_text='Potential Vorticity GFS Variables',
        name='potentialVorticity_vars',
        multiple=False,
        original=True,
        options=reference['potentialVorticity'],
    )

    sigma_vars = SelectInput(
        display_text='Sigma GFS Variables',
        name='sigma_vars',
        multiple=False,
        original=True,
        options=reference['sigma'],
    )

    sigmalayer_vars = SelectInput(
        display_text='Sigma Layer GFS Variables',
        name='sigmaLayer_vars',
        multiple=False,
        original=True,
        options=reference['sigmaLayer'],
    )

    surface_vars = SelectInput(
        display_text='Surface GFS Variables',
        name='surface_vars',
        multiple=False,
        original=True,
        options=reference['surface'],
    )

    tropopause_vars = SelectInput(
        display_text='Tropopause GFS Variables',
        name='tropopause_vars',
        multiple=False,
        original=True,
        options=reference['tropopause'],
    )

    unknown_vars = SelectInput(
        display_text='Other GFS Variables',
        name='unknown_vars',
        multiple=False,
        original=True,
        options=reference['unknown'],
    )

    current_gfs_time = currentgfs()

    colorscheme = SelectInput(
        display_text='Raster Color Scheme',
        name='colorscheme',
        multiple=False,
        original=True,
        options=wms_colors(),
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
        'layers': layers,

        'heightAboveSea_vars': heightAboveSea_vars,
        'hybrid_vars': hybrid_vars,
        'isothermZero_vars': isothermZero_vars,
        'maxWind_vars': maxWind_vars,
        'meanSea_vars': meanSea_vars,
        'potentialVorticity_vars': potentialVorticity_vars,
        'sigma_vars': sigma_vars,
        'sigmalayer_vars': sigmalayer_vars,
        'surface_vars': surface_vars,
        'tropopause_vars': tropopause_vars,
        'unknown_vars': unknown_vars,

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
