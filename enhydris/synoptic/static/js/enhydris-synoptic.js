const setupMarkers = function (dataLayers) {
  for (let i = 0; i < enhydris.mapStations.length; i += 1) {
    const station = enhydris.mapStations[i];

    // Circle marker
    L.circleMarker(
      [station.latitude, station.longitude],
      {
        color: 'red', fillColor: '#f03', fillOpacity: 0.5, radius: 5,
      },
    ).addTo(enhydris.map.leafletMap);

    Object.keys(station.last_values).forEach(function (key) {
      // Rectangle with info
      const html = (
        `<strong><a href='${station.target_url}'>${station.name}</a></strong><br>`
                + `<span class='date ${station.freshness}'>${station.last_common_date_pretty_without_timezone}</span><br>`
                + `<span class='value ${station.last_values_status[key]}'>${station.last_values[key]}</span>`
      );
      const icon = L.divIcon({ html, iconSize: [105, 55], iconAnchor: [108, 58] });
      L.marker([station.latitude, station.longitude], { icon }).addTo(
        dataLayers[key],
      );
    });
  }
};

const setupLayersControl = function (dataLayers) {
  L.control.groupedLayers(
    enhydris.mapBaseLayers,
    { '': dataLayers },
    { exclusiveGroups: [''] },
  ).addTo(enhydris.map.leafletMap);
};

const getDataLayers = function () {
  const layers = {};
  for (let i = 0; i < enhydris.mapStations.length; i += 1) {
    const station = enhydris.mapStations[i];
    Object.keys(station.last_values).forEach(function (key) {
      if (!(key in layers)) {
        layers[key] = L.featureGroup();
        if (Object.keys(layers).length === 1) {
          layers[key].addTo(enhydris.map.leafletMap);
        }
      }
    });
  }
  return layers;
};

enhydris.map.setUpMap();
const dataLayers = getDataLayers();
enhydris.map.layerControl.remove(); // We'll use a different layer control instead
setupLayersControl(dataLayers);
setupMarkers(dataLayers);
