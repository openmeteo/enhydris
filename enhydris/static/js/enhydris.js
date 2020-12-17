enhydris.map = {
  create() {
    this.setUpMap();
    this.setupStationsLayer();
  },

  setUpMap() {
    this.leafletMap = L.map('mapid');
    this.setupBaseLayers();
    this.setupViewport();
    this.setupMapControls();
  },

  setupBaseLayers() {
    enhydris.mapBaseLayers[enhydris.mapDefaultBaseLayer].addTo(this.leafletMap);
  },

  setupViewport() {
    const vp = enhydris.mapViewport;
    this.leafletMap.fitBounds([[vp[1], vp[0]], [vp[3], vp[2]]]);
  },

  setupMapControls() {
    L.control.scale().addTo(this.leafletMap);
    L.control.mousePosition(
      { position: 'bottomright', emptyString: '' },
    ).addTo(this.leafletMap);
    this.layerControl = L.control.layers(enhydris.mapBaseLayers, {}).addTo(this.leafletMap);
  },

  setupStationsLayer() {
    let url = `${enhydris.rootUrl}stations/kml/`;
    if (enhydris.mapMode === 'many-stations') {
      url += `?q=${enhydris.searchString}`;
    } else if (enhydris.mapMode === 'single-station') {
      url += `?gentity_id=${enhydris.agentityId}`;
    }
    this.stationsLayer = new L.KML(url, { async: true });
    this.leafletMap.addLayer(this.stationsLayer);
    this.layerControl.addOverlay(this.stationsLayer, 'Stations');
  },

  listStationsVisibleOnMap() {
    const queryParams = Arg.all();
    queryParams.bbox = this.leafletMap.getBounds().toBBoxString();
    let queryString = '';
    Object.keys(queryParams).forEach((param) => {
      if (Object.prototype.hasOwnProperty.call(queryParams, param)) {
        if (param !== '') {
          if (queryString) {
            queryString += '&';
          }
          queryString += `${param}=${queryParams[param]}`;
        }
      }
    });
    window.location = `${window.location.pathname}?${queryString}`;
  },
};
