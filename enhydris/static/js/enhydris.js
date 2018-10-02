/* global enhydris, OpenLayers, Arg */

enhydris.mapModule = (function namespace() {
    'use strict';
    var map;

    // Processing indicator
    var processingIndicator = document.getElementById('processing_indicator');
    var showProcessingIndicator =
        processingIndicator ?
            function () {
                processingIndicator.innerHTML =
                    '<img src="' + enhydris.staticUrl + 'images/wait16.gif">';
            }
        :
            function () {};
    var hideProcessingIndicator =
        processingIndicator ?
            function () {
                processingIndicator.innerHTML = '';
            }
        :
            function () {};

    // Map bounds
    var defaultBounds = new OpenLayers.Bounds();
    defaultBounds.extend(enhydris.mapBounds[0]);
    defaultBounds.extend(enhydris.mapBounds[1]);
    defaultBounds.transform(new OpenLayers.Projection('EPSG:4326'),
                            new OpenLayers.Projection('EPSG:900913'));

    // Various functions

    var getAttribute = function (feature, attrib) {
        var obj = feature.cluster ? feature.cluster[0] : feature;
        return obj.attributes[attrib];
    };

    var setMapExtents = function (map) {
        var gentityId = enhydris.mapMode === 2 ? enhydris.agentityId : '';
        var getBoundOptions = Arg.all();
        getBoundOptions.gentityId = gentityId;
        $.ajax({
            url: enhydris.boundingBoxUrl,
            data: getBoundOptions,
            success: function (data) {
                var bounds = OpenLayers.Bounds.fromString(data);
                bounds.transform(new OpenLayers.Projection('EPSG:4326'),
                                 new OpenLayers.Projection('EPSG:900913'));
                map.zoomToExtent(bounds);
            },
            error: function () {
                map.zoomToExtent(defaultBounds);
            }
        });
    };

    // Popup-related stuff

    var popup = null;

    var onFeatureSelect = function (feature) {
        var point, url;
        showProcessingIndicator();
        removePopup();
        point = feature.geometry.getBounds().getCenterLonLat();
        map.panTo(point);
        url = enhydris.rootUrl + 'stations/b/' +
              getAttribute(feature, 'id') + '/';
        $.get(url, {}, function (message) {
            var size;
            size = new OpenLayers.Size(190, 150);
            popup = new OpenLayers.Popup(getAttribute(feature, 'name'),
                                         point, size, message, true);
            popup.setBorder('2px solid');
            popup.setBackgroundColor('#EEEEBB');
            map.addPopup(popup, true);
            hideProcessingIndicator();
        });
    };

    var removePopup = function () {
        if (popup) {
            map.removePopup(popup);
            popup.destroy();
            popup = null;
        }
    };

    var onFeatureUnselect = function (feature) {
        // jshint unused:false
        removePopup();
    };

    // Layer parameters

    var layerParams =
        enhydris.mapMode === 1 ? Arg.all() :
        enhydris.mapMode === 2 ? {'gentity_id': enhydris.agentityId} :
                                 {};
    OpenLayers.Util.applyDefaults(layerParams, {
        request: 'GetFeature',
        srs: 'EPSG:4326',
        version: '1.0.0',
        service: 'WFS',
        format: 'WFS'
    });

    // Style map

    var getStyleOptions = function (extraOptions) {
        var baseOptions = {
            graphicWidth: 21,
            graphicHeight: 25,
            graphicXOffset: -10,
            graphicYOffset: -25,
            fillOpacity: 1,
            label: '',
            fontColor: '#504065',
            fontSize: '9px',
            fontFamily: 'Verdana, Arial',
            fontWeight: 'bold',
            labelAlign: 'cm',
            graphicTitle: '${name}'
        };
        var result = extraOptions;
        OpenLayers.Util.applyDefaults(result, baseOptions);
        return result;
    };

    var styleContext = {
        aname: function (feature) {
            return getAttribute(feature, 'name');
        },
        aicon: function (feature) {
            var stypeId = getAttribute(feature, 'stype_id');
            return enhydris.mapMarkers[stypeId] ||
                    enhydris.mapMarkers[0];
        }
    };

    var styleMap = new OpenLayers.StyleMap({
        'default': new OpenLayers.Style(
            OpenLayers.Util.applyDefaults(
                getStyleOptions(
                    {externalGraphic: enhydris.staticUrl + '${aicon}'}),
                OpenLayers.Feature.Vector.style.default),
            {context: styleContext}),
        'select': new OpenLayers.Style(
            OpenLayers.Util.applyDefaults(
                getStyleOptions(
                    {externalGraphic: enhydris.staticUrl +
                        'images/drop_marker_selected.png'}),
                OpenLayers.Feature.Vector.style.select)),
        'temporary': new OpenLayers.Style(
            OpenLayers.Util.applyDefaults(
                getStyleOptions(
                    {externalGraphic: enhydris.staticUrl + '${aicon}',
                    fillOpacity: 0.7}),
                OpenLayers.Feature.Vector.style.select),
            {context: styleContext})
    });

    // Create layer

    var createLayer = function (name, objectType) {
        var newLayer = new OpenLayers.Layer.Vector(name, {
            strategies: [
                new OpenLayers.Strategy.BBOX({ratio: 1.5, resFactor: 2}),
                new OpenLayers.Strategy.Cluster({distance: 15, threshold: 3})
            ],
            protocol: new OpenLayers.Protocol.HTTP({
                url: enhydris.rootUrl + objectType + '/kml/',
                format: new OpenLayers.Format.KML(),
                params: layerParams
            }),
            projection: new OpenLayers.Projection('EPSG:4326'),
            formatOptions: {extractAttributes: true},
            styleMap: styleMap
        });
        newLayer.events.register('loadstart', newLayer,
                                  showProcessingIndicator);
        newLayer.events.register('loadend', newLayer, hideProcessingIndicator);
        newLayer.events.register('loadcancel', newLayer,
                                  hideProcessingIndicator);
        return newLayer;
    };

    // getRectAreaResults (exported function)

    var getRectAreaResults = function () {
        var bbox = enhydris.map.getExtent().transform(
                new OpenLayers.Projection('EPSG:900913'),
                new OpenLayers.Projection('EPSG:4326')).toBBOX(7);
        var queryParams = Arg.all();
        queryParams.bbox = bbox;
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

    // Init

    var init = function () {
        map = new OpenLayers.Map(
            'map',
            {'units': 'm',
             'numZoomLevels': 15,
             'sphericalMercator': true,
             'maxExtent': defaultBounds,
             'projection': new OpenLayers.Projection('EPSG:900913'),
             'displayProjection': new OpenLayers.Projection('EPSG:4326'),
             'controls': [new OpenLayers.Control.Navigation(),
                          new OpenLayers.Control.ZoomBox(),
                          new OpenLayers.Control.Zoom(),
                          new OpenLayers.Control.ScaleLine(),
                          new OpenLayers.Control.MousePosition(),
                          new OpenLayers.Control.LayerSwitcher()
                          ]
            });

        map.addLayers(enhydris.mapBaseLayers);
        var dataLayers = [createLayer('Stations', 'stations', '#dd0022',
                '#990077')];
        map.addLayers(dataLayers);

        // Change style on hover
        var hoverControl =  new OpenLayers.Control.SelectFeature(
            dataLayers[0],
            {hover: true, highlightOnly: true, renderIntent: 'temporary'});
        map.addControl(hoverControl);
        hoverControl.activate();

        // Popup on select
        var selectControl =  new OpenLayers.Control.SelectFeature(
            dataLayers[0],
            {onSelect: onFeatureSelect, onUnselect: onFeatureUnselect});
        map.addControl(selectControl);
        selectControl.activate();

        setMapExtents(map);
        return map;
    };

    return {
        init: init,
        getRectAreaResults: getRectAreaResults
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

    // enhydris.transCoordinatesUI init at 'base-sample.html'
    var transText = enhydris.transCoordinatesUI;

    var switchToSimpleView = function () {
        // Hide elements for simple view
        var elementIDArray = ['id_asrid','id_srid','id_approximate'];
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
        var elementIDArray = ['id_asrid','id_srid','id_approximate'];
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
        // Initialize Form elements
        var sridValue = $('#id_srid').val();
        var asridValue = $('#id_asrid').val();
        // if the srid is 4326 or null, AND asrid is null

        if (sridValue === '4326' && asridValue === '') {
            switchToSimpleView();
            $('#btnCoordinates').show();
            $("label[for='id_asrid']").text(transText.formASridLabel);
        } else {
            $('#btnCoordinates').hide();
            $('label[for="id_asrid"]').text(transText.formASridLabel);
            switchToAdvancedView();
        }
    };
    return {
        initializeCoordinatesView: initializeCoordinatesView,
        toggleCoordinatesView: toggleCoordinatesView
    };
}());
