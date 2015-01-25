
function readImg(input) {
        var img_tag = $('#'+$(input).attr('id')+'-img');
        var width = parseInt(img_tag.data('width'));
        var height = parseInt(img_tag.data('height'));
        if (input.files && input.files[0]) {
            var reader = new FileReader();
            reader.onload = function (e) {
                img_tag.attr('src', e.target.result)
                        .width(width)
                        .height(height);
            };

            reader.readAsDataURL(input.files[0]);
        }
    };