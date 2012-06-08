var base_url='http://localhost:8009/api/';
var search_terms = new Array();

$(document).ready(function(){
	$('#top').load('html/header.html');
	$('#bottom').load('html/footer.html');
});

function query(div,sidebar_div,team,count){
	count = typeof count !== 'undefined' ? count : 0;
	team = typeof team !== 'undefined' ? team : "";
	console.info("Query: " + table);
	var url = base_url+"query?target="+table+"&count="+count+"&search="+search_terms.join(",");
	console.debug(url);
	$.getJSON(url,function(json){
		if (process_header(json.status, json.status_message)) {
			if (table == "users" || table == "user") {
				print_users(json.data,div,sidebar_div);
			} else if (table == "teams" || table == "team") {
				print_teams(json.data,div,sidebar_div)
			} else if (table == "alerts" || table == "alert") {
				print_alerts(json.data,div,sidebar_div);
			};
			print_search_terms();
			return json.data;
		};
	});
};

function add_search_terms(term) {
	console.debug("adding search term:" + term);
	term = term.split('+');
	console.debug(term);
	search_terms.push(term);
	search_terms = $.unique(search_terms);
	print_search_terms();
	query("#data","#sidebar_data");
};

function del_search_terms(term) {
	console.debug("deleting search term:" + term);
	search_terms = jQuery.grep(search_terms, function(value) {
    	return value != term;
	});
	print_search_terms();
	query("#data","#sidebar_data");
};

function print_search_terms() {
	console.debug("printing search terms");
	$('#search_terms').html('');
	var output = '';
	output = output + '<div class="search_terms_data">';
	output = output + '<ul>';
	$.each(search_terms,function(i,s) {
		console.debug(s);
		output = output + '<li><span onclick="del_search_terms(\'' + s + '\')">' + s + '</span></li>';
	});
	output = output + '</ul>';
	//console.debug(output);
	$('#search_terms').html(output);
};

function process_header(status, status_message) {
	if ( status % 100 == 0 ) {
		return new Boolean(1);
	} else {
		console.log(status, status_message);
		alert("Error Num: " + status + "\nError Message: " + status_message);
		return new Boolean(0);
	};
};

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