$(document).ready(function() {
  $('.collapse_toggler').click(function() {
    var anchor = $(this);
    var hd = anchor.parent().next().children();
    var img = anchor.children();
    hd.toggle(function(){
        var anchor = $('.collapse_toggler');
        anchor.toggleClass("expand");
        if(anchor.hasClass("expand")){
            img.attr({ 
                src: MEDIA_URL+"images/icons/folder.png",
            });

        }else{
            img.attr({ 
                src: MEDIA_URL+"images/icons/folder_open.png",
            });
        }
    });
  });
});
