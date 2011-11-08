/* Enhydris, Copyright 2011 National Technical University of
   Athens. */
function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi,
        function(m,key,value) {
            vars[key] = decodeURI(value);
        });
    return vars;
}

Object.extend = function(destination, source) {
    for (var property in source)
        destination[property] = source[property];
    return destination;
};
var map = null;
var apopup = null;
function get_attribute(afeature, attrib)
{
    if(!afeature.cluster)
        return afeature.attributes[attrib];
    else
        return afeature.cluster[0].attributes[attrib];
}

function InvokePopup(afeature) {
    var aurl;
    if(get_attribute(afeature, "gis_objects"))
        aurl = ENHYDRIS_ROOT_URL+"gis_objects/b/";
    else
        aurl = ENHYDRIS_ROOT_URL+"stations/b/";
    apoint = afeature.geometry.getBounds().getCenterLonLat();
    map.panTo(apoint);
    $.get(aurl+get_attribute(afeature, "id")+'/', {}, function(data){
        var amessage = '';
        amessage=data;
        apopup = new OpenLayers.Popup(get_attribute(afeature, "name"), apoint, new OpenLayers.Size(190,150), amessage, true);
        apopup.setBorder("2px solid");  
        apopup.setBackgroundColor('#EEEEBB');
        map.addPopup(apopup, true);
        HideProgress('popup');
    });
}
function InvokeTooltip(atitle){
    document.getElementById("map").title = atitle;
}
function HideTooltip(atitle){
    document.getElementById("map").title = '';
}
function CreateLayer(AName, ObjectName, AFillColor, AStrokeColor,
                     LayerName, isStation, agtype){
    if(map_mode==1 || map_mode==11 ){
        var params = getUrlVars();
    }
    else if(map_mode==2){
        var params = {'gentity_id': agentity_id};
    }
    else if(map_mode==12){
        var params = {'gentity_id': 0, 'other_id': agentity_id};
    }
    params['request'] = 'GetFeature';
    params['srs'] = 'EPSG:4326';
    params['version'] = '1.0.0';
    params['service'] = 'WFS';
    params['format'] = 'WFS';
    var labelvalue = "";
    var labeling_opts = {
            label : labelvalue, fontColor: "#504065",
            fontSize: "9px", fontFamily: "Verdana, Arial",
            fontWeight: "bold", labelAlign: "cm" 
    };
    var general_opts = {
            externalGraphic: MEDIA_URL+"${aicon}",
            graphicWidth: 21, graphicHeight:25, graphicXOffset:-10,
            graphicYOffset: -25, fillOpacity: 1,
            fillColor: AFillColor,
            strokeColor: AStrokeColor,
            strokeWidth: 3, strokeOpacity: 0.7,
            srokeLinecap: "round"
    };
    general_opts = Object.extend(general_opts, labeling_opts);
    AURL = ENHYDRIS_ROOT_URL+LayerName+"/kml/";
    if(ObjectName=='aqueduct_lines'){
        var clustering_opts = {distance: 4, threshold: 6};
        var strategy_opts = {ratio: 1024, resFactor: 2};
    }
    else
    {
        var clustering_opts = {distance: 12, threshold: 3};
        var strategy_opts = {ratio: 1.5, resFactor: 2};
    }
    if(!isStation)
        general_opts['graphicYOffset'] =-12;
    var isVisible = true;
    if("gtype" in params)
        if(params['gtype']!=agtype &&(params['gtype']>0 && params['gtype']<8 ))
        {
            isVisible = false;
        }
    if(map_mode==1)
        isVisible = isStation;
    var alayer = new OpenLayers.Layer.Vector(AName,
    { 
        visibility: isVisible,
        strategies: [
                     new OpenLayers.Strategy.BBOX(strategy_opts),
                     new OpenLayers.Strategy.Cluster(clustering_opts)
                    ],
        protocol: new OpenLayers.Protocol.HTTP({
                        url: AURL,
                        format: new OpenLayers.Format.KML(),
                        params: params}),
        projection: new OpenLayers.Projection("EPSG:4326"),
        formatOptions: { extractAttributes:true },
        styleMap: new OpenLayers.StyleMap({
            "default": new OpenLayers.Style(
                  OpenLayers.Util.applyDefaults(general_opts,
                        OpenLayers.Feature.Vector.style["default"]),
                        {context: {aname: function(feature) { return get_attribute(feature, "name"); },
                                   aicon: function(feature) {
                                       if(ObjectName=='boreholes')
                                           return 'custom/borehole_marker.png';
                                       else if(ObjectName=='pumps')
                                           return 'custom/pump_marker.png';
                                       else if(ObjectName=='refineries')
                                           return 'custom/refinary_marker.png';
                                       else if(ObjectName=='springs')
                                           return 'custom/spring_marker.png';
                                       else if(ObjectName=='aqueduct_nodes')
                                           return 'custom/aqueduct_node_marker.png';
                                       else if(ObjectName=='aqueduct_lines')
                                           return '';
                                       else if(ObjectName=='reservoirs')
                                           return '';
                                       if(get_attribute(feature, "type_id")==marker_categories['id'][0])
                                           return marker_categories['icon'][0];
                                       else if(get_attribute(feature, "type_id")==marker_categories['id'][1])
                                           return marker_categories['icon'][1];
                                       else if(get_attribute(feature, "type_id")==marker_categories['id'][2])
                                           return marker_categories['icon'][2];
                                       else 
                                           return marker_categories['icon'][3];
                                    }
                                   }}
                        ),
            "select": new OpenLayers.Style(
                  OpenLayers.Util.applyDefaults({
                        externalGraphic: isStation?MEDIA_URL+'images/drop_marker_selected.png':MEDIA_URL+'custom/other_selected.png',
                        graphicWidth: 21, graphicHeight:25, graphicXOffset:-10,
                        graphicYOffset: isStation?-25:-12, fillOpacity: 1}, 
                        OpenLayers.Feature.Vector.style["select"])
                        ),
            "temporary": new OpenLayers.Style(
                  OpenLayers.Util.applyDefaults({
                        graphicWidth: 21, graphicHeight:25, graphicXOffset:-10,
                        strokeColor: "#00aacc",
                        graphicYOffset: isStation?-25:-12, fillOpacity: 0.7}, 
                        OpenLayers.Feature.Vector.style["select"])
                        )
        })
    } );
    alayer.events.register("loadstart", alayer,
        function() { ShowProgress(ObjectName); } );
    alayer.events.register("loadend", alayer,
        function() { HideProgress(ObjectName); } );
    alayer.events.register("loadcancel", alayer,
        function() { HideProgress(ObjectName); } );
    alayer.events.on({
        "featureselected": function(e) {
            ShowProgress('popup');
            InvokePopup(e.feature);
        },
        "featureunselected": function(e) {
            map.removePopup(apopup);
        }
    });
    return alayer;
}
var stations = CreateLayer("Σταθμοί", "stations", '#dd0022', '#990077',"stations", true, 0);
var aqueduct_nodes = CreateLayer("Κόμβοι Υδραγωγείου", "aqueduct_nodes", '#dd0022', '#990077',"gis_objects/aqueduct_nodes", false, 5);
var aqueduct_lines = CreateLayer("Υδραγωγεία", "aqueduct_lines", '#0033aa', '#0033aa',"gis_objects/aqueduct_lines", false, 6);
var reservoirs = CreateLayer("Ταμιευτήρες", "reservoirs", '#001199', '#001177',"gis_objects/reservoirs", false, 7);
var boreholes = CreateLayer("Γεωτρήσεις", "boreholes", '#dd0022', '#990077',"gis_objects/boreholes", false, 1);
var springs = CreateLayer("Πηγές", "springs", '#dd0022', '#990077',"gis_objects/springs", false, 4);
var pumps = CreateLayer("Αντλιοστάσια", "pumps", '#dd0022', '#990077',"gis_objects/pumps", false,2);
var refineries = CreateLayer("Διυλιστήρια", "refineries", '#dd0022', '#990077',"gis_objects/refineries", false, 3);
var categories = [aqueduct_lines, aqueduct_nodes, reservoirs, boreholes, springs, pumps, refineries, stations];
function init() {
    var options = {
        'units' :   "m",
        'numZoomLevels' :   15,
        'sphericalMercator': true,
        'maxExtent': bounds,
        'projection'    :   new OpenLayers.Projection("EPSG:900913"),
        'displayProjection':    new OpenLayers.Projection("EPSG:4326")
    };
    map = new OpenLayers.Map('map', options);
    map.addControl(new OpenLayers.Control.ScaleLine());
    var ANavToolBar = new OpenLayers.Control.NavToolbar();
        map.addControl(ANavToolBar);
    $("div.olControlNavToolbar").css("top","14px");
    $("div.olControlNavToolbar").css("left","11px");
    pzb = new OpenLayers.Control.PanZoomBar();
    pzb.zoomWorldIcon = false;
    map.addControl(pzb);
    map.addControl(new OpenLayers.Control.MousePosition());
    map.addControl(new OpenLayers.Control.OverviewMap());
    ls = new OpenLayers.Control.LayerSwitcher();
    map.addControl(ls);
    map.addLayers(base_layers);
    map.addLayers(categories);
    ls.baseLbl.innerHTML='Base layers';
    ls.dataLbl.innerHTML='Data layers';
    var labelButton = new OpenLayers.Control.Button({ type: OpenLayers.Control.TYPE_TOGGLE,
        title: "Show labels", displayClass: "LabelButtonClass" , trigger: function(){}});  
    labelButton.events.register("activate", labelButton,
        function() { setLayersLabels(true); } );
    labelButton.events.register("deactivate", labelButton,
        function() { setLayersLabels(false); } );
    var panel = new OpenLayers.Control.Panel({displayClass: 'olControlShowLabels' });  
    panel.addControls([labelButton]);  
    panel.activateControl(labelButton);  
    map.addControl(panel); 
    var agentity_id_repr='';
    if(map_mode==2||map_mode==12)
        agentity_id_repr=agentity_id;
    if(map_mode!=12)
        var getboundoptions = {'gentity_id': agentity_id_repr};
    else
        var getboundoptions = {'gentity_id': 0, 'other_id': agentity_id_repr};
    Object.extend(getboundoptions, getUrlVars());
    $.ajax({url: BOUND_URL, data: getboundoptions, method: 'get', 
        success: function(data){
            bounds = OpenLayers.Bounds.fromString(data);
            bounds.transform(new OpenLayers.Projection("EPSG:4326"), new
                                 OpenLayers.Projection("EPSG:900913"));
            if(map_mode==11||map_mode==12)
                $.ajax({url: GIS_OBJECTS_BOUND_URL, data: getboundoptions, method: 'get',
                    success: function(data){
                        var bounds2 = OpenLayers.Bounds.fromString(data);
                        bounds2.transform(new OpenLayers.Projection("EPSG:4326"), new
                                              OpenLayers.Projection("EPSG:900913"));
                        var params = getboundoptions;
                        if(map_mode==11&&!('gtype' in params && params['gtype']>0 && params['gtype']<8)
                           &&!('timeseries' in params)&&!('scheck' in params))
                            bounds.extend(bounds2);
                        else
                            bounds = bounds2;
                        map.zoomToExtent(bounds);
                    },
                    error: function(data){
                        alert('error condition');
                        map.zoomToExtent(bounds);
                    }});
            else
                map.zoomToExtent(bounds);
        }, 
        error: function(data){
            map.zoomToExtent(bounds);
    }});
    var SelectControl = new OpenLayers.Control.SelectFeature(categories, {
          clickout: true, togle: false, multiple: false,
          hover: false});
    var HoverControl = new OpenLayers.Control.SelectFeature(categories, {
          clickout: false, togle: false, multiple: false,
          hover: true, highlightOnly: true, renderIntent: "temporary",
          eventListeners: { beforefeaturehighlighted: function(e){},
                            featurehighlighted: function(e){InvokeTooltip(get_attribute(e.feature, "name"));},
                            featureunhighlighted: function(e){HideTooltip(get_attribute(e.feature, "name"))}
                          }});
    map.addControl(SelectControl);
    map.addControl(HoverControl);
    HoverControl.activate();
    SelectControl.activate();
    ANavToolBar.controls[0].events.on({
        "activate": function(){
            HoverControl.activate();
            SelectControl.activate();
        },
        "deactivate": function(){
            HoverControl.deactivate();
            SelectControl.deactivate();
        }
    });
    ANavToolBar.controls[0].activate();
    if(legent_displayed)ls.maximizeControl();
}

function ShowProgress(name){
   var aprogress = document.getElementById("map_progress");
   if(aprogress==null)return;
   aprogress.innerHTML=
       "<img src='"+MEDIA_URL+"images/wait16.gif'>";
}

function HideProgress(name){
   var aprogress = document.getElementById("map_progress");
   if(aprogress==null)return;
   aprogress.innerHTML="";
}

function setLayersLabels(value){
    for(i=0;i<categories.length;i++){
        var layer = categories[i];
        var defaultStyle = layer.styleMap.styles["default"].defaultStyle;
        if(value)
            defaultStyle["label"]="${aname}";
        else
            defaultStyle["label"]="";
        layer.styleMap.styles["default"].setDefaultStyle(defaultStyle);
        layer.redraw();
    }
}
