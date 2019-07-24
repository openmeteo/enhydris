enhydris.mapModule = (function namespace() {
    'use strict';
    var map, stationsLayer;

    var init = function () {
        _setupMap();
        _setupBaseLayer();
        _setupStationsLayer();
        _setupLayersControl();
        return map;
    };

    var _setupMap = function () {
        map = L.map("mapid");
        var vp = enhydris.mapViewport;
        map.fitBounds([[vp[1], vp[0]], [vp[3], vp[2]]]);
        L.control.scale().addTo(map);
        L.control.mousePosition(
            {"position": "bottomright", "emptyString": ""}
        ).addTo(map);
        return map;
    };

    var _setupBaseLayer = function () {
        enhydris.mapBaseLayers[enhydris.mapDefaultBaseLayer].addTo(map);
    };

    var _setupStationsLayer = function () {
        var url = enhydris.rootUrl + "stations/kml/"
        if(enhydris.mapMode == "single-station")
            url += "?gentity_id=" + enhydris.agentityId;
        stationsLayer = new L.KML(url, {async: true});
        map.addLayer(stationsLayer);
    };

    var _setupLayersControl = function () {
        L.control.layers(enhydris.mapBaseLayers, {"Stations": stationsLayer}).addTo(map);
    };

    var listStationsVisibleOnMap = function () {
        var queryParams = Arg.all();
        queryParams.bbox = map.getBounds().toBBoxString();
        var queryString = '';
        for (var param in queryParams) {
            if (queryParams.hasOwnProperty(param)) {
                if (param === '') {
                    continue;
                }
                if (queryString) {
                    queryString += '&';
                }
                queryString += param + '=' + queryParams[param];
            }
        }
        window.location = window.location.pathname + '?' + queryString;
    };

    return {
        init: init,
        listStationsVisibleOnMap: listStationsVisibleOnMap,
        setupMap: _setupMap,
        setupBaseLayer: _setupBaseLayer,
    };
}());


enhydris.coordinatesUI = (function namespace() {
    'use strict';
    /* To determine the location of a station, the user must set the
    abscissa , the ordinate and the id of the reference system ,
    information very specialized and incomprehensible to most users
    who just know the longitude and latitude of the station.
    In order to simplify UI when user adds new or edits station,
    openmeteo developers team decided to intergate a fix with minimal as
    possible modifications at backend and add javascript functions to handle
    this.
    */

    var transText = enhydris.transCoordinatesUI;

    var switchToSimpleView = function () {
        // Hide elements for simple view
        var elementIDArray = ['id_srid'];
        for (var i = 0; i < elementIDArray.length; i++) {
            $('#' + elementIDArray[i]).hide();
            $('label[for="' + elementIDArray[i] + '"]').hide();
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

    var switchToAdvancedView = function () {
        // Show elements for advanced view
        var elementIDArray = ['id_srid'];
        for (var i = 0; i < elementIDArray.length; i++) {
            $('#' + elementIDArray[i]).show();
            $('label[for="' + elementIDArray[i] + '"]').show();
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

    var toggleCoordinatesView = function () {
        // Main Switch, handles on click in btn id='btnCoordinates'
        var viewCase = $('#btnCoordinates').attr('form-view');
        if (viewCase === 'simple') {
            switchToSimpleView();
        }
        if (viewCase === 'advanced') {
            switchToAdvancedView();
        }
    };

    var initializeCoordinatesView = function () {
        // if SRID is '' or null then '4326'
        // This is equal to say 'SRID' default value equals '4326'
        if ($('#id_srid').val() === '' || $('#id_srid').val() === null) {
            $('#id_srid').attr('value', '4326');
        }
        var sridValue = $('#id_srid').val();
        if (sridValue === '4326') {
            switchToSimpleView();
            $('#btnCoordinates').show();
        } else {
            $('#btnCoordinates').hide();
            switchToAdvancedView();
        }
    };
    return {
        initializeCoordinatesView: initializeCoordinatesView,
        toggleCoordinatesView: toggleCoordinatesView
    };
}());
