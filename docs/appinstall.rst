======================
Install the Tethys App
======================
Please refer to the `Tethys Documentation <http://docs.tethysplatform.org/en/stable/>`_ for help installing Tethys.

Clone from Git and install
--------------------------
This application is compatible with Tethys 2.X and Tethys 3 Distributions and as such is compatible with both Python 2
and 3 and Django 1 and 2. Install the latest version of Tethys before installing this app. This app requires the python
packages:

* numpy
* pandas
* netcdf4
* pygrib
* rasterio
* rasterstats
* pyshp
* requests

On the terminal of the server where you're installing the app:

.. code-block:: bash

    conda activate tethys
    cd /path/to/apps/directory/

    git clone https://github.com/rileyhales/gfs.git
    cd gfs

    # for tethys 3
    tethys install

    # for tethys 2
    python setup.py develop
    tethys manage collectstatic

Reset the server, then attempt to log in through the web interface as an administrator. The app should appear in the
Apps Library page in grey indicating you need to configure the custom settings.

Set up a THREDDS Data Server
----------------------------
Refer to the documentation for THREDDS to set up an instance of on your tethys server (a UNIDATA has containerized
THREDDS and tethys offers commands to init a container). You will need to modify Thredds' settings files to enable WMS
services and support for netCDF files on your server. In the folder where you installed Thredds, there should be a file
called ``catalog.xml``.

.. code-block:: bash

    vim catalog.xml

At the top of the document is a list of supported services. Make sure the line for wms is not commented out.

| ``<service name="wms" serviceType="WMS" base="/thredds/wms/" />``

Scroll down toward the end of the section that says ``filter``. This is the section that limits which kinds of datasets Thredds will process. We need it to accept .nc, .nc4, and .ncml file types. Make sure your ``filter`` tag includes the following lines.

.. code-block:: xml

    <filter>
        <include wildcard="*.grb"/>
        <include wildcard="*.nc"/>
        <include wildcard="*.ncml"/>
    </filter>

.. code-block:: bash

    vim threddsConfig.xml

Find the section near the top about CORS (Cross-Origin Resource Sharing). CORS allows Thredds to serve data to servers besides the host where it is located. Depending on your exact setup, you need to enable CORS by uncommenting these tags.

.. code-block:: xml

    <CORS>
        <enabled>true</enabled>
        <maxAge>1728000</maxAge>
        <allowedMethods>GET</allowedMethods>
        <allowedHeaders>Authorization</allowedHeaders>
        <allowedOrigin>``</allowedOrigin>
    </CORS>

Reset the Thredds server so the catalog is regenerated with the edits that you've made. The command to reset your
server will vary based on your installation method, such as ``docker restart thredds`` or
``sudo systemctl reset tomcat``.

GFS Downloads
-------------
In THREDDS' public folder, where your datasets are stored, create a new folder called ``gfs``. Get the path to this
directory (pwd) and save it for later. You need to fill this folder with the GFS data. To do this, you need to run the
gfsworkflow.py file using the path to that ``gfs`` folder as the argument to the function. The time needed to run the
workflow depends on the processing power of your computer/server, internet connection, and how fast NOAA can serve the
GFS gribs. On the same machine i've timed the workflow at 5-10 minutes and over 30 minutes.

You can monitor the progress of the workflow by checking the workflow.log file which will be created in the ``gfs``
folder along with the rest of the data. The log is updated in real time as steps in the workflow are finished including
if it succeeded or why it failed.

After a successful workflow run, your ``gfs`` folder should look something like this:

| gfs/
| ---> YYYYMMDDHH/ (directory, named for the time of the data)
|      ---> netcdfs/ (directory)
| ---> workflow.log (messages about the workflow's status)
| ---> lastrun.txt (the date of the last successful run)
| ---> atmosphere_wms.ncml
| ---> depthBelowLayer_wms.ncml
| ---> ...(several more .ncml files)

If there is a ``running.txt`` file in the ``gfs`` folder, the workflow didn't finish correctly. You need to:

1. Read the log.
2. Address the cause of the workflow failure. The most common failures are download errors because NOAA's servers are
   overloaded/slow or the process interrupted by a server function. Both are most likely caused by unfortunate timing.
   Usually trying again is enough to solve it. As a best practice, try running this workflow in a CRON job as explained
   below.
3. Delete running.txt (as a precaution, the workflow will not run until you do)
4. Re-run the workflow

CRON Job
--------
The workflow was scripted such that it is easy to turn in to a cron task where you could run the workflow up to 4 times
per day. GFS forecasts are generated every 6 hours at 00, 06, 12, 18. The forecast for that time step will be available
soon after it is created. To keep the app's data current, you'll need to set up a cron job such that you can:

1. Activate a python environment with the required dependencies.
2. Run the workflow.sh script found in the files for this app.
3. Know the path to the folder within the THREDDS directories where the GFS data will be stored.
4. Have read/write access to that folder.

Set up a GeoServer
------------------
Refer to the documentation for GeoServer to set up an instance of GeoServer on your tethys server. There is an official
GeoServer container which you can install using tethys commands. Log in to your tethys portal as an administrator and
create a Spatial Dataset Service Setting configured to the GeoServer instance you just created.

If you choose not to use geoserver, your users will not be able to view custom shapefiles in the app.

Set The Custom Settings
-----------------------
Log in to your Tethys portal as an admin. Click on the grey GLDAS box and specify these settings:

* ``thredds_path:`` This is the full path to the directory named gldas that you should have created within the thredds data directory during step 2. You can get this by navigating to that folder in the terminal and then using the ``pwd`` command. (example: ``/tomcat/content/thredds/gldas/``)
* ``thredds_url:`` This is the base URL to Thredds WMS services that the app uses to build urls for each of the WMS layers generated for the netcdf datasets. If you followed the typical configuration of thredds (these instructions) then your base url will look something like ``yourserver.com/thredds/wms/testAll/gldas/``. You can verify this by opening the thredds catalog in a web browser (typically at ``yourserver.com/thredds/catalog.html``). Navigate to one of the GLDAS netcdf files and click the WMS link. A page showing an xml document should load. Copy the url in the address bar until you get to the ``/gldas/`` folder in that url. Do not include ``/raw/name_of_dataset.nc`` or the request that comes after. (example: ``https://tethys.byu.edu/thredds/wms/testAll/gldas/``)
* ``Spatial Dataset Services:`` Create a Tethys SpatialDatasetService configured with the correct urls and admin username/password for the GeoServer from step 3
