/* Settings for OpenLayers map. Settings are created based on stuff in
 * Django settings.
 */

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
