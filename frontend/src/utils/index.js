const utils = {
  get_api_root: function() {
    return process.env.VUE_APP_ENHYDRIS_API;
  },
  get_app_mode: function() {
    return process.env.NODE_ENV;
  },
  get_app_logo: function() {
    return process.env.VUE_APP_LOGO;
  },
  get_app_logo_alt: function() {
    return process.env.VUE_APP_ALT;
  },
  yearRanger: function(startYear) {
    var currentYear = new Date().getFullYear(),
      years = [];
    startYear = startYear || 2000;

    while (startYear <= currentYear) {
      years.push(startYear++);
    }
    return years;
  },
  get_map_center: function(bounding_box) {
    let box = bounding_box;
    return [(box[1] + box[3]) / 2, (box[0] + box[2]) / 2];
  },
  convert2coords: function(point_string) {
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

export default utils;
