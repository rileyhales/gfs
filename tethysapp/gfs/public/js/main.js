// base.html scripts has additional vars from render context
let csrftoken = Cookies.get('csrftoken');
Cookies.set('instance_id', instance_id);
function csrfSafeMethod(method){return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));}
$.ajaxSetup({beforeSend: function (xhr, settings) {if (!csrfSafeMethod(settings.type) && !this.crossDomain) {xhr.setRequestHeader("X-CSRFToken", csrftoken);}}});

let layerWMS = newWMS();            // adds the wms raster layer
let layerRegion = regionsESRI();        // adds the world region boundaries from esri living atlas
let controlsObj = makeControls();       // the layer toggle controls top-right corner
legend.addTo(mapObj);                   // add the legend graphic to the map
latlon.addTo(mapObj);                   // add the box showing lat and lon to the map
////////////////////////////////////////////////////////////////////////  EVENT LISTENERS
function update() {
    layerWMS = newWMS();
    controlsObj = makeControls();
    legend.addTo(mapObj);
}
function changeregions(firedfrom) {
    let countryJQ = $("#countries");
    let regionJQ = $("#regions");
    if (firedfrom === 'country') {
        let country = countryJQ.val();
        if (!countrieslist.includes(country)) {
            alert('The country "' + country + '" was not found in the list of countries available. Please check spelling and capitalization, and use the input suggestions.');
            return
        }
        regionJQ.val('none');
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

// data controls
$("#variables").change(function () {
    let level_div = $("#levels");
    level_div.empty();
    $.ajax({
        url: URL_levelsForVar,
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
$("#levels").change(function () {clearMap();update()});
$("#regions").change(function () {changeregions('region')});
$("#countriesGO").click(function () {changeregions('country')});

// display controls
$("#display").click(function() {$("#displayopts").toggle();});
$("#cs_min").change(function () {if ($("#use_csrange").is(":checked")) {clearMap();update()}});
$("#cs_max").change(function () {if ($("#use_csrange").is(":checked")) {clearMap();update()}});
$("#use_csrange").change(function () {clearMap();update()});
$('#colorscheme').change(function () {clearMap();update();});
$("#opacity").change(function () {layerWMS.setOpacity($(this).val())});
$('#gjClr').change(function () {styleGeoJSON()});
$("#gjOp").change(function () {styleGeoJSON()});
$("#gjWt").change(function () {styleGeoJSON()});
$('#gjFlClr').change(function () {styleGeoJSON()});
$("#gjFlOp").change(function () {styleGeoJSON()});