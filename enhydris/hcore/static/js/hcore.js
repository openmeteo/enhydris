/* global enhydris, OpenLayers */

// Functions to handle political division relations
function render_pref_filter(data) {
    'use strict';
	$.getJSON(enhydris.root_url + 'get_subdivision/' + data + '/', {},
        function (j) {
            var options = '';
            var pref = $(document).getUrlParam('prefecture');
            var i;
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

            var options = '';
            var dist = $(document).getUrlParam('district');
            var i;
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
	var query = '?';
	var pd_v = $('#political_division');
	var p_v = $('#prefecture');
	var d_v = $('#district');
    var wd_v, wb_v, t_v, o_v;
    
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
	var pathname = window.location.pathname;
	window.location.replace(pathname + query);

	return false;
}


function getUrlVars() {
    'use strict';
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi,
        function (m, key, value) {
            vars[key] = decodeURI(value);
        });
    return vars;
}


Object.extend = function (destination, source) {
    'use strict';
    for (var property in source) {
        destination[property] = source[property];
    }
    return destination;
};


function get_attribute(afeature, attrib) {
    'use strict';
    if (!afeature.cluster) {
        return afeature.attributes[attrib];
    } else {
        return afeature.cluster[0].attributes[attrib];
    }
}


function InvokePopup(afeature) {
    'use strict';
    var map = null;
    apopup = null;
    var apoint = afeature.geometry.getBounds().getCenterLonLat();
    map.panTo(apoint);
    $.get(enhydris.root_url + 'stations/b/' + get_attribute(afeature, 'id') +
        '/', {}, function (data) {
            var amessage = '';
            amessage = data;
            apopup = new OpenLayers.Popup(get_attribute(afeature, 'name'),
                apoint, new OpenLayers.Size(190, 150), amessage, true);
            apopup.setBorder('2px solid');
            apopup.setBackgroundColor('#EEEEBB');
            map.addPopup(apopup, true);
            HideProgress('popup');
        });
}


function InvokeTooltip(atitle) {
    'use strict';
    document.getElementById('map').title = atitle;
}


function HideTooltip() {
    'use strict';
    document.getElementById('map').title = '';
}


function CreateLayer(AName, ObjectName) {
    'use strict';
    var params, labelvalue, labeling_opts, general_opts, alayer;
    if (enhydris.map_mode === 1) {
        params = getUrlVars();
    }
    else if (enhydris.map_mode === 2) {
        params = {'gentity_id': enhydris.agentity_id};
    }
    params.request = 'GetFeature';
    params.srs = 'EPSG:4326';
    params.version = '1.0.0';
    params.service = 'WFS';
    params.format = 'WFS';
    labelvalue = '';
    labeling_opts = {
        label : labelvalue,
        fontColor: '#504065',
        fontSize: '9px',
        fontFamily: 'Verdana, Arial',
        fontWeight: 'bold',
        labelAlign: 'cm'
    };
    general_opts = {
        externalGraphic: enhydris.static_url + '${aicon}',
        graphicWidth: 21,
        graphicHeight: 25,
        graphicXOffset: -10,
        graphicYOffset: -25,
        fillOpacity: 1
    };
    general_opts = Object.extend(general_opts, labeling_opts);
    var AURL = enhydris.root_url + ObjectName + '/kml/';
    alayer = new OpenLayers.Layer.Vector(AName, {
        strategies: [
            new OpenLayers.Strategy.BBOX({ratio: 1.5, resFactor: 2}),
            new OpenLayers.Strategy.Cluster({distance: 15, threshold: 3})
        ],
        protocol: new OpenLayers.Protocol.HTTP({
            url: AURL,
            format: new OpenLayers.Format.KML(),
            params: params
        }),
        projection: new OpenLayers.Projection('EPSG:4326'),
        formatOptions: { extractAttributes: true },
        styleMap: new OpenLayers.StyleMap({
            'default': new OpenLayers.Style(
                OpenLayers.Util.applyDefaults(general_opts,
                OpenLayers.Feature.Vector.style['default']),
                {context: {
                    aname: function (feature) {
                        return get_attribute(feature, 'name');
                    },
                    aicon: function (feature) {
                        if (get_attribute(feature, 'stype_id') ===
                                marker_categories.id[0]) {
                            return marker_categories.icon[0];
                        } else if (get_attribute(feature, 'stype_id') ===
                                marker_categories.id[1]) {
                            return marker_categories.icon[1];
                        } else if (get_attribute(feature, 'stype_id') ===
                                marker_categories.id[2]) {
                            return marker_categories.icon[2];
                        } else {
                            return marker_categories.icon[3];
                        }
                    }
                }}
            ),
            'select': new OpenLayers.Style(
                OpenLayers.Util.applyDefaults({
                    externalGraphic: enhydris.static_url +
                        'images/drop_marker_selected.png',
                    graphicWidth: 21,
                    graphicHeight: 25,
                    graphicXOffset: -10,
                    graphicYOffset: -25,
                    fillOpacity: 1
                }, OpenLayers.Feature.Vector.style.select)
            ),
            'temporary': new OpenLayers.Style(
                OpenLayers.Util.applyDefaults({
                    graphicWidth: 21,
                    graphicHeight: 25,
                    graphicXOffset: -10,
                    graphicYOffset: -25,
                    fillOpacity: 0.7
                }, OpenLayers.Feature.Vector.style.select)
            )
        })
    });
    alayer.events.register('loadstart', alayer,
        function () { ShowProgress(ObjectName); });
    alayer.events.register('loadend', alayer,
        function () { HideProgress(ObjectName); });
    alayer.events.register('loadcancel', alayer,
        function () { HideProgress(ObjectName); });
    alayer.events.on({
        'featureselected': function (e) {
            ShowProgress('popup');
            InvokePopup(e.feature);
        },
        'featureunselected': function (e) {
            map.removePopup(apopup);
        }
    });
    return alayer;
}


function init() {
    'use strict';
    var stations = CreateLayer('Σταθμοί', 'stations', '#dd0022', '#990077');
    categories = [stations];
    var options = {
        'units' :   'm',
        'numZoomLevels' :   15,
        'sphericalMercator': true,
        'maxExtent': bounds,
        'projection': new OpenLayers.Projection('EPSG:900913'),
        'displayProjection': new OpenLayers.Projection('EPSG:4326')
    };
    map = new OpenLayers.Map('map', options);
    map.addControl(new OpenLayers.Control.ScaleLine());
    var ANavToolBar = new OpenLayers.Control.NavToolbar();
    map.addControl(ANavToolBar);
    $('div.olControlNavToolbar').css('top', '14px');
    $('div.olControlNavToolbar').css('left', '11px');
    var pzb = new OpenLayers.Control.PanZoomBar();
    pzb.zoomWorldIcon = false;
    map.addControl(pzb);
    map.addControl(new OpenLayers.Control.MousePosition());
    map.addControl(new OpenLayers.Control.OverviewMap());
    var ls = new OpenLayers.Control.LayerSwitcher();
    map.addControl(ls);
    map.addLayers(base_layers);
    map.addLayers(categories);
    ls.baseLbl.innerHTML = 'Base layers';
    ls.dataLbl.innerHTML = 'Data layers';
    var labelButton = new OpenLayers.Control.Button({
        type: OpenLayers.Control.TYPE_TOGGLE,
        title: 'Show labels',
        displayClass: 'LabelButtonClass',
        trigger: function () {}
    });
    labelButton.events.register('activate', labelButton,
        function () { setLayersLabels(true); });
    labelButton.events.register('deactivate', labelButton,
        function () { setLayersLabels(false); });
    var panel = new OpenLayers.Control.Panel({
        displayClass: 'olControlShowLabels'
    });
    panel.addControls([labelButton]);
    panel.activateControl(labelButton);
    map.addControl(panel);
    var agentity_id_repr = '';
    if (enhydris.map_mode === 2)
    {
        agentity_id_repr = enhydris.agentity_id;
    }
    var getboundoptions =  {'gentity_id': agentity_id_repr};
    Object.extend(getboundoptions, getUrlVars());
    $.ajax({url: enhydris.bound_url, data: getboundoptions, method: 'get',
        success: function (data) {
            var bounds = OpenLayers.Bounds.fromString(data);
            bounds.transform(new OpenLayers.Projection('EPSG:4326'), new
                                 OpenLayers.Projection('EPSG:900913'));
            map.zoomToExtent(bounds);
        },
        error: function () {
            map.zoomToExtent(bounds);
        }
    });
    var SelectControl = new OpenLayers.Control.SelectFeature(categories, {
        clickout: true,
        togle: false,
        multiple: false,
        hover: false
    });
    var HoverControl = new OpenLayers.Control.SelectFeature(categories, {
        clickout: false,
        togle: false,
        multiple: false,
        hover: true,
        highlightOnly: true,
        renderIntent: 'temporary',
        eventListeners: {
            beforefeaturehighlighted: function () {},
            featurehighlighted: function (e) {
                InvokeTooltip(get_attribute(e.feature, 'name'));
            },
            featureunhighlighted: function (e) {
                HideTooltip(get_attribute(e.feature, 'name'));
            }
        }
    });
    map.addControl(SelectControl);
    map.addControl(HoverControl);
    HoverControl.activate();
    SelectControl.activate();
    ANavToolBar.controls[0].events.on({
        'activate': function () {
            HoverControl.activate();
            SelectControl.activate();
        },
        'deactivate': function () {
            HoverControl.deactivate();
            SelectControl.deactivate();
        }
    });
    ANavToolBar.controls[0].activate();
}

function ShowProgress() {
    'use strict';
    var aprogress = document.getElementById('map_progress');
    if (aprogress === null) {
        return;
    }
    aprogress.innerHTML =
        '<img src="' + enhydris.static_url + 'images/wait16.gif">';
}


function HideProgress() {
    'use strict';
    var aprogress = document.getElementById('map_progress');
    if (aprogress === null) {
        return;
    }
    aprogress.innerHTML = '';
}


function setLayersLabels(value) {
    'use strict';
    for (var i = 0; i < categories.length; i++) {
        var layer = categories[i];
        var defaultStyle = layer.styleMap.styles['default'].defaultStyle;
        if (value) {
            defaultStyle.label = '${aname}';
        } else {
            defaultStyle.label = '';
        }
        layer.styleMap.styles['default'].setDefaultStyle(defaultStyle);
        layer.redraw();
    }
}
