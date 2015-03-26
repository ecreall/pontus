
function init_input(oid){

    $("#"+oid).fileinput({'showUpload': false, 
    	                  'previewFileType':'any',
    	                  'previewClass': 'pontus-file-preview',
    	                  'previewSettings': {image: {width: "auto", height: "90px"},
											  html: {width: "auto", height: "90px"},
											  flash: {width: "auto", height: "90px"}}});
}