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

  $('.current-iteration').addClass('success');

  $('.toggle').on('click', function() {
    $($(this).data('target')).toggle().toggleClass('out').toggleClass('in');
  });
  $($('.toggle').data('target')+'.out').hide();

});
