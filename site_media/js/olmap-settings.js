/***********************************/
/* OpenLayers map for enhydris     */
/* Settings file. You may alter    */
/* contents of this file to        */
/* customize the map display.      */
/***********************************/

/* Set the bounds of your geographical area, by
   specifying bottom-left (bl) and top right
   (tr) corners */
var bl_point = new OpenLayers.LonLat(19.3, 34.75);
var tr_point = new OpenLayers.LonLat(29.65,41.8);

var bounds = new OpenLayers.Bounds();
bounds.extend(bl_point);
bounds.extend(tr_point);
bounds.transform(new OpenLayers.Projection("EPSG:4326"),
                 new OpenLayers.Projection("EPSG:900913"));

var wms1_base = new OpenLayers.Layer.WMS("Υπόβαθρο «ΚΤΗΜΑΤΟΛΟΓΙΟ Α.Ε.»",
  "http://gis.ktimanet.gr/wms/wmsopen/wmsserver.aspx",
    {   layers: 'KTBASEMAP', transparent: false},
    {   isBaseLayer: true,
        projection: new OpenLayers.Projection("EPSG:900913"),
        iformat: 'image/png', maxExtent: bounds, numZoomLevels:
        15, units: "m", maxResolution: 900,
        attribution: ""});

/* Uncomment to use WMS layer */
//var wms2_base = new OpenLayers.Layer.WMS("Another WMS layer",
//  "http://specify.url/",
//    {   layers: 'LAYER', transparent: false},
//    {   isBaseLayer: true,
//        projection: new OpenLayers.Projection("EPSG:900913"),
//        iformat: 'image/png', maxExtent: bounds, numZoomLevels:
//        15, units: "m", maxResolution: 900,
//        attribution: ""});

var osm = new OpenLayers.Layer.OSM.Mapnik("Υπόβαθρο \"Open Street Map\"",{isBaseLayer: true,
        attribution: "Map by <a href='http://www.openstreetmap.org/'>OSM</a>"});

var ocm = new OpenLayers.Layer.OSM.CycleMap("Υπόβαθρο \"Open Cycle Map\"",{isBaseLayer: true,
        attribution: "Map by <a href='http://www.openstreetmap.org/'>OSM</a>"});

/* Uncoment to use google maps layer */
// var google_map = new OpenLayers.Layer.Google("Google map", {isBaseLayer:true});
/* Note, in order to use google maps, you should include the google
 * maps API in the main html file, provided by Google.*/

/* Add base layers to this array by the order of apearance */
var base_layers = [ocm, osm, wms1_base];

//Set the markers for several station types
//Maximum of categories: 4. The last row has a dummy id and the icon
//for stations not belongin to the first 3 categories.
//If you wish to use less than 4 categories, then use dummy ids in the
//third or/and second category. 
var marker_categories = {id: [11,1,3,0],
                         icon: ['images/drop_marker_green.png', 
                                'images/drop_marker_cyan.png',
                                'images/drop_marker_orange.png', 
                                'images/drop_marker.png']};
