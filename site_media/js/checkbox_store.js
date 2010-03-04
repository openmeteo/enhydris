function syncSids()
{
    t_osids = $(document).getUrlParam("selected_ids");
    if ( t_osids ) {
        t_osids = t_osids.replace(/%2C/g, ',');
        t_osids = t_osids.substring(0, t_osids.length-1).split(',');
        for (i in t_osids ) {
            sids.push(t_osids[i]);
        }
    }
}

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
        new_href += station_id + '%2C';
    }

    $(src).attr({'href': orig_href.substring(0, orig_href.indexOf('&selected_ids=')+14) + new_href});
}

function toggleCheck()
{
    val = $(this).attr('value');
    if (detectItem(sids,val)) {
        sids = removeItem(sids,val);
    } else { 
        sids.push(val);
    }

}

function detectItem(originalArray, itemToDetect) {
    var j = 0;
    while (j < originalArray.length) {
        if (originalArray[j] == itemToDetect) {
            return true;
        } else { j++; }
    }
    return false;
}


function removeItem(originalArray, itemToRemove) {
    var j = 0;
    while (j < originalArray.length) {
    //  alert(originalArray[j]);
    if (originalArray[j] == itemToRemove) {
            originalArray.splice(j, 1);
    } else { j++; }
    }
   
    return originalArray;

}

