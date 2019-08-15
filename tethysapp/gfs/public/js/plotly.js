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

    let values = {
        x: x,
        y: y,
        title: data['meta']['name'],
        mode: 'lines+markers',
        type: 'scatter'
    };
    Plotly.newPlot('chart', [values], layout);
}

function plotlyMultilineSeries(data) {
    let index;
    let x = [];
    let max = [];
    let mean = [];
    let min = [];

    if ($("#charttype").val().includes('year')) {
        index = 0;
    } else {
        index = 1;
    }

    let layout = {
        title: data['meta']['name'] + ' v Time ' + '(' + data['meta']['seriesmsg'] + ')',
        xaxis: {title: 'Time'},
        yaxis: {title: 'Units - ' + data['meta']['units']}
    };

    for (let i = 0; i < data['stats'][index].length; i++) {
        x.push(data['stats'][index][i][0]);
        min.push(data['stats'][index][i][1]);
        mean.push(data['stats'][index][i][2]);
        max.push(data['stats'][index][i][3]);
    }

    let values = [
        {x: x, y: min, name: 'Minimum', mode: 'lines+markers', type: 'scatter'},
        {x: x, y: mean, name: 'Average', mode: 'lines+markers', type: 'scatter'},
        {x: x, y: max, name: 'Maximum', mode: 'lines+markers', type: 'scatter'},
    ];
    Plotly.newPlot('chart', values, layout);
}

function plotlyBoxplotSeries(data) {
    let index;
    let values = [];

    if ($("#charttype").val().includes('year')) {
        index = 2;
    } else {
        index = 3;
    }

    let layout = {
        title: data['meta']['name'] + ' v Time ' + '(' + data['meta']['seriesmsg'] + ')',
        xaxis: {title: 'Time'},
        yaxis: {title: 'Units - ' + data['meta']['units']}
    };

    for (let i = 0; i < data['stats'][index].length; i++) {
        values.push({
            x: data['stats'][index][i][0],
            y: data['stats'][index][i][1],
            name: data['stats'][index][i][0],
            type: 'box'
        })
    }
    Plotly.newPlot('chart', values, layout);
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

        // decide which ajax url you need based on drawing type
        $.ajax({
            url: '/apps/' + app + '/ajax/getChart/',
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
        loc_type: 'VectorGeometry'
    };

    if (selectedregion === 'lastregion') {
        // if we want to update, change the region to the last completed region
        data['vectordata'] = chosenRegion;
    } else if (selectedregion === 'customshape') {
        data['vectordata'] = selectedregion;
        chosenRegion = selectedregion;
    } else {
        // otherwise, the new selection is the current region on the chart
        data['vectordata'] = selectedregion;
        chosenRegion = selectedregion;
    }

    $.ajax({
        url: '/apps/' + app + '/ajax/getChart/',
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
    let data = chartdata['timeseries'];
    let csv = "data:text/csv;charset=utf-8," + data.map(e => e.join(",")).join("\n");
    let link = document.createElement('a');
    link.setAttribute('href', encodeURI(csv));
    link.setAttribute('target', '_blank');
    link.setAttribute('download', 'gldastimeseries.csv');
    document.body.appendChild(link);
    link.click();
    $("#a").remove()
}