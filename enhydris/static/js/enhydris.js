enhydris.mapModule = (function namespace() {
  let map;
  let stationsLayer;

  const setupMap = function () {
    map = L.map('mapid');
    const vp = enhydris.mapViewport;
    map.fitBounds([[vp[1], vp[0]], [vp[3], vp[2]]]);
    L.control.scale().addTo(map);
    L.control.mousePosition(
      { position: 'bottomright', emptyString: '' },
    ).addTo(map);
    return map;
  };

  const setupBaseLayer = function () {
    enhydris.mapBaseLayers[enhydris.mapDefaultBaseLayer].addTo(map);
  };

  const setupStationsLayer = function () {
    let url = `${enhydris.rootUrl}stations/kml/`;
    if (enhydris.mapMode === 'many-stations') url += `?q=${enhydris.searchString}`;
    else if (enhydris.mapMode === 'single-station') url += `?gentity_id=${enhydris.agentityId}`;
    stationsLayer = new L.KML(url, { async: true });
    map.addLayer(stationsLayer);
  };

  const setupLayersControl = function () {
    L.control.layers(enhydris.mapBaseLayers, { Stations: stationsLayer }).addTo(map);
  };

  const init = function () {
    setupMap();
    setupBaseLayer();
    setupStationsLayer();
    setupLayersControl();
    return map;
  };

  const listStationsVisibleOnMap = function () {
    const queryParams = Arg.all();
    queryParams.bbox = map.getBounds().toBBoxString();
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
  };

  return {
    init,
    listStationsVisibleOnMap,
    setupMap,
    setupBaseLayer,
  };
}());

enhydris.coordinatesUI = (function namespace() {
  /* To determine the location of a station, the user must set the
    abscissa , the ordinate and the id of the reference system ,
    information very specialized and incomprehensible to most users
    who just know the longitude and latitude of the station.
    In order to simplify UI when user adds new or edits station,
    openmeteo developers team decided to intergate a fix with minimal as
    possible modifications at backend and add javascript functions to handle
    this.
    */

  const transText = enhydris.transCoordinatesUI;

  const switchToSimpleView = function () {
    // Hide elements for simple view
    const elementIDArray = ['id_srid'];
    for (let i = 0; i < elementIDArray.length; i += 1) {
      $(`#${elementIDArray[i]}`).hide();
      $(`label[for="${elementIDArray[i]}"]`).hide();
    }
    // Prepare switch for the next view: advanced
    $('#btnCoordinates').html(transText.btnAdvanceView);
    $('#btnCoordinates').attr('form-view', 'advanced');
    // Alter elements attributes
    $('label[for="id_srid"]').text(transText.formSridLabel);
    $('label[for="id_abscissa"]').text(transText.formLongtitudeLabel);
    $('#id_abscissa').attr('placeholder', 'ex. 20.94546');
    $('label[for="id_ordinate"]').text(transText.formLatitudeLabel);
    $('#id_ordinate').attr('placeholder', 'ex. 39.12171');
  };

  const switchToAdvancedView = function () {
    // Show elements for advanced view
    const elementIDArray = ['id_srid'];
    for (let i = 0; i < elementIDArray.length; i += 1) {
      $(`#${elementIDArray[i]}`).show();
      $(`label[for="${elementIDArray[i]}"]`).show();
    }
    // Prepare  switch for the next view: simple
    $('#btnCoordinates').html(transText.btnSimpleView);
    $('#btnCoordinates').attr('form-view', 'simple');
    // Alter elements attributes
    $('label[for="id_srid"]').text(transText.formSridLabel);
    $('label[for="id_abscissa"]').text(transText.formAbscissaLabel);
    $('#id_abscissa').attr('placeholder', 'ex. 20.94546');
    $('label[for="id_ordinate"]').text(transText.formOrdinateLabel);
    $('#id_ordinate').attr('placeholder', 'ex. 39.12171');
  };

  const toggleCoordinatesView = function () {
    // Main Switch, handles on click in btn id='btnCoordinates'
    const viewCase = $('#btnCoordinates').attr('form-view');
    if (viewCase === 'simple') {
      switchToSimpleView();
    }
    if (viewCase === 'advanced') {
      switchToAdvancedView();
    }
  };

  const initializeCoordinatesView = function () {
    // if SRID is '' or null then '4326'
    // This is equal to say 'SRID' default value equals '4326'
    if ($('#id_srid').val() === '' || $('#id_srid').val() === null) {
      $('#id_srid').attr('value', '4326');
    }
    const sridValue = $('#id_srid').val();
    if (sridValue === '4326') {
      switchToSimpleView();
      $('#btnCoordinates').show();
    } else {
      $('#btnCoordinates').hide();
      switchToAdvancedView();
    }
  };
  return {
    initializeCoordinatesView,
    toggleCoordinatesView,
  };
}());
