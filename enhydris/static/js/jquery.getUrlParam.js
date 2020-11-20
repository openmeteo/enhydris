/* Copyright (c) 2006-2007 Mathias Bank (http://www.mathias-bank.de)
 * Dual licensed under the MIT (http://www.opensource.org/licenses/mit-license.php)
 * and GPL (http://www.opensource.org/licenses/gpl-license.php) licenses.
 *
 * Version 2.1
 *
 * Thanks to
 * Hinnerk Ruemenapf - http://hinnerk.ruemenapf.de/ for bug reporting and fixing.
 * Tom Leonard for some improvements
 *
 */
jQuery.fn.extend({
/**
* Returns get parameters.
*
* If the desired param does not exist, null will be returned
*
* To get the document params:
* @example value = $(document).getUrlParam("paramName");
*
* To get the params of a html-attribut (uses src attribute)
* @example value = $('#imgLink').getUrlParam("paramName");
*/
  getUrlParam(strParamName) {
    const paramName = escape(unescape(strParamName));

    const returnVal = [];
    let qString = null;

    if ($(this).attr('nodeName') === '#document') {
      // document-handler
      if (window.location.search.search(paramName) > -1) {
        qString = window.location.search.substr(1, window.location.search.length).split('&');
      }
    } else if ($(this).attr('src') !== 'undefined') {
      const strHref = $(this).attr('src');
      if (strHref.indexOf('?') > -1) {
        const strQueryString = strHref.substr(strHref.indexOf('?') + 1);
        qString = strQueryString.split('&');
      }
    } else if ($(this).attr('href') !== 'undefined') {
      const strHref = $(this).attr('href');
      if (strHref.indexOf('?') > -1) {
        const strQueryString = strHref.substr(strHref.indexOf('?') + 1);
        qString = strQueryString.split('&');
      }
    } else {
      return null;
    }

    if (qString == null) return null;

    for (let i = 0; i < qString.length; i += 1) {
      if (escape(unescape(qString[i].split('=')[0])) === paramName) {
        returnVal.push(qString[i].split('=')[1]);
      }
    }

    if (returnVal.length === 0) return null;
    if (returnVal.length === 1) return returnVal[0];
    return returnVal;
  },
});
