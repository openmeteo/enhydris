function storeValue()
{
    src = this;
    if ( $(src).attr('href').indexOf("&selected_ids") >= 0 ) {
        orig_href = ($(src).attr('href'));
    } else {
        orig_href = ($(src).attr('href')) + '&selected_ids=';
    }
    
    new_href = '';

    for( var i = 0; i<  sids.length; i++ ) { 
            station_id = sids[i]; 
            if ( orig_href.indexOf(station_id) < 0 ) {
                new_href += station_id + '%2C';
            } else { 
                orig_href = orig_href.replace(station_id + "%2C",""); 
            }
    }
      
    $(src).attr({'href': orig_href + new_href});
}

function toggleCheck()
{
	if ( jQuery.inArray($(this).attr('value'), sids) > -1 ) {
 	   sids.pop($(this).attr('value'));
	} else {
 	   sids.push($(this).attr('value'));
	}
}
