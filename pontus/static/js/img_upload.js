

var _URL = window.URL || window.webkitURL;


function readImg(input_id){
  var image = $('#'+input_id+'-img');
  var size = {max_height: parseInt(image.data('max_height')), 
              max_width: parseInt(image.data('max_width')), 
              min_width: parseInt(image.data('min_width')), 
              min_height: parseInt(image.data('min_height'))};
  var dataHeight = $('#'+input_id+'-dataHeight'),
      dataWidth = $('#'+input_id+'-dataWidth'),
      console = window.console || {log:$.noop},
      cropper;

  image.cropper({
    autoCropArea: 1,
    maxWidth: size.max_width == -1 && Infinity || size.max_width,
    minWidth:size.min_width == -1 && 0 || size.min_width,
    maxHeight:size.max_height == -1 && Infinity || size.max_height,
    minHeight:size.min_height == -1 && 0 ||  size.min_height,
    data: {
      width: size.max_width,
      height: size.max_height
    },
    preview: '#'+input_id+'-preview .preview',

    // multiple: true,
    // autoCrop: false,
    // dragCrop: false,
    // dashed: false,
    // modal: false,
    // movable: false,
    // resizable: false,
    // zoomable: false,
    // rotatable: false,
    // checkImageOrigin: false,

    // maxWidth: 480,
    // maxHeight: 270,
    // minWidth: 160,
    // minHeight: 90,

    done: function(data) {
      dataHeight.val(data.height);
      dataWidth.val(data.width);
      //var dataURL = image.cropper("getDataURL");
      //var blob = dataURItoBlob(dataURL);
      //cant set input.files attribute (for security reasons)
    },
  });

  cropper = image.data("cropper");

  image.on({
    "build.cropper": function(e) {
      console.log(e.type);
      // e.preventDefault();
    },
    "built.cropper": function(e) {
      console.log(e.type);
      // e.preventDefault();
    },
    "dragstart.cropper": function(e) {
      console.log(e.type);
      // e.preventDefault();
    },
    "dragmove.cropper": function(e) {
      console.log(e.type);
      // e.preventDefault();
    },
    "dragend.cropper": function(e) {
      console.log(e.type);
      // e.preventDefault();
    }
  });

  $('#'+input_id+'-clear').click(function() {
    image.cropper("clear");
  });

  $('#'+input_id+'-destroy').click(function() {
    image.cropper("destroy");
  });

  $('#'+input_id+'-move').click(function() {
    image.cropper("setDragMode", "move");
  });

  $('#'+input_id+'-crop').click(function() {
    image.cropper("setDragMode", "crop");
  });
  
  $('#'+input_id+'-zoomIn').click(function() {
    image.cropper("zoom", 0.1);
  });

  $('#'+input_id+'-zoomOut').click(function() {
    image.cropper("zoom", -0.1);
  });

  $('#'+input_id+'-rotateLeft').click(function() {
    image.cropper("rotate", -90);
  });

  $('#'+input_id+'-rotateRight').click(function() {
    image.cropper("rotate", 90);
  });

  var inputImage = $('#'+input_id);

  if (window.FileReader) {
    inputImage.change(function() {
      var fileReader = new FileReader(),
          files = this.files,
          file;

      if (!files.length) {
        return;
      }

      file = files[0];

      if (/^image\/\w+$/.test(file.type)) {
        fileReader.readAsDataURL(file);
        fileReader.onload = function () {
          image.cropper("reset", true).cropper("replace", this.result);
        };
      } else {
        showMessage("Please choose an image file.");
      }
    });
  } else {
    inputImage.addClass("hide");
  }

};