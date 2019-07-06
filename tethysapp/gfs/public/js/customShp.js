let uploaded_shp = false;

function uploadShapefile() {
    let files = $('#shapefile-upload')[0].files;

    if (files.length !== 4) {
        alert('The files you selected were rejected. Upload exactly 4 files ending in shp, shx, prj and dbf.')
        return
    }

    let data = new FormData();
    Object.keys(files).forEach(function (file) {
        data.append('files', files[file]);
    });

    let loadgif = $("#loading");
    loadgif.show();
    $.ajax({
        url: '/apps/gfs/ajax/uploadShapefile/',
        type: 'POST',
        data: data,
        dataType: 'json',
        processData: false,
        contentType: false,
        success: function () {
            uploaded_shp = true;
            loadgif.hide();
            $("#shp-modal").modal('hide');
        },
    });
}

$("#uploadshp").click(function () {
    uploadShapefile()
});

$("#customShpTS").click(function () {
    if (uploaded_shp) {
        getShapeChart('customshape')
    } else {
        alert('You need to upload a shapefile first. Use this interface to upload a shapefile then try again');
        $("#shp-modal").modal('show');
    }
});