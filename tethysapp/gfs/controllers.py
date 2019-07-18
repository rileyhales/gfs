import random
import string

from django.shortcuts import render
from tethys_sdk.gizmos import SelectInput, RangeSlider

from .options import *
from .app import Gfs as App


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
        'app': App.package,
        'githublink': App.githublink,
        'datawebsite': App.datawebsite,
        'version': App.version,
        'settings': app_settings(),
        'instance_id': ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for i in range(10))
    }

    return render(request, 'gfs/home.html', context)
