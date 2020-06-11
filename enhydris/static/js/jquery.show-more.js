(function ( $ ) {
    
    /*
    Plugin: ShowMore
    author: dtasic@gmail.com
    */
    
    $.fn.showMore = function (options) {
        
        "use strict";
        
        var currentelem = 1;
        
        this.each(function(){
            
            var currentid = '';
            var element = $(this);
            var auto = parseInt(element.innerHeight())/2;
            var fullheight = element.innerHeight();
            var maxWidth = element.css('width');
            var settings = $.extend({
                minheight: auto,
                buttontxtmore: "show more",
                buttontxtless: "show less",
                buttoncss: "showmore-button",
                animationspeed: auto       
            }, options );        
            
            element.attr('id') != undefined ? currentid = element.attr('id') : currentid = currentelem;
            element.wrap( "<div id='showmore-"+currentid+"' data-showmore"+(maxWidth == '0px' ? "" : " style='max-width:"+maxWidth+";'")+"></div>" );
            
            if (element.parent().not('[data-showmore]')) {
            
                if (fullheight > settings.minheight) {
                    
                    element.css('min-height', settings.minheight).css('max-height', settings.minheight).css('overflow', 'hidden');
                    var showMoreButton = $("<div />", {
                        id: "showmore-button-"+currentid,
                        "class": settings.buttoncss,
                        click: function() {

                            if (element.css('max-height') != 'none') {
                                element.css('height', settings.minheight).css('max-height', '').animate({height:fullheight}, settings.animationspeed, function () { showMoreButton.html(settings.buttontxtless); });
                            } else {
                                element.animate({height:settings.minheight}, settings.animationspeed, function () { showMoreButton.html(settings.buttontxtmore); element.css('max-height', settings.minheight); });
                            }
                        },
                        html: settings.buttontxtmore
                    });

                    element.after(showMoreButton);

                }
                
                currentelem++;
                
            }
            
        });
        
        return this;
        
    };

}(jQuery));
