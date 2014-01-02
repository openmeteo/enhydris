/* global enhydris, OpenLayers */

// Functions to handle political division relations
function render_pref_filter(data) {
    'use strict';
    $.getJSON(enhydris.root_url + 'get_subdivision/' + data + '/', {},
        function (j) {
            var options, pref, i;
            options = '';
            pref = $(document).getUrlParam('prefecture');
            if (j.length === 0) {
                options = '<option value="0" selected="selected" ' +
                          'disabled>None Available</option>';
            } else {
                options = '<option value="0" selected="selected" ' +
                          'disabled>Select a Prefecture</option>';
            }
            for (i = 0; i < j.length; i++) {
                if (pref === j[i].id) {
                    options += '<option value="' + j[i].id +
                               '" selected=\'selected\'>' + j[i].name +
                               '</option>';
                } else {
                    options += '<option value="' + j[i].id + '">' + j[i].name +
                               '</option>';
                }
            }
            $('select#prefecture').html(options);
        });
}
function render_dist_filter(data) {
    'use strict';
    $.getJSON(enhydris.root_url + 'get_subdivision/' + data + '/', {},
        function (j) {
            var options, dist, i;
            options = '';
            dist = $(document).getUrlParam('district');
            if (j.length === 0) {
                options = '<option value="0" selected="selected" ' +
                          'disabled>None Available</option>';
            } else {
                options = '<option value="0" selected="selected" ' +
                          'disabled>Select a District</option>';
            }
            for (i = 0; i < j.length; i++) {
                if (dist === j[i].id) {
                    options += '<option value="' + j[i].id +
                               '" selected=\'selected\'>' + j[i].name +
                               '</option>';
                } else {
                    options += '<option value="' + j[i].id + '">' + j[i].name +
                               '</option>';
                }
            }

            $('select#district').html(options);

            render_pref_filter(dist);
        });
}

// Function to handle asynchronous station search 
function station_search() {
    'use strict';
    var query, pd_v, p_v, d_v, wd_v, wb_v, t_v, o_v, pathname;
    query = '?';
    pd_v = $('#political_division');
    p_v = $('#prefecture');
    d_v = $('#district');
    
    if (pd_v.val() > -1) {
        if (p_v.val() > -1 && ! p_v.is(':disabled')) {
            query += '&political_division=' + p_v.val();
            query += '&district=' + d_v.val();
            query += '&prefecture=' + p_v.val();
        } else if (d_v.val() > -1 && ! d_v.is(':disabled')) {
            query += '&political_division=' + d_v.val();
            query += '&district=' + d_v.val();
        } else if (! pd_v.is(':disabled')) {
            query += '&political_division=' + pd_v.val();
        }
    }
    
    wd_v = $('#water_division');
    if (wd_v.val() > -1 && ! wd_v.is(':disabled')) {
        query += '&water_division=' + wd_v.val();
    }

    wb_v = $('#water_basin');
    if (wb_v.val() > -1 && ! wb_v.is(':disabled')) {
        query += '&water_basin=' + wb_v.val();
    }
    t_v = $('#variable');
    if (t_v.val() > -1 && ! t_v.is(':disabled')) {
        query += '&variable=' + t_v.val();
    }
    o_v = $('#owner');
    if (o_v.val() > -1 && ! o_v.is(':disabled')) {
        query += '&owner=' + o_v.val();
    }
    t_v = $('#type');
    if (t_v.val() > -1 && ! t_v.is(':disabled')) {
        query += '&type=' + t_v.val();
    }
    
    if ($('#ts_only').is(':checked')) {
        query += '&ts_only=True';
    }
    pathname = window.location.pathname;
    window.location.replace(pathname + query);

    return false;
}


enhydris.map_module = (function namespace() {
    'use strict';
    var default_bounds, options, map, data_layers, add_nav_toolbar,
        add_pan_zoom_bar, add_layer_switcher, show_labels, add_label_button,
        add_panel, set_map_extents, add_select_control, add_hover_control,
        layer_params, layer_options, style_default, style_select,
        style_temporary, style_map, init, create_layer, popup,
        show_popup, processing_indicator, show_processing_indicator,
        hide_processing_indicator, get_attribute;
    
    // Processing indicator
    processing_indicator = document.getElementById('processing_indicator');
    if (processing_indicator) {
        show_processing_indicator = function () {
            processing_indicator.innerHTML =
                    '<img src="' + enhydris.static_url + 'images/wait16.gif">';
        };
        hide_processing_indicator = function () {
            processing_indicator.innerHTML = '';
        };
    } else {
        show_processing_indicator = hide_processing_indicator = function () {};
    }

    // Map bounds
    default_bounds = new OpenLayers.Bounds();
    default_bounds.extend(enhydris.map_bounds[0]);
    default_bounds.extend(enhydris.map_bounds[1]);
    default_bounds.transform(new OpenLayers.Projection('EPSG:4326'),
                     new OpenLayers.Projection('EPSG:900913'));

    // Map options
    options = {
        'units': 'm',
        'numZoomLevels': 15,
        'sphericalMercator': true,
        'maxExtent': default_bounds,
        'projection': new OpenLayers.Projection('EPSG:900913'),
        'displayProjection': new OpenLayers.Projection('EPSG:4326')
    };

    get_attribute = function (feature, attrib) {
        var obj = feature.cluster ? feature.cluster[0] : feature;
        return obj.attributes[attrib];
    };

    add_nav_toolbar = function (hover_control, select_control) {
        var nav_toolbar;
        nav_toolbar = new OpenLayers.Control.NavToolbar();
        map.addControl(nav_toolbar);
        $('div.olControlNavToolbar').css('top', '14px');
        $('div.olControlNavToolbar').css('left', '11px');
        nav_toolbar.controls[0].events.on({
            'activate': function () {
                hover_control.activate();
                select_control.activate();
            },
            'deactivate': function () {
                hover_control.deactivate();
                select_control.deactivate();
            }
        });
        nav_toolbar.controls[0].activate();
    };

    add_pan_zoom_bar = function () {
        var pzb = new OpenLayers.Control.PanZoomBar();
        pzb.zoomWorldIcon = false;
        map.addControl(pzb);
    };

    add_layer_switcher = function () {
        var layer_switcher = new OpenLayers.Control.LayerSwitcher();
        map.addControl(layer_switcher);
        layer_switcher.baseLbl.innerHTML = 'Base layers';
        layer_switcher.dataLbl.innerHTML = 'Data layers';
    };

    show_labels = function (value) {
        var i, layer, defaultStyle;
        for (i = 0; i < data_layers.length; i++) {
            layer = data_layers[i];
            defaultStyle = layer.styleMap.styles['default'].defaultStyle;
            defaultStyle.value = value ?  '${aname}' : '';
            layer.styleMap.styles['default'].setDefaultStyle(defaultStyle);
            layer.redraw();
        }
    };

    add_label_button = function () {
        var label_button = new OpenLayers.Control.Button({
            type: OpenLayers.Control.TYPE_TOGGLE,
            title: 'Show labels',
            displayClass: 'LabelButtonClass',
            trigger: function () {}
        });
        label_button.events.register('activate', label_button,
            function () { show_labels(true); });
        label_button.events.register('deactivate', label_button,
            function () { show_labels(false); });
        return label_button;
    };

    add_panel = function (map, controls) {
        var panel, i;
        panel = new OpenLayers.Control.Panel({
            displayClass: 'olControlShowLabels'
        });
        panel.addControls(controls);
        for (i = 0; i < controls.length; ++i) {
            panel.activateControl(arguments[i]);
        }
        map.addControl(panel);
    };

    add_select_control = function (layers) {
        var select_control;
        select_control = new OpenLayers.Control.SelectFeature(layers, {
            clickout: true,
            togle: false,
            multiple: false,
            hover: false
        });
        map.addControl(select_control);
        select_control.activate();
        return select_control;
    };

    add_hover_control = function (layers) {
        var hover_control = new OpenLayers.Control.SelectFeature(layers, {
            clickout: false,
            togle: false,
            multiple: false,
            hover: true,
            highlightOnly: true,
            renderIntent: 'temporary',
            eventListeners: {
                beforefeaturehighlighted: function () {},
                featurehighlighted: function (e) {
                    document.getElementById('map').title = get_attribute(
                        e.feature, 'name');
                },
                featureunhighlighted: function () {
                    document.getElementById('map').title = '';
                }
            }
        });
        map.addControl(hover_control);
        hover_control.activate();
        return hover_control;
    };

    set_map_extents = function (map) {
        var gentity_id, get_bound_options;
        gentity_id = enhydris.map_mode === 2 ? enhydris.agentity_id : '';
        get_bound_options = Arg.all();
        get_bound_options.gentity_id = gentity_id;
        $.ajax({
            url: enhydris.bound_url,
            data: get_bound_options,
            success: function (data) {
                var bounds = OpenLayers.Bounds.fromString(data);
                bounds.transform(new OpenLayers.Projection('EPSG:4326'),
                                 new OpenLayers.Projection('EPSG:900913'));
                map.zoomToExtent(bounds);
            },
            error: function () {
                map.zoomToExtent(default_bounds);
            }
        });
    };
 
    popup = null;

    show_popup = function (map, feature) {
        var point, url;
        point = feature.geometry.getBounds().getCenterLonLat();
        map.panTo(point);
        url = enhydris.root_url + 'stations/b/' +
              get_attribute(feature, 'id') + '/';
        $.get(url, {}, function (message) {
            var size;
            size = new OpenLayers.Size(190, 150);
            popup = new OpenLayers.Popup(get_attribute(feature, 'name'),
                                         point, size, message, true);
            popup.setBorder('2px solid');
            popup.setBackgroundColor('#EEEEBB');
            map.addPopup(popup, true);
            hide_processing_indicator();
        });
    };

    layer_params =
        enhydris.map_mode === 1 ? Arg.all() :
        enhydris.map_mode === 2 ? { 'gentity_id': enhydris.agentity_id} :
                                  {};
    $.extend(layer_params, {
        request: 'GetFeature',
        srs: 'EPSG:4326',
        version: '1.0.0',
        service: 'WFS',
        format: 'WFS'
    });

    layer_options = {
        externalGraphic: enhydris.static_url + '${aicon}',
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
        labelAlign: 'cm'
    };

    // Style map
    style_default = new OpenLayers.Style(
        OpenLayers.Util.applyDefaults(layer_options,
        OpenLayers.Feature.Vector.style['default']), {
            context: {
                aname: function (feature) {
                    return get_attribute(feature, 'name');
                },
                aicon: function (feature) {
                    var stype_id = get_attribute(feature, 'stype_id');
                    return enhydris.map_markers[stype_id] ||
                            enhydris.map_markers[0];
                }
            }
        });
    style_select = new OpenLayers.Style(
        OpenLayers.Util.applyDefaults($.extend(layer_options, {
            externalGraphic: enhydris.static_url +
                'images/drop_marker_selected.png',
        }, OpenLayers.Feature.Vector.style.select))
    );
    style_temporary = new OpenLayers.Style(
        OpenLayers.Util.applyDefaults($.extend(layer_options, {
            fillOpacity: 0.7
        }, OpenLayers.Feature.Vector.style.select))
    );
    style_map = new OpenLayers.StyleMap({
        'default': style_default,
        'select': style_select,
        'temporary': style_temporary,
    });

    create_layer = function (name, object_type) {
        var new_layer;
        new_layer = new OpenLayers.Layer.Vector(name, {
            strategies: [
                new OpenLayers.Strategy.BBOX({ratio: 1.5, resFactor: 2}),
                new OpenLayers.Strategy.Cluster({distance: 15, threshold: 3})
            ],
            protocol: new OpenLayers.Protocol.HTTP({
                url: enhydris.root_url + object_type + '/kml/',
                format: new OpenLayers.Format.KML(),
                params: layer_params
            }),
            projection: new OpenLayers.Projection('EPSG:4326'),
            formatOptions: {extractAttributes: true},
            styleMap: style_map
        });
        new_layer.events.register('loadstart', new_layer,
                                  show_processing_indicator);
        new_layer.events.register('loadend', new_layer,
                                  hide_processing_indicator);
        new_layer.events.register('loadcancel', new_layer,
                                  hide_processing_indicator);
        new_layer.events.on({
            'featureselected': function (e) {
                show_processing_indicator();
                show_popup(e.feature);
            },
            'featureunselected': function () {
                map.removePopup(popup);
            }
        });
        return new_layer;
    };

    init = function () {
        var label_button, hover_control, select_control, layers;

        layers = [create_layer('Stations', 'stations', '#dd0022', '#990077')];
        map = new OpenLayers.Map('map', options);
        map.addLayers(layers);
        map.addControl(new OpenLayers.Control.ScaleLine());
        map.addControl(new OpenLayers.Control.MousePosition());
        map.addControl(new OpenLayers.Control.OverviewMap());
        map.addLayers(enhydris.map_base_layers);
        add_pan_zoom_bar();
        add_layer_switcher();
        label_button = add_label_button();
        add_panel(map, [label_button]);
        select_control = add_select_control(layers);
        hover_control = add_hover_control(layers);
        add_nav_toolbar(hover_control, select_control);
        set_map_extents(map);
        return map;
    };

    return {
        init: init
    };
}());
