const maputils = {
  // From Bounding box coord get center of the box
  // Note: Over simplified version.
  getBoundingBoxCenter: bbox => [
    (bbox[1] + bbox[3]) / 2,
    (bbox[0] + bbox[2]) / 2
  ],
  stationsWithMarkers: function(data) {
    // Filter stations that have coordinates and return the coord array
    return data.filter(obj => obj.marker[0]).map(obj => obj.marker);
  },
  convert2coords: function(point_string) {
    // Review with @aptiko
    // "point": "SRID=4326;POINT (20.984238 39.147111)", --> to object
    // related with stationsWithMarkers
    if (point_string) {
      let newpoint = point_string
        .split("(")[1]
        .slice(0, -1)
        .split(" ")
        .map(Number);
      return [newpoint[1], newpoint[0]];
    } else {
      return [null, null];
    }
  }
};
export default maputils;
