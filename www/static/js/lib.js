var search_terms = new Array();

// keep track of number of things loading so not to close loading window while 
// something is still loading (ie like a garbage collector)
var loading_gc = 0;

$(document).ready(function(){
    // build loading div
    div = $('<div>');
    div.attr('id', 'loading');
    $('body').append(div);
    $('#loading').load('static/html/loading.html');
    $('#loadingModal').modal({
        keyboard: false
    }); 
    showLoading('lib doc ready');
	$('#top').load('static/html/header.html');
	$('#bottom').load('static/html/footer.html');
    hideLoading('lib doc ready');
});

function query(div,sidebar_div,team,count){
    showLoading("query");
	count = typeof count !== 'undefined' ? count : 0;
	team = typeof team !== 'undefined' ? team : "";
	console.info("Query: " + table);
	var url = '/api/'+table+"?limit="+count+"&search="+search_terms.join(",");
	console.debug(url);
	$.getJSON(url,function(json){
		if (table == "users" || table == "user") {
			print_users(json,div,sidebar_div);
		} else if (table == "teams" || table == "team") {
			print_teams(json,div,sidebar_div)
		} else if (table == "alerts" || table == "alert") {
			print_alerts(json,div,sidebar_div);
            print_search_terms();
		};
        hideLoading("query");
		return json;
	});
};

function showLoading(log) {
    $("#loadingModal").modal('show');
    ++loading_gc;
    console.debug("show loading: "+log+" ("+loading_gc+")");
};

function hideLoading(log) {
    --loading_gc;
    
    if ( loading_gc <= 0 ) {
        $("#loadingModal").modal('hide');
    };
    if ( loading_gc < 0 ) {
        loading_gc = 0;
    };
    console.debug("hide loading: "+log+" ("+loading_gc+")");
};

function getRelTime(thedate) {
    now = new Date();
    d = new Date(thedate);
    one_min = 60; 
    one_hour = 60*60;
    one_day = 60*60*24;
    date_diff = Math.floor(now.getTime() / 1000) - Math.floor(d.getTime() / 1000)
    if ( date_diff < 60 ) {
        ts = Math.ceil(date_diff) + " seconds ago";
    } else if ( date_diff / one_min <= 60 ) {         
        ts = Math.ceil(date_diff / one_min) +" min ago";
    } else if ( date_diff / one_hour <= 24 ) {
        ts = Math.ceil(date_diff / one_hour) + " hours ago";
    } else {
        ts = Math.ceil(date_diff / one_day) + " days ago";
    };
    return ts
}

function validate_email(email) {
    var pattern = new RegExp(/^((([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+(\.([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+)*)|((\x22)((((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(([\x01-\x08\x0b\x0c\x0e-\x1f\x7f]|\x21|[\x23-\x5b]|[\x5d-\x7e]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(\\([\x01-\x09\x0b\x0c\x0d-\x7f]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))))*(((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(\x22)))@((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?$/i);
    return pattern.test(email);
};

function validate_phone(phone) {
	if ( phone.length == 12 ) {
		return true
	} else {
		return false
	}
};

function validate_name(name) { 
	if ( name.length > 0 ) {
		return true
	} else {
		return false
	}
}

var unique = function(origArr) {
    var newArr = [],
        origLen = origArr.length,
        found,
        x, y;

    for ( x = 0; x < origLen; x++ ) {
        found = undefined;
        for ( y = 0; y < newArr.length; y++ ) {
            if ( origArr[x] === newArr[y] ) {
              found = true;
              break;
            }
        }
        if ( !found) newArr.push( origArr[x] );
    }
   return newArr;
};

