// Getting the csrf token
let csrftoken = Cookies.get('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});


////////////////////////////////////////////////////////////////////////  AJAX FUNCTIONS
function getThreddswms() {
    $.ajax({
        url: '/apps/gldas/ajax/getCustomSettings/',
        async: false,
        data: '',
        dataType: 'json',
        contentType: "application/json",
        method: 'POST',
        success: function (result) {
            threddsbase = result['threddsurl'];
            geoserverbase = result['geoserverurl']
        },
    });
}

////////////////////////////////////////////////////////////////////////  LOAD THE MAP
let threddsbase;
let geoserverbase;
getThreddswms();                        // sets the value of threddsbase and geoserverbase
const mapObj = map();                   // used by legend and draw controls
const basemapObj = basemaps();          // used in the make controls function

////////////////////////////////////////////////////////////////////////  DRAWING/LAYER CONTROLS, MAP EVENTS, LEGEND
let drawnItems = new L.FeatureGroup().addTo(mapObj);      // FeatureGroup is to store editable layers
let drawControl = new L.Control.Draw({
    edit: {
        featureGroup: drawnItems,
        edit: false,
    },
    draw: {
        polyline: false,
        circlemarker: false,
        circle: false,
        polygon: false,
        rectangle: true,
    },
});
mapObj.addControl(drawControl);
mapObj.on("draw:drawstart ", function () {     // control what happens when the user draws things on the map
    drawnItems.clearLayers();
});
mapObj.on(L.Draw.Event.CREATED, function (event) {
    drawnItems.addLayer(event.layer);
    L.Draw.Event.STOP;
    getDrawnChart(drawnItems);
});

mapObj.on("mousemove", function (event) {
    $("#mouse-position").html('Lat: ' + event.latlng.lat.toFixed(5) + ', Lon: ' + event.latlng.lng.toFixed(5));
});

let layerObj = newLayer();              // adds the wms raster layer
let controlsObj = makeControls();       // the layer toggle controls top-right corner
legend.addTo(mapObj);                   // add the legend graphic to the map
updateGEOJSON();                        // asynchronously get geoserver wfs/geojson data for the regions

////////////////////////////////////////////////////////////////////////  EVENT LISTENERS
$("#dates").change(function () {
    clearMap();
    for (let i = 0; i < geojsons.length; i++) {
        geojsons[i][0].addTo(mapObj)
    }
    layerObj = newLayer();
    controlsObj = makeControls();
    getDrawnChart(drawnItems);
    legend.addTo(mapObj);
});

$("#variables").change(function () {
    clearMap();
    for (let i = 0; i < geojsons.length; i++) {
        geojsons[i][0].addTo(mapObj)
    }
    layerObj = newLayer();
    controlsObj = makeControls();
    getDrawnChart(drawnItems);
    legend.addTo(mapObj);
});

$("#opacity_raster").change(function () {
    layerObj.setOpacity($('#opacity_raster').val());
});

$('#colorscheme').change(function () {
    clearMap();
    for (let i = 0; i < geojsons.length; i++) {
        geojsons[i][0].addTo(mapObj)
    }
    layerObj = newLayer();
    controlsObj = makeControls();
    legend.addTo(mapObj);
});

$("#opacity_geojson").change(function () {
    styleGeoJSON();
});

$('#colors_geojson').change(function () {
    styleGeoJSON();
});

$('#colors_geojson').change(function () {
    styleGeoJSON();
});

$('#charttype').change(function () {
    makechart();
});

$("#datatoggle").click(function() {
    $("#datacontrols").toggle();
});

$("#displaytoggle").click(function() {
    $("#displaycontrols").toggle();
});