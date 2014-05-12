function after_execution(url){
    $.getJSON(url, {}, function(data) {});
};

function update_action(url){
              var toreplay = $(this).closest('.dace-action').data('toreplay');
              var target = $(this).closest('.dace-action').data('target')+'-modal';
              if (Boolean(toreplay)){$(target).modal('show'); return false}
              var url = $(this).closest('.dace-action').data('updateurl');
              $.getJSON(url,{tomerge:'True', coordinates:'main'}, function(data) { 
                 var action_body = data['body'];
                 $($(target).find('.modal-body')).html(action_body);
                 $(target).modal('show');
                 try {
                      deform.processCallbacks();
                  }
                 catch(err) {};
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
