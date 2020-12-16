L.Control.MousePosition = L.Control.extend({

  pos: null,

  options: {
    position: 'bottomleft',
    separator: ' : ',
    emptyString: 'Unavailable',
    lngFirst: false,
    numDigits: 5,
    lngFormatter: undefined,
    latFormatter: undefined,
    formatter: undefined,
    prefix: '',
    wrapLng: true,
  },

  onAdd(map) {
    this.container = L.DomUtil.create('div', 'leaflet-control-mouseposition');
    L.DomEvent.disableClickPropagation(this.container);
    map.on('mousemove', this.onMouseMove, this);
    this.container.innerHTML = this.options.emptyString;
    return this.container;
  },

  onRemove(map) {
    map.off('mousemove', this.onMouseMove);
  },

  getLatLng() {
    return this.pos;
  },

  onMouseMove(e) {
    this.pos = e.latlng.wrap();
    const lngValue = this.options.wrapLng ? e.latlng.wrap().lng : e.latlng.lng;
    const latValue = e.latlng.lat;
    let lng;
    let lat;
    let value;
    let prefixAndValue;

    if (this.options.formatter) {
      prefixAndValue = this.options.formatter(lngValue, latValue);
    } else {
      lng = this.options.lngFormatter
        ? this.options.lngFormatter(lngValue)
        : L.Util.formatNum(lngValue, this.options.numDigits);

      lat = this.options.latFormatter
        ? this.options.latFormatter(latValue)
        : L.Util.formatNum(latValue, this.options.numDigits);

      value = this.options.lngFirst
        ? lng + this.options.separator + lat
        : lat + this.options.separator + lng;

      prefixAndValue = `${this.options.prefix} ${value}`;
    }

    this.container.innerHTML = prefixAndValue;
  },

});

L.Map.mergeOptions({
  positionControl: false,
});

L.Map.addInitHook(function () {
  if (this.options.positionControl) {
    this.positionControl = new L.Control.MousePosition();
    this.addControl(this.positionControl);
  }
});

L.control.mousePosition = function (options) {
  return new L.Control.MousePosition(options);
};
