/* global enhydris */

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
