jQuery(document).ready(function(){
    $("#hidePanel").click(function(){
        $("#leftofmap").hide();
        $("#mapcontent").show();
		map.resize();
        $("#hp").attr("src","/site_media/images/icons/resultset_previous_disabled.png");
        $("#sp").attr("src","/site_media/images/icons/resultset_next.png");
        $("#hm").attr("src","/site_media/images/icons/resultset_next.png");
        $("#sm").attr("src","/site_media/images/icons/resultset_previous_disabled.png");
        $("#show_stations").removeAttr("disabled");

    });

    $("#showPanel").click(function(){
        $("#leftofmap").show();
        $("#sp").attr("src","/site_media/images/icons/resultset_next_disabled.png");
        $("#hp").attr("src","/site_media/images/icons/resultset_previous.png");
        collapse_table();
    });

    $("#hideMap").click(function(){
        $("#mapcontent").hide();
        $("#leftofmap").show();
        $("#hm").attr("src","/site_media/images/icons/resultset_next_disabled.png");
        $("#sm").attr("src","/site_media/images/icons/resultset_previous.png");
        $("#sp").attr("src","/site_media/images/icons/resultset_next_disabled.png");
        $("#hp").attr("src","/site_media/images/icons/resultset_previous.png");
        expand_table();
        $("#show_stations").attr("disabled","disabled");
    });

    $("#showMap").click(function(){
        $("#mapcontent").show();
		map.resize();
        $("#hm").attr("src","/site_media/images/icons/resultset_next.png");
        $("#sm").attr("src","/site_media/images/icons/resultset_previous_disabled.png");
        collapse_table();
        $("#show_stations").removeAttr("disabled");
    });

    function expand_table(){
        el = $(".hide_extra");
        el.show();
    }
    function collapse_table(){
        el = $(".hide_extra");
        el.hide();
    }
});
