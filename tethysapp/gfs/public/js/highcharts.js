// Global Highcharts options
Highcharts.setOptions({
    lang: {
        downloadCSV: "Download CSV",
        downloadJPEG: "Download JPEG image",
        downloadPDF: "Download PDF document",
        downloadPNG: "Download PNG image",
        downloadSVG: "Download SVG vector image",
        downloadXLS: "Download XLS",
        loading: "Timeseries loading, please wait...",
        noData: "No Data Selected. Place a point, draw a polygon, or select a region."
    },
});

let chartdata = null;

// Placeholder chart
let chart = Highcharts.chart('highchart', {
    title: {
        align: "center",
        text: "Timeseries Data Chart Placeholder",
    },
    series: [{
        data: [],
    }],
    chart: {
        animation: true,
        zoomType: 'x',
        borderColor: '#000000',
        borderWidth: 2,
        type: 'area',
    },
    noData: {
        style: {
            fontWeight: 'bold',
            fontSize: '15px',
            color: '#303030'
        }
    },
});

function newHighchart(data) {
    chart = Highcharts.chart('highchart', {
        title: {
            align: "center",
            text: data['name'] + ' v Time ' + data['type'],
        },
        xAxis: {
            type: 'datetime',
            title: {text: "Time"},
        },
        yAxis: {
            title: {text: data['units']}
        },
        series: [{
            data: data['values'],
            type: "line",
            name: data['name'],
            tooltip: {
                xDateFormat: '%A, %b %e, %Y',
            },
        }],
        chart: {
            animation: true,
            zoomType: 'xy',
            borderColor: '#000000',
            borderWidth: 2,
            type: 'area',

        },

    });
}

function newMultilineChart(data) {
    let charttype = $("#charttype").val();
    let categories;
    if (charttype.includes('month')) {
        categories = 'month'
    } else {
        categories = 'year'
    }
    chart = Highcharts.chart('highchart', {
        title: {
            align: "center",
            text: data['name'] + ' v Time ' + data['type'],
        },
        xAxis: {
            title: {text: "Time"},
            categories: data['categories'][categories],
        },
        yAxis: {
            title: {text: data['units']}
        },
        series: [
            {
                data: data['multiline'][charttype]['min'],
                type: "line",
                name: 'Yearly Minimum',
            },
            {
                data: data['multiline'][charttype]['max'],
                type: "line",
                name: 'Yearly Maximum',
            },
            {
                data: data['multiline'][charttype]['mean'],
                type: "line",
                name: 'Yearly Average',
            }
        ],
        chart: {
            animation: true,
            zoomType: 'xy',
            borderColor: '#000000',
            borderWidth: 2,
            type: 'area',

        },

    });
}

function newBoxPlot(data) {
    let charttype = $("#charttype").val();
    let categories;
    if (charttype.includes('month')) {
        categories = 'month'
    } else {
        categories = 'year'
    }
    chart = Highcharts.chart('highchart', {
        chart: {
            type: 'boxplot',
            animation: true,
            zoomType: 'xy',
            borderColor: '#000000',
            borderWidth: 2,
        },
        title: {align: "center", text: data['name'] + ' Statistics ' + data['type']},
        legend: {enabled: false},
        xAxis: {
            title: {text: 'Time'},
            categories: data['categories'][categories],
        },
        yAxis: {title: {text: data['units']}},
        series: [{
            name: data['name'],
            data: data['boxplot'][charttype],
            tooltip: {xDateFormat: '%b',},
        }]

    });
}

function getDrawnChart(drawnItems) {
    // if there's nothing to get charts for then quit
    let geojson = drawnItems.toGeoJSON()['features'];
    if (geojson.length === 0 && currentregion === '') {
        return
    }

    // if there's geojson data, update that chart
    if (geojson.length > 0) {
        chart.hideNoData();
        chart.showLoading();

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

        // setup a parameters json to generate the right timeseries
        let data = {
            coords: coords,
            geojson: geojson[0],
            variable: $('#variables').val(),
            time: $("#dates").val(),
        };

        // decide which ajax url you need based on drawing type
        let url;
        let drawtype = geojson[0]['geometry']['type'];
        if (drawtype === 'Point') {
            url = '/apps/gldas/ajax/getPointSeries/';
        } else {
            url = '/apps/gldas/ajax/getPolygonAverage/';
        }

        $.ajax({
            url: url,
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
        if (!confirm("Computing a timeseries of spatial averages for all available times requires over 200 iterations of file conversions and geoprocessing operations. This may result in a long wait (15+ seconds) or cause errors. Are you sure you want to continue?")) {
            return
        }
    }

    drawnItems.clearLayers();
    chart.hideNoData();
    chart.showLoading();

    let data = {
        variable: $('#variables').val(),
        time: $("#dates").val(),
        region: selectedregion,
    };
    if (selectedregion === 'lastregion') {
        // if we want to update, change the region to the last completed region
        data['region'] = currentregion;
    } else {
        // otherwise, the new selection is the current region on the chart
        currentregion = selectedregion;
    }

    $.ajax({
        url: '/apps/gldas/ajax/getShapeAverage/',
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
        let type = $("#charttype").val();
        if (type === 'timeseries') {
            newHighchart(chartdata);
        } else if (type === 'yearmulti' || type === 'monthmulti') {
            newMultilineChart(chartdata);
        } else if (type === 'yearbox' || type === 'monthbox') {
            newBoxPlot(chartdata);
        }
    }
}
