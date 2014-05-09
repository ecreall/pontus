
function after_execution(url){
    $.getJSON(url, {}, function(data) {});
};

function update_action(url){
              var toreplay = $(this).closest('.dace-action').data('toreplay');
              var actionid = $(this).closest('.dace-action').data('actionid');
              var target = $(this).closest('.dace-action').data('target')+'-modal';
              if (Boolean(toreplay)){$(target).modal('show'); return false}
              var url = $(this).closest('.dace-action').data('updateurl');
              $.getJSON(url,{tomerge:'True', coordinates:'main'}, function(data) {
                var action_body = data['body']
                var js_links = data['js_links'];
                var css_links = data['css_links'];
                //start: source (http://www.hunlock.com/blogs/Howto_Dynamically_Insert_Javascript_And_CSS)
                var headID = document.getElementsByTagName("head")[0]; 
                for (js in js_links){
                    var newScript = document.createElement('script');
                    newScript.type = 'text/javascript';
                    newScript.src = js;
                    headID.appendChild(newScript);
                };
                for (css in css_links){
                    var cssNode = document.createElement('link');
                    cssNode.type = 'text/css';
                    cssNode.rel = 'stylesheet';
                    cssNode.href = css;
                    headID.appendChild(cssNode);
                };
                //end: source
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

    $(document).on('click', '.dace-action', update_action);


    $('.current-iteration').addClass('success');

    $('.toggle').on('click', function() {
       $($(this).data('target')).toggle().toggleClass('out').toggleClass('in');
      });

    $($('.toggle').data('target')+'.out').hide();

});
