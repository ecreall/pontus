


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
                 if (action_body){
                     $($(target).find('.modal-body')).html(action_body);
                     $(target).modal('show');
                     try {
                          deform.processCallbacks();
                      }
                     catch(err) {};
                  }else{
                     location.reload();
                     return false
                  }
              });
              return false;
};

$(function() {

$('ul.dropdown-menu [data-toggle=dropdown]').on('click', function(event) {
    // Avoid following the href location when clicking
    event.preventDefault();
    // Avoid having the menu to close when clicking
    event.stopPropagation();
    // If a menu is already open we close it
    //$('ul.dropdown-menu [data-toggle=dropdown]').parent().removeClass('open');
    // opening the one you clicked on
    $(this).parent().addClass('open');

    var menu = $(this).parent().find("ul");
    var menupos = menu.offset();

    if ((menupos.left + menu.width()) + 30 > $(window).width()) {
        var newpos = - menu.width();
    } else {
        var newpos = $(this).parent().width();
    }
    menu.css({ left:newpos });

});

    $(document).on('click', '.pager li a', function() {
          var target = $(this).closest('.pager').data('target');
          var url = $(this).attr('href');
          $.get(url, {}, function(data) {
                $(target).html($(data).find(target).html());
                $("html, body").animate({ scrollTop: $(target).offset().top }, "slow");
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
