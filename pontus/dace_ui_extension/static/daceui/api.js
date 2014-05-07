
function after_execution(url){
    $.getJSON(url, {}, function(data) {});
};

$(function() {
        $(document).on('click', '.pager li a', function() {
              var target = $(this).closest('.pager').data('target');
              var url = $(this).attr('href');
              $.get(url, {}, function(data) {
                $(target).html($(data).find(target).html());
                $("html, body").animate({ scrollTop: 0 }, "slow");
              });
              return false;
        });

        $(document).on('click', '.dace-action', function(){
              var target = $(this).closest('.dace-action').data('target')+'-modal';
              var url = $(this).attr('href');
              $.get(url,{tomerge:'True', coordinates:'main'}, function(data) {
                var action_body = $($(data).find('.pontus-main')).html()
                var scripts = [];
                $($(target).find('.modal-body')).html(action_body);
                // execute inline scripts
                $.buildFragment([data], document, scripts);
                  if (scripts.length) {
                    $.each(scripts, function() {
                      $.globalEval( this.text || this.textContent || this.innerHTML || "" );
                   });
                };
                
                deform.processCallbacks();
                $(target).modal('show');
                $(target).on('shown.bs.modal', function() {$('.mce-tinymce').show();});
              });
              return false;
        });


  $('.current-iteration').addClass('success');

  $('.toggle').on('click', function() {
    $($(this).data('target')).toggle().toggleClass('out').toggleClass('in');
  });
  $($('.toggle').data('target')+'.out').hide();

});
