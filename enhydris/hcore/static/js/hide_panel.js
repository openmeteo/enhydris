jQuery(document).ready(function(){

    $("#hidePanel").click(function(){
        $("#leftofmap").hide();
        $("#mapcontent").show();
        $("#hp").attr("src",STATIC_URL+"images/icons/resultset_previous_disabled.png");
        $("#sp").attr("src",STATIC_URL+"images/icons/resultset_next.png");
        $("#hm").attr("src",STATIC_URL+"images/icons/resultset_next.png");
        $("#sm").attr("src",STATIC_URL+"images/icons/resultset_previous_disabled.png");
		$("#leftofmap").css('width', '450px');
		map.resize();
		map.reposition();
        $("#show_stations").removeAttr("disabled");

    });

    $("#showPanel").click(function(){
        $("#leftofmap").show();
		map.resize();
		map.reposition();
        $("#sp").attr("src",STATIC_URL+"images/icons/resultset_next_disabled.png");
        $("#hp").attr("src",STATIC_URL+"images/icons/resultset_previous.png");
        collapse_table();
    });

    $("#hideMap").click(function(){
        $("#mapcontent").hide();
        $("#leftofmap").show();
		$("#leftofmap").css('width', "auto");
        $("#hm").attr("src",STATIC_URL+"images/icons/resultset_next_disabled.png");
        $("#sm").attr("src",STATIC_URL+"images/icons/resultset_previous.png");
        $("#sp").attr("src",STATIC_URL+"images/icons/resultset_next_disabled.png");
        $("#hp").attr("src",STATIC_URL+"images/icons/resultset_previous.png");
        expand_table();
        $("#show_stations").attr("disabled","disabled");
    });

    $("#showMap").click(function(){
        $("#mapcontent").show();
        $("#hm").attr("src",STATIC_URL+"images/icons/resultset_next.png");
        $("#sm").attr("src",STATIC_URL+"images/icons/resultset_previous_disabled.png");
        collapse_table();
		$("#leftofmap").css('width', '450px');
		map.resize();
		map.reposition();
        $("#show_stations").removeAttr("disabled");
    });

    function expand_table(){
		for (i=3;i<8;i++){
			oTable.fnSetColumnVis( i, true );
		}
    }
    function collapse_table(){
		for (i=3;i<8;i++){
			oTable.fnSetColumnVis( i, false );
		}
    }
});
