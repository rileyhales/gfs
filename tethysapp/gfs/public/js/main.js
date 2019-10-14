var staticPath = baseStatic
var apiServer = `${staticPath.replace("/static", "/apps")}`

// see base.html scripts for thredds, geoserver, app, model, instance_id
let csrftoken = Cookies.get('csrftoken');
Cookies.set('instance_id', instance_id);

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

let layerGFS = newGFS();                // adds the wms raster layer
let layerRegion = regionsESRI();        // adds the world regions
let controlsObj = makeControls();       // the layer toggle controls top-right corner
legend.addTo(mapObj);                   // add the legend graphic to the map
latlon.addTo(mapObj);                   // add the box showing lat and lon to the map

////////////////////////////////////////////////////////////////////////  EVENT LISTENERS
function update() {
    layerGFS = newGFS();
    controlsObj = makeControls();
    legend.addTo(mapObj);
}
function changeregions(firedfrom) {
    let countryJQ = $("#countries");
    let regionjQ = $("#regions");
    if (firedfrom === 'country') {
        let country = countryJQ.val();
        if (!countrieslist.includes(country)) {
            alert('The country "' + country + '" was not found in the list of countries available. Please check spelling and capitalization, and use the input suggestions.');
            return
        }
        regionjQ.val('none');
    } else {
        countryJQ.val('')
    }
    // change to none/empty input
    mapObj.removeLayer(layerRegion);
    controlsObj.removeLayer(layerRegion);
    if (firedfrom === 'region') {
        layerRegion = regionsESRI();
        controlsObj.addOverlay(layerRegion, 'Region Boundaries');
    } else {
        layerRegion = countriesESRI();
        controlsObj.addOverlay(layerRegion, 'Country Boundaries');
    }
}

// input validation
$(".customs").keyup(function () {this.value = this.value.replace(/i[a-z]/, '')});

// chart download
$("#chartCSV").click(function () {chartToCSV()});

// data controls
$("#variables").change(function () {
    let level_div = $("#levels");
    level_div.empty();
    $.ajax({
        url: `${apiServer}/ajax/getLevelsForVar/`,
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
$("#dates").change(function () {clearMap();update();getDrawnChart(drawnItems)});
$('#charttype').change(function () {makechart()});
$("#levels").change(function () {clearMap();update()});
$("#regions").change(function () {changeregions('region')});
$("#countriesGO").click(function () {changeregions('country')});

// display controls
$("#display").click(function() {$("#displayopts").toggle();});
$("#cs_min").change(function () {if ($("#use_csrange").is(":checked")) {clearMap();update()}});
$("#cs_max").change(function () {if ($("#use_csrange").is(":checked")) {clearMap();update()}});
$("#use_csrange").change(function () {clearMap();update()});
$('#colorscheme').change(function () {clearMap();update();});
$("#opacity").change(function () {layerGFS.setOpacity($(this).val())});
$('#gjClr').change(function () {styleGeoJSON()});
$("#gjOp").change(function () {styleGeoJSON()});
$("#gjWt").change(function () {styleGeoJSON()});
$('#gjFlClr').change(function () {styleGeoJSON()});
$("#gjFlOp").change(function () {styleGeoJSON()});