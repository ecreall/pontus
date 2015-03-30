
function init_input(oid){
	var input = $("#"+oid);
    var file_type = input.data('file_type');
    if(typeof file_type === 'undefined'){
       file_type = ''
    };
    
    if (file_type != ''){
    	file_type = JSON.parse(file_type.replace(/'/g, "\""))
    };
    input.fileinput({'showUpload': false,
	                  'allowedFileTypes': file_type,
	                  'previewClass': 'pontus-file-preview',
	                  'previewSettings': {image: {width: "auto", height: "90px"},
										  html: {width: "auto", height: "90px"},
										  flash: {width: "auto", height: "90px"},
										  other: {width: "auto", height: "90px"},},
					  });
}