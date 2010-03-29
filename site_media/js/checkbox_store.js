function toggleCheck(obj)
{	
    val = $(obj).attr('value');
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

