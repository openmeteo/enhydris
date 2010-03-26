//============================================================================

function StationSelect(stationList)
{
	map.graphics.clear();
	QueryStations(stationList);
}

//============================================================================

function init() {

	//Set proxy params
	esri.config.defaults.io.proxyUrl = "http://" + Server + "/proxy.ashx"; 
	esri.config.defaults.io.alwaysUseProxy = false;
	//Create map, set initial extent
	
	map = new esri.Map("map_data", {nav:true, slider:true, extent: new esri.geometry.Extent( {"xmin" :104010,"ymin" :3785403,"xmax" : 1007943, "ymax" : 4689336},  new esri.SpatialReference({wkid:2100}) ), showInfoWindowOnClick:false});
	var LayerLink = "http://" + Server + "/ArcGIS/rest/services/HydroScope_Stations/MapServer";
	map.addLayer(new esri.layers.ArcGISDynamicMapServiceLayer(LayerLink));
	dojo.connect(map, "onLoad", createToolbar);

	map.height = Math.floor((parseFloat(map.height) + 0.5));
	map.width = Math.floor(parseFloat(map.width) + 0.5);

	initialExtent = map.extent;

	//Initialize symbology for Stations
	defaultSymbol = new esri.symbol.SimpleMarkerSymbol().setColor(new dojo.Color([0,0,255]));
	highlightSymbol = new esri.symbol.SimpleMarkerSymbol().setColor(new dojo.Color([255,0,0]));

	//Listen for click event on the map, when the user clicks on the map call executeQueryTask function.
	 dojo.connect(map, "onClick", executeQueryTask);
	//Build query task on mouse click
	var queryLink = "http://" + Server + "/ArcGIS/rest/services/Hydroscope_Stations/MapServer/0";
	queryTask = new esri.tasks.QueryTask(queryLink);
	query = new esri.tasks.Query();
	query.returnGeometry = true;
	//Select output station fields
	query.outFields = ["objectid","name","water_basin_id","water_division_id","political_division_id","owner_id","type_id","descr","is_active","is_automatic","start_date","end_date"]; 

	//Check initial stuff
	var pd = $(document).getUrlParam("political_division");
	var wd =  $(document).getUrlParam("water_division");
	var wb =  $(document).getUrlParam("water_basin");
	var owner =  $(document).getUrlParam("owner");
	var type =  $(document).getUrlParam("type");


	if (pd) {
		QueryPolDiv(pd);
	}

	if (wb) {
		QueryWaterBas(wb);
	}

	if (wd) { 
		QueryWaterDiv(wd);
	}

//	if (owner) {
//		QueryOwner(owner);
//	}
//
//	if (type) {
//		QueryType(type);
//	}	

} 


//=============================================================================
function createToolbar(map) {
	toolbar = new esri.toolbars.Draw(map);
	dojo.connect(toolbar, "onDrawEnd", QueryStations1);
}

//=============================================================================
function QueryStations1(extent)
	 {  //Query Stations Layer #0 - Find stations from spatial query
		map.graphics.clear();
		ShowExtent(extent);
		var queryStationsLink = "http://" + Server + "/ArcGIS/rest/services/HydroScope_Stations/MapServer/0";
        queryStationsTask = new esri.tasks.QueryTask(queryStationsLink);
        queryStations = new esri.tasks.Query();
        queryStations.returnGeometry = true;
  			queryStations.outFields = ["objectid","name","srid","abscissa","ordinate","water_basin_id","water_division_id","political_division_id","owner_id","type_id","descr","is_active","is_automatic","start_date","end_date"];
			  queryStations.geometry = extent;
				queryStationsTask.execute(queryStations, function(fset) {					 									      
																						      if (fset.features.length == 1) 
																							 	     { showFeature1(fset.features[0]); }
																						      else if (fset.features.length !== 0) 
																						         { showFeatureSet1(fset); }
																										 });
			map.setExtent(extent.getExtent().expand(1.2));
}  

//=============================================================================
    
      function ShowExtent(extent)
            {// Show Extent as graphic
                var ExtentSymbol = new esri.symbol.SimpleFillSymbol(esri.symbol.SimpleFillSymbol.STYLE_NONE,new esri.symbol.SimpleLineSymbol(esri.symbol.SimpleLineSymbol.STYLE_DASH, new dojo.Color([255,0,0]), 2), new dojo.Color([255,255,255,0.9]));
                var ExtentGraphic = new esri.Graphic(extent, ExtentSymbol);
                map.graphics.add(ExtentGraphic);
                map.setExtent(extent.getExtent().expand(1.2));
      }

//=============================================================================

      function ClickMap(where) {
						var queryLink = "http://" + Server + "/ArcGIS/rest/services/Hydroscope_Stations/MapServer/0";
        		queryTask = new esri.tasks.QueryTask(queryLink);
        		query = new esri.tasks.Query();
        		query.returnGeometry = true;
        		//Select output station fields
						query.outFields = ["objectid","name","srid","water_basin_id","water_division_id","political_division_id","owner_id","type_id","descr","is_active","is_automatic","start_date","end_date"]; 
						query.where = where; //"objectid IN " + StList + " AND abscissa>50";				
						//Listen for click event on the map, when the user clicks on the map call executeQueryTask function.
       			dojo.connect(map, "onClick", executeQueryTask);
      }		
	
//=============================================================================
    
      function executeQueryTask(evt) {
        map.infoWindow.hide();
        // map.graphics.clear();
        featureSet = null;
        var centerPoint = new esri.geometry.Point
                (evt.mapPoint.x,evt.mapPoint.y,evt.mapPoint.spatialReference);
        var mapWidth = map.extent.getWidth();
        
        //Divide width in map units by width in pixels
        var pixelWidth = mapWidth/map.width;
        
        //Calculate a 10 pixel envelope width (5 pixel tolerance on each side)
        var tolerance = 10 * pixelWidth;
        
        //Build tolerance envelope and set it as the query geometry
        var queryExtent = new esri.geometry.Extent
                (1,1,tolerance,tolerance,evt.mapPoint.spatialReference);
        query.geometry = queryExtent.centerAt(centerPoint);
			  //Execute task and call showResults on completion
  			queryTask.execute(query, function(fset) { 
																						      if (fset.features.length === 1) 
																							 	     { showFeature(fset.features[0],evt); }
																						      else if (fset.features.length !== 0) 
																						         { showFeatureSet(fset,evt); }
																				        }); 
    }
			
//=============================================================================
		
		function showFeature(feature,evt) {
        //set symbol
        var symbol = new esri.symbol.SimpleFillSymbol(esri.symbol.SimpleFillSymbol.STYLE_SOLID, new esri.symbol.SimpleLineSymbol(esri.symbol.SimpleLineSymbol.STYLE_SOLID, new dojo.Color([255,0,0]), 2), new dojo.Color([255,255,0,0.5]));
        feature.setSymbol(symbol);
        //Construct infowindow title and content
        var attr = feature.attributes;
        var title = attr.name;
        var content = "<b>OBJECT ID                    : </b>" + attr.objectid
                    + "<br /><b>Name                   : </b> " + attr.name
                    + "<br /><b>water_basin_id         : </b> " + attr.water_basin_id
                    + "<br /><b>water_division_id      : </b>" + attr.water_division_id
										+ "<br /><b>political_division_id  : </b>" + attr.political_division_id
										+ "<br /><b>owner_id               : </b>" + attr.owner_id
										+ "<br /><b>type_id                : </b>" + attr.type_id
										+ "<br /><b>descr                  : </b>" + attr.descr
										+ "<br /><b>is_active              : </b>" + attr.is_active
										+ "<br /><b>is_automatic           : </b>" + attr.is_automatic
										+ "<br /><b>start_date             : </b>" + attr.end_date
										;
        map.graphics.add(feature);
        map.infoWindow.setTitle(title);
        map.infoWindow.setContent(content);
        (evt) ? map.infoWindow.show(evt.screenPoint,map.getInfoWindowAnchor(evt.screenPoint)) : null;
      }


//=============================================================================
			
function showFeatureSet(fset,evt) {
      var screenPoint = evt.screenPoint;
      featureSet = fset;
      var numFeatures = featureSet.features.length;
      //QueryTask returns a featureSet.  Loop through features in the featureSet and add them to the infowindow.
      var title = "ΒΡΕΘΗΚΑΝ " + numFeatures + " ΣΤΑΘΜΟΙ";
      var content = "ΕΠΙΛΕΞΤΕ ΣΤΑΘΜΟ:<br />";

      for (var i=0; i<numFeatures; i++) {
             var graphic = featureSet.features[i]; var ind=i+1;
             content = content + ind+") " + " <A href='#' onclick='showFeature(featureSet.features[" + i + "]);'>" +  graphic.attributes.name + " ("+ graphic.attributes.objectid + ")"+ "</A>)<br/>";
            }
      map.infoWindow.setTitle(title);
      map.infoWindow.setContent(content);
      map.infoWindow.show(screenPoint,map.getInfoWindowAnchor(evt.screenPoint));
 }


//=============================================================================
		
		function showFeature1(feature) {
     //Add one point to map and set symbology
      attr = feature.attributes;
	     var x = attr.abscissa; y = attr.ordinate;
			 var point = new esri.geometry.Point( {"x": x,"y": y}, new esri.SpatialReference({"wkid":attr.srid}) );
	     var graphPoint = new esri.Graphic(point, defaultSymbol);
			 map.graphics.add(graphPoint);
			 StList[0]=attr.objectid;
			 }

//=============================================================================
			function showFeatureSet1(fset) {
        //Add points to map and set symbology
       var features = fset.features;
       var attr = features[0].attributes;
			 StList=[];
	     for (var i=0, il=features.length; i<il; i++)
		   {
      		  attr = features[i].attributes;
			      var point = new esri.geometry.Point( {"x": attr.abscissa ,"y": attr.ordinate}, new esri.SpatialReference({"wkid":attr.srid}) );
         	  var graphPoint = new esri.Graphic(point, defaultSymbol);
			   	  map.graphics.add(graphPoint);
						StList[i] = attr.objectid;
			 }    			   
       
		  }

//=============================================================================
function QueryDistrict(perif)
{//Query Layer#0

	 if (perif=='ΠΕΛΟΠΟΝΝΗΣΟΥ'){distrList="('408','409','410','411','412')";}
	 if (perif=='ΔΥΤΙΚΗΣ ΕΛΛΑΔΑΣ'){distrList="('413','414')";}
	 if (perif=='ΑΤΤΙΚΗΣ'){distrList="('453','454','455','456')";}
	 if (perif=='ΣΤΕΡΕΑΣ ΕΛΛΑΔΑΣ'){distrList="('402','403','404','405','406','407')";}
	 if (perif=='ΘΕΣΣΑΛΙΑΣ'){distrList="('415','416','417','418')";}
	 if (perif=='ΗΠΕΙΡΟΥ'){distrList="('419','420','421','422')";}
	 if (perif=='ΔΥΤΙΚΗΣ ΜΑΚΕΔΟΝΙΑΣ'){distrList="('423','424','425','426')";}
	 if (perif=='ΚΕΝΤΡΙΚΗΣ ΜΑΚΕΔΟΝΙΑΣ'){distrList="('427','428','429','430','431','432','433','434')";}
	 if (perif=='ΑΝΑΤΟΛΙΚΗΣ ΜΑΚΕΔΟΝΙΑΣ - ΘΡΑΚΗΣ'){distrList="('435','436','437','438','439')";}
	 if (perif=='ΚΡΗΤΗΣ'){distrList="('449','450','451','452')";}
	 if (perif=='ΒΟΡΕΙΟΥ ΑΙΓΑΙΟΥ'){distrList="('441','442','443')";}
	 if (perif=='ΝΟΤΙΟΥ ΑΙΓΑΙΟΥ'){distrList="('440','444')";}
	 if (perif=='ΙΟΝΙΩΝ ΝΗΣΩΝ'){distrList="('445','446','447','448')";}

	 var queryPolDivLink = "http://" + Server + "/ArcGIS/rest/services/HydroScope_Stations/MapServer/0";
	 var queryPolDivTask = new esri.tasks.QueryTask(queryPolDivLink);
	 var queryPolDiv = new esri.tasks.Query();
	 queryPolDiv.returnGeometry = false;
	 queryPolDiv.outFields = ["objectid","name","political_division_id","abscissa","ordinate"]; //Select output fields
	 queryPolDiv.where = "political_division_id IN "+ distrList; 
	 queryPolDivTask.execute(queryPolDiv, ShowStations);
}

//=============================================================================

function QueryStations(StList)
{  // Find stations from objectid field
   //Initialize & execute query
   var queryStationsLink = "http://" + Server + "/ArcGIS/rest/services/HydroScope_Stations/MapServer/0";
   queryStationsTask = new esri.tasks.QueryTask(queryStationsLink);
   queryStations = new esri.tasks.Query();
   queryStations.returnGeometry = false;
   queryStations.outFields = ["objectid","name","srid","abscissa","ordinate","water_basin_id","water_division_id","political_division_id","owner_id","type_id","descr","is_active","is_automatic","start_date","end_date"];
	queryStations.where = "objectid IN " + StList + " AND abscissa>50";				
	var where = queryStations.where; 
	queryStationsTask.execute(queryStations, function(fset){ShowStations(fset);ClickMap(where);});
}  

//=============================================================================

function ShowStations(featureSet)
{ 
      if (featureSet.features.length==1)
	     {ShowOneStation(featureSet);}
	else
   	     {ShowMultiStations(featureSet);}
}

//=============================================================================

     //Add one point to map and set symbology
     function ShowOneStation(featureSet)
     { //Add one point to map and set symbology
       var feature = featureSet.features[0];
  		 attr = feature.attributes;
	     var x = attr.abscissa; y = attr.ordinate;
			 var point = new esri.geometry.Point( {"x": x,"y": y}, new esri.SpatialReference({"wkid":attr.srid}) );
	     var graphPoint = new esri.Graphic(point, defaultSymbol);
			 map.graphics.add(graphPoint);
			 // Create map extent to show map point
			 var BufferX = 30000; BufferY = 30000;
       var PointExt = new esri.geometry.Extent({"xmin" :x-BufferX,"ymin" :y-BufferY,"xmax" : x+BufferX, "ymax" : y+BufferY}, map.spatialreference);
       map.setExtent(PointExt, false);
     }
//=============================================================================
    
     function ShowMultiStations(featureSet)
     { //Add points to map and set symbology
       var features = featureSet.features;
       var attr = features[0].attributes;
	     var minX = maxX = parseFloat(attr.abscissa); 
       var minY = maxY = parseFloat(attr.ordinate);
	     //Find minimum and maximum values for X
       dojo.forEach(features, function(feature) {
				      attr = feature.attributes;
              minX = Math.min(minX, attr.abscissa);
              maxX = Math.max(maxX, attr.abscissa);
        });
       //Find minimum and maximum values for Y
       dojo.forEach(features, function(feature) {
				     attr = feature.attributes;
             minY = Math.min(minY, attr.ordinate);
             maxY = Math.max(maxY, attr.ordinate);
       });
       for (var i=0, il=features.length; i<il; i++)
		   {
      		  attr = features[i].attributes;
			      var point = new esri.geometry.Point( {"x": attr.abscissa ,"y": attr.ordinate}, new esri.SpatialReference({"wkid":attr.srid}) );
         	  var graphPoint = new esri.Graphic(point, defaultSymbol);
			   	  map.graphics.add(graphPoint);
			 }    			   
       // Create map extent to show map points
		   var BufferX = 30000; BufferY = 30000;
       var PointsExt = new esri.geometry.Extent({"xmin" :minX-BufferX,"ymin" :minY-BufferY,"xmax" : maxX+BufferX, "ymax" : maxY+BufferY}, map.spatialreference);
       map.setExtent(PointsExt, false);
     }
//=============================================================================
  
	   function QueryType(type_id)
     {   //Query Layer#0 - Find stations from type_id field
         var queryTypeLink = "http://" + Server + "/ArcGIS/rest/services/HydroScope_Stations/MapServer/0";
				 var queryTypeTask = new esri.tasks.QueryTask(queryTypeLink);
         var queryType = new esri.tasks.Query();
         queryType.returnGeometry = true;
				 queryType.outFields = ["objectid","name","srid","abscissa","ordinate","water_basin_id","water_division_id","political_division_id","owner_id","type_id","descr","is_active","is_automatic","start_date","end_date"];
				 queryType.where = "type_id='" + type_id + "'" + " AND abscissa>50"; 
  			 var where = queryType.where; 
				 queryTypeTask.execute(queryType, function(fset){ShowStations(fset);ClickMap(where);});
     }
//=============================================================================

     function QueryOwner(owner_id)
     {   //Query Layer#0 - Find stations from owner_id field
 				 var queryOwnerLink = "http://" + Server + "/ArcGIS/rest/services/HydroScope_Stations/MapServer/0";
				 var queryOwnerTask = new esri.tasks.QueryTask(queryOwnerLink);
         var queryOwner = new esri.tasks.Query();
         queryOwner.returnGeometry = true;
         queryOwner.outFields = ["objectid","name","srid","abscissa","ordinate","water_basin_id","water_division_id","political_division_id","owner_id","type_id","descr","is_active","is_automatic","start_date","end_date"];
				 queryOwner.where = "owner_id='"+ owner_id+"'" + " AND abscissa>50"; 
				 var where = queryOwner.where; 
				 queryOwnerTask.execute(queryOwner, function(fset){ShowStations(fset);ClickMap(where);});
     }
//=============================================================================

     function QueryWaterBas(water_basin_id)
     {   //Query Layer#0 - Find stations from water_basin_id field
 				 var queryWaterBasLink = "http://" + Server + "/ArcGIS/rest/services/HydroScope_Stations/MapServer/0";
				 var queryWaterBasTask = new esri.tasks.QueryTask(queryWaterBasLink);
         var queryWaterBas = new esri.tasks.Query();
         queryWaterBas.returnGeometry = true;
         queryWaterBas.outFields = ["objectid","name","srid","abscissa","ordinate","water_basin_id","water_division_id","political_division_id","owner_id","type_id","descr","is_active","is_automatic","start_date","end_date"];
				 queryWaterBas.where = "water_basin_id='"+ water_basin_id+"'" + " AND abscissa>50" ; 
				 var where = queryWaterBas.where; 
				 queryWaterBasTask.execute(queryWaterBas, function(fset){ShowStations(fset);ClickMap(where);});
     }
//=============================================================================

     function QueryWaterDiv(water_division_id)
     {   //Query Layer#0 - Find stations from water_division_id field
 				 var queryWaterDivLink = "http://" + Server + "/ArcGIS/rest/services/HydroScope_Stations/MapServer/0";
				 var queryWaterDivTask = new esri.tasks.QueryTask(queryWaterDivLink);
         var queryWaterDiv = new esri.tasks.Query();
         queryWaterDiv.returnGeometry = false;
				 queryWaterDiv.outFields = ["objectid","name","srid","abscissa","ordinate","water_basin_id","water_division_id","political_division_id","owner_id","type_id","descr","is_active","is_automatic","start_date","end_date"];
         queryWaterDiv.where = "water_division_id='" + water_division_id + "'" + " AND abscissa>50"; 
				 var where = queryWaterDiv.where; 
				 queryWaterDivTask.execute(queryWaterDiv, function(fset){ShowStations(fset);ClickMap(where);});
		 }
//=============================================================================   

     function QueryPrefecture(nomos)
     {//Query Layer#0 - Find stations from political_division_id field
		  // PREFECTURE choice to list of political_division_id's
         if ( nomos =='ÄÉÁÌ.ÁÈÇÍÁÓ'){polDivId = 453;}; if ( nomos =='ÄÉÁÌ. ÁÍÁÔ. ÁÔÔÉÊÇÓ'){polDivId = 454;}; if ( nomos =='ÄÉÁÌ. ÄÕÔ. ÁÔÔÉÊÇÓ'){polDivId = 455;}; if ( nomos =='ÄÉÁÌ. ÐÅÉÑÁÉÁ'){polDivId = 456;};
         if ( nomos =='ÊÏÑÉÍÈÉÁÓ'){polDivId = 408;}; if ( nomos =='ÁÑÃÏËÉÄÁÓ'){polDivId = 409;} if ( nomos =='ÁÑÊÁÄÉÁÓ'){polDivId = 410;} if ( nomos =='ËÁÊÙÍÉÁÓ'){polDivId = 411;};
         if ( nomos =='ÌÅÓÓÇÍÉÁÓ'){polDivId = 412;};
         if ( nomos =='ÁÉÔÙËÏÁÊÁÑÍÁÍÉÁÓ'){polDivId = 406;}; if ( nomos =='ÇËÅÉÁÓ'){polDivId = 413;}; if ( nomos =='Á×ÁÉÁÓ'){polDivId = 414;};
         if ( nomos =='ÂÏÉÙÔÉÁÓ'){polDivId = 402;}; if ( nomos =='ÖÈÉÙÔÉÄÁÓ'){polDivId = 403;}; if ( nomos =='ÖÙÊÉÄÁÓ'){polDivId = 404;}; if ( nomos =='ÅÕÑÕÔÁÍÉÁÓ'){polDivId = 405;}; if ( nomos =='ÅÕÂÏÉÁÓ'){polDivId = 407;};
         if ( nomos =='ËÁÑÉÓÁÓ'){polDivId = 415;}; if ( nomos =='ÌÁÃÍÇÓÉÁÓ'){polDivId = 416;}; if ( nomos =='ÔÑÉÊÁËÙÍ'){polDivId = 417;}; if ( nomos =='ÊÁÑÄÉÔÓÁÓ'){polDivId = 418;};
         if ( nomos =='ÉÙÁÍÍÉÍÙÍ'){polDivId = 419;}; if ( nomos =='ÈÅÓÐÑÙÔÉÁÓ'){polDivId = 420;}; if ( nomos =='ÐÑÅÂÅÆÁÓ'){polDivId = 421;}; if ( nomos =='ÁÑÔÁÓ'){polDivId = 422;}; 
         if ( nomos =='ÊÁÓÔÏÑÉÁÓ'){polDivId = 423;}; if ( nomos =='ÖËÙÑÉÍÁÓ'){polDivId = 424;}; if ( nomos =='ÊÏÆÁÍÇÓ'){polDivId = 425;}; if ( nomos =='ÃÑÅÂÅÍÙÍ'){polDivId = 426;};
         if ( nomos =='ÈÅÓÓÁËÏÍÉÊÇÓ'){polDivId = 427;}; if ( nomos =='ÊÉËÊÉÓ'){polDivId = 428;}; if ( nomos =='ÐÅËËÁÓ'){polDivId = 429;};
         if ( nomos =='ÇÌÁÈÉÁÓ'){polDivId = 430;}; if ( nomos =='ÐÉÅÑÉÁÓ'){polDivId = 431;}; if ( nomos =='×ÁËÊÉÄÉÊÇÓ'){polDivId = 432;}; if ( nomos =='ÓÅÑÑÙÍ'){polDivId = 434;};
         if ( nomos =='ÄÑÁÌÁÓ'){polDivId = 435;}; if ( nomos =='ÊÁÂÁËÁÓ'){polDivId = 436;}; if ( nomos =='ÅÂÑÏÕ'){polDivId = 437;}; if ( nomos =='ÑÏÄÏÐÇÓ'){polDivId = 438;} if ( nomos =='ÎÁÍÈÇÓ'){polDivId = 439;};
         if ( nomos =='ËÅÓÂÏÕ'){polDivId = 441;}; if ( nomos =='×ÉÏÕ'){polDivId = 442;}; if ( nomos =='ÓÁÌÏÕ'){polDivId = 443;}; if ( nomos =='ÊÕÊËÁÄÙÍ'){polDivId = 440;} if ( nomos =='ÄÙÄÅÊÁÍÇÓÏÕ'){polDivId = 444;};
         if ( nomos =='×ÁÍÉÙÍ'){polDivId = 449;}; if ( nomos =='ÑÅÈÕÌÍÏÕ'){polDivId = 450;}; if ( nomos =='ÇÑÁÊËÅÉÏÕ'){polDivId = 451;}; if ( nomos =='ËÁÓÉÈÉÏÕ'){polDivId = 452;};
         if ( nomos =='ÊÅÑÊÕÑÁÓ'){polDivId = 445;}; if ( nomos =='ËÅÕÊÁÄÁÓ'){polDivId = 446;}; if ( nomos =='ÊÅÖÁËËÇÍÉÁÓ'){polDivId = 447;}; if ( nomos =='ÆÁÊÕÍÈÏÕ'){polDivId = 448;};
 				
	   var queryPrefLink = "http://" + Server + "/ArcGIS/rest/services/HydroScope_Stations/MapServer/0";
	   var queryPrefTask = new esri.tasks.QueryTask(queryPrefLink);
         var queryPref = new esri.tasks.Query();
         queryPref.returnGeometry = false;
	   queryPref.outFields = ["objectid","name","srid","abscissa","ordinate","water_basin_id","water_division_id","political_division_id","owner_id","type_id","descr","is_active","is_automatic","start_date","end_date"];
	   queryPref.where = "political_division_id=" + polDivId + " AND abscissa>50"; 
	   var where = queryPref.where; 
	   queryPrefTask.execute(queryPref, function(fset){ShowStations(fset);ClickMap(where);});
	} 
//=============================================================================


