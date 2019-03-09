const maputils = {
  // From Bounding box coord get center of the box
  // Note: Over simplified version.
  getBoundingBoxCenter: bbox => [
    (bbox[1] + bbox[3]) / 2,
    (bbox[0] + bbox[2]) / 2
  ],
  getStationCoordinates: function(data) {
    // return an Array with stations coords
    // [[lat, long], ... [lat, long]]
    return data.filter(obj => obj.coordinates[0]).map(obj => obj.coordinates);
  },
  wkt2coordinates: function(point_string) {
    // Review with @aptiko
    // "point": "SRID=4326;POINT (20.984238 39.147111)", --> to object
    // related with getStationCoordinates
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
