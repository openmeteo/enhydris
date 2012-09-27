$(document).ready(function() {
  $('.hide_disable_toggler').click(function() {
    var hd = $(this).parent().prev().children();
    if ( hd.is(':disabled') ) { 
      hd.removeAttr("disabled"); 
      if ( hd.attr('id') == 'district' ) {
        render_pref_filter(hd.attr('value'));
      } else if  (hd.attr('id') == 'political_division') {
        render_dist_filter(hd.attr('value'));
      }
    } else {
        hd.attr("disabled", true); 
        if ( hd.attr('id') == 'district' ) {
            $('#prefecture').attr("disabled", true);
        } else if (hd.attr('id') == 'political_division') {
            $('#district').attr("disabled", true);
            $('#prefecture').attr("disabled", true);
        }
    }
  })
});
