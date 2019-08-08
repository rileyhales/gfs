let uploaded_shp = false;

function uploadShapefile() {
    let files = $('#shapefile-upload')[0].files;

    if (files.length !== 4) {
        alert('The files you selected were rejected. Upload exactly 4 files ending in shp, shx, prj and dbf.');
        return
    }

    let data = new FormData();
    Object.keys(files).forEach(function (file) {
        data.append('files', files[file]);
    });

    let loadgif = $("#loading");
    loadgif.show();
    $.ajax({
        url: '/apps/' + app + '/ajax/uploadShapefile/',
        type: 'POST',
        data: data,
        dataType: 'json',
        processData: false,
        contentType: false,
        success: function (response) {
            uploaded_shp = true;
            loadgif.hide();
            $("#shp-modal").modal('hide');
            getGeoServerGJ(response['gsworksp'], response['shpname'], response['gsurl']);
        },
    });
}

$("#uploadshp").click(function () {uploadShapefile();});
$("#customShpChart").click(function () {
    if (uploaded_shp) {
        getShapeChart('customshape')
    } else {
        if (confirm('You need to upload a shapefile first. Would you like to upload one?')){
            $("#shp-modal").modal('show');
        }
    }
});