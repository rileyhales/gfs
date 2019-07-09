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


// threddsbase and geoserverurl defined in base.html
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
latlon.addTo(mapObj);                   // add the box showing lat and lon to the map
updateGEOJSON();                        // asynchronously get geoserver wfs/geojson data for the regions

////////////////////////////////////////////////////////////////////////  EVENT LISTENERS
function update() {
    for (let i = 0; i < geojsons.length; i++) {
        geojsons[i][0].addTo(mapObj)
    }
    layerObj = newLayer();
    controlsObj = makeControls();
    legend.addTo(mapObj);
}

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
            for (let i = 0; i < levels.length; i++){
                level_div.append('<option value="' + levels[i][1] + '">' + levels[i][0] + "</option>");
            }
            clearMap();
            update();
            getDrawnChart(drawnItems);
        },
    });
});
$("#dates").change(function () {clearMap();update();getDrawnChart(drawnItems);});
// custom dates control
$('#charttype').change(function () {makechart();});
$("#levels").change(function () {clearMap();update();});

$("#display").click(function() {
    $("#displayopts").toggle();
});
$("#use_csrange").change(function () {clearMap();update()});
$('#colorscheme').change(function () {clearMap();update()});
$("#opacity").change(function () {layerObj.setOpacity($(this).val())});
$('#gjClr').change(function () {styleGeoJSON()});
$("#gjOp").change(function () {styleGeoJSON()});
$("#gjWt").change(function () {styleGeoJSON()});
$('#gjFlClr').change(function () {styleGeoJSON()});
$("#gjFlOp").change(function () {styleGeoJSON()});