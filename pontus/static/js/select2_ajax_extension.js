
function remove_btn_template(clear_title){
    return  "<span role=\"presentation\" class=\"select2-remove\">"+
                      "<span title=\"" + clear_title + "\" class=\"glyphicon glyphicon-remove\">"+
                      "</span></span>"
}


function default_item_template(item){
   return item.text;
};


function default_selection_template(item){
   var markup = item.text || item.id;
   return markup
}


var select2_ajax_templates = {
                 'default_item_template': default_item_template,
                 'default_selection_template': default_selection_template,
           }


function get_context_data(id){
	 var contextData = {};
	 var element = $(id);
	 var form = $(element.parents('.deform-seq-item').first());
	 if (form == null){
	 	form = $(element.parents('form').first());
	 };
     var contexts = element.data("context").split(",");
     $.map(contexts, function (c) {
         var name = c.trim();
         var value = form.find("[name='" + name + "']").val();
         if (value) {
           contextData[name] = value;
        }
     }); 
     contextData['source'] = element.attr('name')
     return contextData
}


function add_clear_btn(select_field, clear_title){
    if (! clear_title){
      clear_title = "Clear"
    }

    var btn_container = $($(select_field.parents('div').first()).find('.select2.select2-container.select2-container--default').first());
    btn_container.append(remove_btn_template(clear_title));
    var btn = $(btn_container.find('.select2-remove').first());
    btn.on('click', function(){
      var event = jQuery.Event("change");
      event.dt_update = true;
      select_field.val("").trigger(event);
    })
}