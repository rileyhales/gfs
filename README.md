# GFS Visualizer Tool Documentation
This is a Tethys 2/3 compatible app that visualizes GFS data from NOAA.

© [Riley Hales](http://rileyhales.com), 2019. Based on the [GLDAS Data Visualizer](https://github.com/rileyhales/gldas) (Hales, 2018) Developed at the BYU Hydroinformatics Lab.

## App Features

~~~~
rasterstats
rasterio
osr
conda install -c conda-forge cfgrib
~~~~

## Installation Instructions
### 1 Install the Tethys App
This application is compatible with Tethys 2.X and Tethys 3 Distributions and is compatible with both Python 2 and 3 and Django 1 and 2. Install the latest version of Tethys before installing this app. This app requires the python packages: numpy, netcdf4, ogr, osr. Both should be installed automatically as part of this installation process.

On the terminal of the server enter the tethys environment with the ```t``` command. ```cd``` to the directory where you install apps then run the following commands:  
~~~~
git clone https://github.com/rileyhales/gfs.git  
cd gfs
python setup.py develop
~~~~  
If you are on a production server, run:
~~~~
tethys manage collectstatic
~~~~
Reset the server, then attempt to log in through the web interface as an administrator. The app should appear in the Apps Library page in grey indicating you need to configure the custom settings.

### 2 Set up a Thredds Server (GFS Raster Images)
You will also need to modify Thredds' settings files to enable WMS services and support for netCDF files on your server. In the folder where you installed Thredds, there should be a file called ```catalog.xml```. 
~~~~
vim catalog.xml
~~~~
Type ```a``` to begin editing the document.

At the top of the document is a list of supported services. Make sure the line for wms is not commented out.
~~~~
<service name="wms" serviceType="WMS" base="/thredds/wms/" />
~~~~
Scroll down toward the end of the section that says ```filter```. This is the section that limits which kinds of datasets Thredds will process. We need it to accept .nc, .nc4, and .ncml file types. Make sure your ```filter``` tag includes the following lines.
~~~~
<filter>
    <include wildcard="*.nc"/>
    <include wildcard="*.nc4"/>
    <include wildcard="*.ncml"/>
</filter>
~~~~
Press ```esc``` then type ```:x!```  and press the ```return``` key to save and quit.
~~~~
vim threddsConfig.xml
~~~~
Find the section near the top about CORS (Cross-Origin Resource Sharing). CORS allows Thredds to serve data to servers besides the host where it is located. Depending on your exact setup, you need to enable CORS by uncommenting these tags.
~~~~
<CORS>
    <enabled>true</enabled>
    <maxAge>1728000</maxAge>
    <allowedMethods>GET</allowedMethods>
    <allowedHeaders>Authorization</allowedHeaders>
    <allowedOrigin>*</allowedOrigin>
</CORS>
~~~~
Press ```esc``` then type ```:x!```  and press the ```return``` key to save and quit.

Reset the Thredds server so the catalog is regenerated with the edits that you've made. The command to reset your server will vary based on your installation method, such as ```docker reset thredds``` or ```sudo systemctl reset tomcat```.

### 3 Get the GFS Data from NOAA

### 4 Set up a GeoServer (World Region Boundaries) (Optional, Recommended)
Refer to the documentation for GeoServer to set up an instance of GeoServer on your tethys server. If you choose not to use geoserver, skip this step and follow instructions in step 5 for the custom settings.

This app can display and perform spatial averaging for 8 world regions. The app will perform the raster operations and averaging using shapefiles that cover general regions of the globe in as few points as possible to increase computation speed, reduce file sizes, and prevent computation errors related to large and complex polygon shapefiles. More accurate boundaries for the regions are available for visualization as a Web Feature Service (WFS) through GeoServer or as local geojson files. A copy of the shapefiles you need, in the properly formatted zip archives, is found in the ```workspaces/app_workspace``` directory of the app.   

Use a web browser to log in to your GeoServer. Use the web interface to create a new workspace named ```gfs```. Use the command line to navigate to the directory containing the GeoServerFiles zip archive you got from the app. Extract the contents of that zip archive, but do not unzip the 8 zip archives that it contains. Upload each of those 8 zip archives to the new GeoServer workspace using cURL commands (e.g. run this command 8 times). The general format of the command is:
~~~~
curl -v -u [user]:[password] -XPUT -H "Content-type: application/zip" --data-binary @[name_of_zip].zip https://[hostname]/geoserver/rest/workspaces/[workspaceURI]/datastores/[name_of_zip]/file.shp
~~~~
This command asks you to specify:
* Geoserver Username and Password. If you have not changed it, the default is admin and geoserver.
* Name of the Zip Archive you're uploading. Be sure you spell it correctly and that you put it in each of the 2 places it is asked for.
* Hostname. The host website, e.g. ```tethys.byu.edu```.
* The Workspace URI. The URI that you specified when you created the new workspace through the web interface. If you followed these instructions it should be ```gldas```.

### 5 Set The Custom Settings
Log in to your Tethys portal as an admin. Click on the grey GLDAS box and specify these settings:

**Local File Path:** This is the full path to the directory named gldas that you should have created within the thredds data directory during step 2. You can get this by navigating to that folder in the terminal and then using the ```pwd``` command. (example: ```/tomcat/content/thredds/gfs/```)  

**Thredds Base Address:** This is the base URL to Thredds WMS services that the app uses to build urls for each of the WMS layers generated for the netcdf datasets. If you followed the typical configuration of thredds (these instructions) then your base url will look something like ```yourserver.com/thredds/wms/testAll/gfs/```. You can verify this by opening the thredds catalog in a web browser (typically at ```yourserver.com/thredds/catalog.html```). Navigate to one of the GLDAS netcdf files and click the WMS link. A page showing an xml document should load. Copy the url in the address bar until you get to the ```/gldas/``` folder in that url. Do not include ```/raw/name_of_dataset.nc``` or the request that comes after. (example: ```https://tethys.byu.edu/thredds/wms/testAll/gldas/```)

**Geoserver Workspace Address:** This is the WFS (ows) url to the workspace on geoserver where the shapefiles for the world region boundaries are served. This geoserver workspace needs to have at minimum WFS services enabled. You can find it by using the layer preview interface of GeoServer and choosing GeoJSON as the format. If you chose not to use geoserver, enter ```geojson``` as your url. (example: ```https://tethys.byu.edu/geoserver/gfs/ows```)

## How the app works
