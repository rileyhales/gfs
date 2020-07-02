let chartdata = null;
Plotly.newPlot('chart', [], {title: 'No Data Selected', xaxis: {range: [-100, 100]}, yaxis: {range: [-100, 100]}});

function plotlyTimeseries(data) {
    let x = [];
    let y = [];
    let layout = {
        title: data['meta']['name'] + ' v Time ' + '(' + data['meta']['seriesmsg'] + ')',
        xaxis: {title: 'Time'},
        yaxis: {title: 'Units - ' + data['meta']['units']}
    };

    for (let i = 0; i < data['timeseries'].length; i++) {
        x.push(data['timeseries'][i][0]);
        y.push(data['timeseries'][i][1]);
    }
    console.log(x);

    let values = {
        x: x,
        y: y,
        title: data['meta']['name'],
        mode: 'lines+markers',
        type: 'scatter'
    };
    Plotly.newPlot('chart', [values], layout);
    let chart = $("#chart");
    chart.css('height', 500);
    Plotly.Plots.resize(chart[0]);
}

function getDrawnChart(drawnItems) {
    // if there's nothing to get charts for then quit
    let geojson = drawnItems.toGeoJSON()['features'];
    if (geojson.length === 0 && chosenRegion === '') {
        return
    }

    // if there's geojson data, update that chart
    if (geojson.length > 0) {
        $("#chart").html('<div class="load"><img src="https://media.giphy.com/media/jAYUbVXgESSti/giphy.gif"></div>');

        //  Compatibility if user picks something out of normal bounds
        let coords = geojson[0]['geometry']['coordinates'];
        for (let i in coords.length) {
            if (coords[i] < -180) {
                coords[i] += 360;
            }
            if (coords[i] > 180) {
                coords[i] -= 360;
            }
        }

        // setup a parameters json to generate the right timeserie
        let data = {
            coords: coords,
            variable: $("#variables").val(),
            level: $("#levels").val(),
            loc_type: geojson[0]['geometry']['type']
        };

        $("#chart_modal").modal('show');
        // decide which ajax url you need based on drawing type
        $.ajax({
            url: URL_getChart,
            data: JSON.stringify(data),
            dataType: 'json',
            contentType: "application/json",
            method: 'POST',
            success: function (result) {
                chartdata = result;
                makechart();
            }
        })
        // If there isn't any geojson, then you actually should refresh the shapefile chart (ie the data is the lastregion)
    } else {
        getShapeChart('lastregion');
    }
}

function getShapeChart(selectedregion) {
    // if the time range is all times then confirm before executing the spatial averaging
    if ($("#dates").val() === 'alltimes') {
        if (!confirm("Computing a timeseries of spatial averages for all available data requires over 850 GIS operations. This may result in a long wait (20+ seconds) or cause errors. Please confirm you want to proceed.")) {
            return
        }
    }
    drawnItems.clearLayers();
    $("#chart").html('<div class="load"><img src="https://media.giphy.com/media/jAYUbVXgESSti/giphy.gif"></div>');

    // setup a parameters json to generate the right timeseries
    let data = {
        variable: $("#variables").val(),
        level: $("#levels").val(),
    };

    if (selectedregion === 'lastregion') {
        // if we want to update, change the region to the last completed region
        data['loc_type'] = chosenRegion;
    } else if (selectedregion === 'Shapefile') {
        data['loc_type'] = selectedregion;
        chosenRegion = selectedregion;
    } else {
        // otherwise, the new selection is the current region on the chart
        data['loc_type'] = selectedregion;
        chosenRegion = selectedregion;
    }

    $("#chart_modal").modal('show');
    $.ajax({
        url: URL_getChart,
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: "application/json",
        method: 'POST',
        success: function (result) {
            chartdata = result;
            makechart();
        }
    })
}

function makechart() {
    if (chartdata !== null) {
        $("#chart").html('');
        plotlyTimeseries(chartdata);
    }
}

function chartToCSV() {
    if (chartdata === null) {
        alert('There is no data in the chart. Please plot some data first.');
        return
    }
    let data = [];
    let charttype = $("#charttype").val();
    if (charttype === 'timeseries') {
        data = chartdata['timeseries']
    } else {
        let tmp;
        if (charttype === 'yearmulti') {
            tmp = chartdata['stats'][0];
        } else if (charttype === 'monthmulti') {
            tmp = chartdata['stats'][1];
        } else if (charttype === 'yearbox') {
            tmp = chartdata['stats'][2];
        } else if (charttype === 'monthbox') {
            tmp = chartdata['stats'][3];
        }
        for (let i = 0; i < tmp.length; i++) {
            data.push(tmp[i]);
        }
    }
    let csv = "data:text/csv;charset=utf-8," + data.map(e => e.join(",")).join("\n");
    let link = document.createElement('a');
    link.setAttribute('href', encodeURI(csv));
    link.setAttribute('target', '_blank');
    link.setAttribute('download', app + '_timeseries.csv');
    document.body.appendChild(link);
    link.click();
    $("#a").remove()
}

// WHEN YOU CLICK ON THE DOWNLOAD BUTTON- RUN THE DOWNLOAD CSV FUNCTION
$("#chartCSV").click(function () {chartToCSV()});