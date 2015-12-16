

var _URL = window.URL || window.webkitURL;

function init_reader(input_id, image){
  if (window.FileReader) {
    $('#'+input_id).change(function() {
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
          var file_removed = $("#"+input_id+"-dataDel");
          file_removed.val(false)
        };
      } else {
        showMessage("Please choose an image file.");
      }
    });
  } else {
    $('#'+input_id).addClass("hide");
  }

};

function readImg(input_id){
  var image = $('#'+input_id+'-img');
  var size = {max_height: parseInt(image.data('max_height')), 
              max_width: parseInt(image.data('max_width')), 
              min_width: parseInt(image.data('min_width')), 
              min_height: parseInt(image.data('min_height'))};
  var dataHeight = $('#'+input_id+'-dataHeight'),
      dataWidth = $('#'+input_id+'-dataWidth'),
      dataX = $('#'+input_id+'-dataX'),
      dataY = $('#'+input_id+'-dataY'),
      dataR = $('#'+input_id+'-dataR'),
      dataUID = $('#'+input_id+'-uid'),
      cropper;

  var current_width = parseFloat(dataWidth.val()),
      current_height = parseFloat(dataHeight.val()),
      current_y = parseFloat(dataY.val()),
      current_x = parseFloat(dataX.val()),
      current_rotate = parseFloat(dataR.val())

  var options = {
    autoCropArea: 1,
    maxWidth: size.max_width == -1 && Infinity || size.max_width,
    minWidth:size.min_width == -1 && 0 || size.min_width,
    maxHeight:size.max_height == -1 && Infinity || size.max_height,
    minHeight:size.min_height == -1 && 0 ||  size.min_height,
    data: {
      width: current_width,
      height: current_height,
      y: current_y,
      x: current_x,
      rotate: current_rotate
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
      dataX.val(data.x);
      dataY.val(data.y);
      if (dataR.val() == ''){
          dataR.val('0')
      };
    },
  }

  image.cropper(options);
  cropper = image.data("cropper");

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
    dataR.val(parseFloat(dataR.val())+90);
  });

  $('#'+input_id+'-rotateRight').click(function() {
    image.cropper("rotate", 90);
    dataR.val(parseFloat(dataR.val())-90);
  });

  $('#'+input_id+'-remove').click(function() {
    var css =  $('#'+input_id).attr('class');
      $('#'+input_id).replaceWith('<input accept=\"image/*\" type=\"file\" name=\"upload\" class=\"'+css+'\" id=\"'+input_id+'\"/>');
      $('#'+input_id).css('display', 'none');
      image.attr('src', '#');
      image.cropper("destroy");
      dataUID.val('');
      dataX.val('');
      dataY.val('');
      dataWidth.val('');
      dataHeight.val('');
      image.cropper(options);
      init_reader(input_id, image);
      var file_removed = $("#"+input_id+"-dataDel");
      file_removed.val(true)
  });
  
    init_reader(input_id, image);

};