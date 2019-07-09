////////////////////////////////////////////////////////////////////////  MAP FUNCTIONS
function map() {
    // create the map
    return L.map('map', {
        zoom: 2,
        minZoom: 1.25,
        boxZoom: true,
        maxBounds: L.latLngBounds(L.latLng(-100.0, -270.0), L.latLng(100.0, 270.0)),
        center: [20, 0],
        timeDimension: true,
        timeDimensionControl: true,
        timeDimensionControlOptions: {
            position: "bottomleft",
            autoPlay: true,
            loopButton: true,
            backwardButton: true,
            forwardButton: true,
            timeSliderDragUpdate: true,
            minSpeed: 2,
            maxSpeed: 6,
            speedStep: 1,
        },
    });
}

function basemaps() {
    // create the basemap layers
    let Esri_WorldImagery = L.esri.basemapLayer('Imagery');
    let Esri_WorldTerrain = L.esri.basemapLayer('Terrain');
    let Esri_Imagery_Labels = L.esri.basemapLayer('ImageryLabels');
    return {
        "ESRI Imagery": L.layerGroup([Esri_WorldImagery, Esri_Imagery_Labels]).addTo(mapObj),
        "ESRI Terrain": L.layerGroup([Esri_WorldTerrain, Esri_Imagery_Labels])
    }
}

////////////////////////////////////////////////////////////////////////  WMS LAYERS
function newLayer() {
    let layer = $("#variables").val();

    let wmsurl;
    wmsurl = threddsbase + $("#levels").val() + '_wms.ncml';

    let cs_rng = bounds[model][layer];
    if ($("#use_csrange").is(":checked")) {
        console.log('is checked');
        cs_rng = String($("#cs_min").val()) + ',' + String($("#cs_max").val())
    }

    let wmsLayer = L.tileLayer.wms(wmsurl, {
        // version: '1.3.0',
        layers: layer,
        dimension: 'time',
        useCache: true,
        crossOrigin: false,
        format: 'image/png',
        transparent: true,
        opacity: $("#opacity_raster").val(),
        BGCOLOR: '0x000000',
        styles: 'boxfill/' + $('#colorscheme').val(),
        colorscalerange: cs_rng,
    });

    return L.timeDimension.layer.wms(wmsLayer, {
        name: 'time',
        requestTimefromCapabilities: true,
        updateTimeDimension: true,
        updateTimeDimensionMode: 'replace',
        cache: 20,
    }).addTo(mapObj);
}

////////////////////////////////////////////////////////////////////////  LEGEND DEFINITIONS
let legend = L.control({position: 'topright'});
legend.onAdd = function () {
    let layer = $("#variables").val();

    let wmsurl;
    wmsurl = threddsbase + $("#levels").val() + '_wms.ncml';

    let cs_rng = bounds[model][layer];
    if ($("#use_csrange").is(":checked")) {
        cs_rng = String($("#cs_min").val()) + ',' + String($("#cs_max").val())
    }

    let div = L.DomUtil.create('div', 'legend');
    let url = wmsurl + "?REQUEST=GetLegendGraphic&LAYER=" + layer + "&PALETTE=" + $('#colorscheme').val() + "&COLORSCALERANGE=" + cs_rng;
    div.innerHTML = '<img src="' + url + '" alt="legend" style="width:100%; float:right;">';
    return div
};

let latlon = L.control({position: 'bottomleft'});
latlon.onAdd = function () {
    let div = L.DomUtil.create('div', 'well well-sm');
    div.innerHTML = '<div id="mouse-position" style="text-align: center"></div>';
    return div;
};
////////////////////////////////////////////////////////////////////////  GEOJSON LAYERS - GEOSERVER + WFS / GEOJSON
let currentregion = '';              // tracks which region is on the chart for updates not caused by the user picking a new region
function layerPopups(feature, layer) {
    let region = feature.properties.name;
    layer.bindPopup('<a class="btn btn-default" role="button" onclick="getShapeChart(' + "'" + region + "'" + ')">Get timeseries (average) for ' + region + '</a>');
}

// declare a placeholder layer for all the geojson layers you want to add
let jsonparams = {
    onEachFeature: layerPopups,
    style: {
        color: $("#gjClr").val(),
        opacity: $("#gjOp").val(),
        weight: $("#gjWt").val(),
        fillColor: $("#gjFlClr").val(),
        fillOpacity: $("#gjFlOp").val()
    }
};
let africa = L.geoJSON(false, jsonparams);
let asia = L.geoJSON(false, jsonparams);
let australia = L.geoJSON(false, jsonparams);
let centralamerica = L.geoJSON(false, jsonparams);
let europe = L.geoJSON(false, jsonparams);
let middleeast = L.geoJSON(false, jsonparams);
let northamerica = L.geoJSON(false, jsonparams);
let southamerica = L.geoJSON(false, jsonparams);
// create this reference array that other functions will build on
const geojsons = [
    [africa, 'africa', africa_json],
    [asia, 'asia', asia_json],
    [australia, 'australia', australia_json],
    [centralamerica, 'centralamerica', centralamerica_json],
    [europe, 'europe', europe_json],
    [middleeast, 'middleeast', middleeast_json],
    [northamerica, 'northamerica', northamerica_json],
    [southamerica, 'southamerica', southamerica_json],
];

// gets the geojson layers from geoserver wfs and updates the layer
function getWFSData(geoserverlayer, leafletlayer) {
    // http://jsfiddle.net/1f2Lxey4/2/
    let parameters = L.Util.extend({
        service: 'WFS',
        version: '1.0.0',
        request: 'GetFeature',
        typeName: 'gldas:' + geoserverlayer,
        maxFeatures: 10000,
        outputFormat: 'application/json',
        parseResponse: 'getJson',
        srsName: 'EPSG:4326',
        crossOrigin: 'anonymous'
    });
    $.ajax({
        async: true,
        jsonp: false,
        url: geoserverbase + L.Util.getParamString(parameters),
        contentType: 'application/json',
        success: function (data) {
            leafletlayer.addData(data).addTo(mapObj);
        },
    });
}

function updateGEOJSON() {
    if (geoserverbase === 'geojson') {
        for (let i = 0; i < geojsons.length; i++) {
            geojsons[i][0].addData(geojsons[i][2]).addTo(mapObj);
        }
    } else {
        for (let i = 0; i < geojsons.length; i++) {
            getWFSData(geojsons[i][1], geojsons[i][0]);
        }
    }
}

function styleGeoJSON() {
    // determine the styling to apply
    let style = {
        color: $("#gjClr").val(),
        opacity: $("#gjOp").val(),
        weight: $("#gjWt").val(),
        fillColor: $("#gjFlClr").val(),
        fillOpacity: $("#gjFlOp").val(),
    };
    // apply it to all the geojson layers
    for (let i = 0; i < geojsons.length; i++) {
        geojsons[i][0].setStyle(style);
    }
}

////////////////////////////////////////////////////////////////////////  MAP CONTROLS AND CLEARING
// the layers box on the top right of the map
function makeControls() {
    return L.control.layers(basemapObj, {
        'Earth Observation': layerObj,
        'Drawing': drawnItems,
        'Europe': europe,
        'Asia': asia,
        'Middle East': middleeast,
        'North America': northamerica,
        'Central America': centralamerica,
        'South America': southamerica,
        'Africa': africa,
        'Australia': australia,
    }).addTo(mapObj);
}

// you need to remove layers when you make changes so duplicates dont persist and accumulate
function clearMap() {
    // remove the controls for the wms layer then remove it from the map
    controlsObj.removeLayer(layerObj);
    mapObj.removeLayer(layerObj);
    // now do it for all the geojson layers
    for (let i = 0; i < geojsons.length; i++) {
        controlsObj.removeLayer(geojsons[i][0]);
        mapObj.removeLayer(geojsons[i][0]);
    }
    // now delete the controls object
    mapObj.removeControl(controlsObj);
}
