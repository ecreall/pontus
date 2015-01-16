
function default_item_template(item){
   return item.text;
};


function default_selection_template(item){
   var markup = item.text || item.id;
   return markup
}


var select2_ajac_templates = {
                 'default_item_template': default_item_template,
                 'default_selection_template': default_selection_template,
           }


function get_context_data(id){
	 var contextData = {};
	 var element = $(id);
	 var form = $(element.parents('.deformSeqItem').first());
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