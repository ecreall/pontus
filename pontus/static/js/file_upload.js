
function readImg() {
        var input = $(this);
        var img = $('#'+input.attr(id)+'-img');
        if (input.files && input.files[0]) {
            var reader = new FileReader();

            reader.onload = function (e) {
                img.attr('src', e.target.result)
                    .width(400)
                    .height(200);
            };

            reader.readAsDataURL(input.files[0]);
        }
    };