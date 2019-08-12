**********************
REST API Documentation
**********************

A REST API is a web service or a set of methods that can be used to produce or access data without a web interface.
REST APIs use the http protocol to request data.

help
====

The help function requires no arguments and returns a JSON object. The response contains information about each of the
parameters for the timeseries function and links to help websites.

.. code-block:: python

    import requests
    import json

    helpme = requests.get('[TethysPortalUrl]/apps/gfs/api/help/')

    print(helpme.text)
    help_as_dictionary = json.loads(helmp.text)

variableLevels
==============
This function accepts the abbreviated name of a variable as an argument and returns a JSON object containing a list of
any levels that correspond to the GFS variable provided.

+------------+--------------------------------------------------+--------------------------+
| Parameter  | Description                                      | Examples                 |
+============+==================================================+==========================+
| variable   | The shortened name of a GFS variable             | 'acpcp'                  |
+------------+--------------------------------------------------+--------------------------+

.. code-block:: python

    import requests
    import json

    levels = requests.get('[TethysPortalUrl]/apps/gfs/api/variableLevels/', params={'variable': 'acpcp'})

    print(levels.text)
    print(json.loads(levels.text)['levels'])

timeseries
==========

+------------+--------------------------------------------------+--------------------------+
| Parameter  | Description                                      | Examples                 |
+============+==================================================+==========================+
| variable   | The shortened name of a GFS variable             | 'acpcp'                  |
+------------+--------------------------------------------------+--------------------------+
| level      | The abbreviated name of a measurement level      | - 'surface'              |
|            |                                                  | - 'hybrid'               |
+------------+--------------------------------------------------+--------------------------+
|            | - Coordinates or the name of a country or region | - 'Northern Africa'      |
| location   | - (Point) [longitude, latitude]                  | - [-110, 45]             |
|            | - (Bound Box) [minLon, maxLon, minLat, maxLat]   | - [-115, -105, 40, 50]   |
+------------+--------------------------------------------------+--------------------------+

.. code-block:: python

    import requests
    import json

    parameters = {
        'variable': 'acpcp',
        'level': 'surface',
        'location': 'Italy',
    }
    italy_timeseries = requests.get('[TethysPortalUrl]/apps/gfs/api/timeseries/', params=parameters)

    italy_timeseries_as_dictionary = json.loads(italy_timeseries.text)
