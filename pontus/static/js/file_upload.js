
function init_input(oid){
	var input = $("#"+oid);
	var file_name = $("#"+oid+"-filename");
	var initialPreviewData = {}
	if(file_name.length>0){
	    var init_caption = file_name.text();
	    initialPreviewData = {
    	  'initialPreview': ("<div class='file-preview-other'>" +
							  "<h2><i class='glyphicon glyphicon-file'></i></h2>" +
							  init_caption + "</div>"),
          'overwriteInitial': true,
          'initialCaption': init_caption,
	    }
	};
    var file_type = input.data('file_type');
    if(typeof file_type === 'undefined'){
       file_type = ''
    };
    
    if (file_type != ''){
    	file_type = JSON.parse(file_type.replace(/'/g, "\""))
    };
    var input_data = {'showUpload': false,
	                  'allowedFileTypes': file_type,
	                  'previewClass': 'pontus-file-preview',
	                  'previewSettings': {image: {width: "auto", height: "90px"},
										  html: {width: "auto", height: "90px"},
										  flash: {width: "auto", height: "90px"},
										  other: {width: "auto", height: "90px"},},
					  };
    $.extend(input_data, initialPreviewData)
	input.fileinput(input_data);
	var file_removed = $("#"+oid+"-dataDel");
	if(file_removed.length>0){
		input.on('filedeleted, fileclear', function(event, key) {
	        file_removed.val('true')
	    });
    }


}