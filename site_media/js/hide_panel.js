jQuery(document).ready(function(){
    $("#hidePanel").click(function(){
        $("#leftofmap").hide();
        $("#mapcontent").show();
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
    
$(document).ready(function (){
        station_list = ""; /* WHAT NOW? */
        gis_page = "gis-server/get_map/station_list/";
        $.post(gis_page, {'station_list': station_list}, placeMap)
        $("#map_data").html("<p>Error contacting GIS server.</p>");
    });

    function placeMap( RContent, RStatus) {
        if ( RStatus == "Success" ) {
            $("#map_data").html(RContent);
        } else {
            $("#map_data").html("<p>Error contacting GIS server.</p>");
        }
    }
