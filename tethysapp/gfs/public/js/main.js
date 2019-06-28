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
        url: '/apps/gfs/ajax/getCustomSettings/',
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
$("#variables").change(function () {
    let level_div = $("#levels");
    level_div.empty();
    $.ajax({
        url: '/apps/gfs/ajax/getLevelsForVar/',
        async: true,
        data: JSON.stringify({variable: this.options[this.selectedIndex].value}),
        dataType: 'json',
        contentType: "application/json",
        method: 'POST',
        success: function (result) {
            let levels = result['levels'];
            // if (levels.length === 1) {
            //     level_div.hide()
            // } else {
            //     level_div.show()
            // }
            for (let i = 0; i < levels.length; i++){
                level_div.append('<option value="' + levels[i][1] + '">' + levels[i][0] + "</option>");
            }

            clearMap();
            for (let i = 0; i < geojsons.length; i++) {
                geojsons[i][0].addTo(mapObj)
            }
            layerObj = newLayer();
            controlsObj = makeControls();
            getDrawnChart(drawnItems);
            legend.addTo(mapObj);
            // todo change the measurements options
        },
    });
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

$('#levels').change(function () {
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

$("#datatoggle").click(function () {
    $("#datacontrols").toggle();
});

$("#displaytoggle").click(function () {
    $("#displaycontrols").toggle();
});
