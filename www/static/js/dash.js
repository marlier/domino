$(document).ready(function(){
	chronological("#new_data", "newest");
	chronological("#old_data", "oldest");
	frequent("#frequent_data");
//	graph("#graph", 7, "DAY") 
});

function chronological(div, direction) {
    showLoading("chron");
	var url = "/api/alert?search=status:-OK&limit=10&sort=" + direction;
	$.getJSON(url,function(json){
		print_alert_list(json,div);
        hideLoading("chron");
		return json;
	});
};

function frequent(div) {
    console.debug('Getting frequent data');
    showLoading("freq");
	$.getJSON("/api/analytics?name=frequent&since=7&limit=10",function(json){
		print_frequent_alert_list(json,div);
        hideLoading("freq");
		return json;
	});
};

function status(div) {
	var url = base_url+"metric?metric=status";
    showLoading("status");
	$.getJSON(url,function(json){
		print_frequent_alert_list(json,div);
        hideLoading("status");
		return json;
	});
};

function print_frequent_alert_list(alerts,div) {
    console.debug('Print frequent alerts');
    showLoading("print freq");
	$(div + " .data-set").remove();
	$.each(alerts,function(i,a) {
        o = $('<tr class="data-set">');
		o.append('<td>' + a.count + '</td>');
        o.append('<td>' + a.environment + '</td>');
        o.append('<td>' + a.colo + '</td>');
        o.append('<td>' + a.host + '</td>');
        o.append('<td>' + a.service + '</td>');
        $(div).append(o);
	});
    hideLoading("print freq");
};

function print_alert_list(alerts,div) {
    showLoading("print alert list");
    $(div + " .data-set").remove();
	$.each(alerts,function(i,a) {
        o = $('<tr class="data-set">');
        if ( a.status == "OK" ) {
            o.addClass("success")
        } else if ( a.status == "Warning" ) {
            o.addClass("warning")
        } else if ( a.status == "Critical" ) {
            o.addClass("error")
        } else { 
            o.addClass("info")
        };
        o.append('<td>' + new Date(a.createDate+"Z").toDateString() + '</td>')
        o.append('<td>' + a.environment + '</td>');
        o.append('<td>' + a.colo + '</td>');
        o.append('<td>' + a.host + '</td>');
        o.append('<td>' + a.service + '</td>');
        $(div).append(o);
	});
    hideLoading("print alert list");
};

function get_graph_data(div) {
	graph(div, $("#segment").val(), $('select option:selected').text() );
}

function graph(div, segment, unit) {
	timeperiod = $("input[name='timeperiod']:checked").val();
	var url = base_url+"graph?segment=" + segment + "&unit=" + unit + "&search=" + $("#graph_filter").val();
	$.getJSON(url,function(json){
		if (process_header(json.status, json.status_message)) {
				var datapoints = new Array();
				var labelpoints = new Array();
				var mydata = new Array();
				var minValue = "nil";
				var maxValue = "nil";
				$.each(json.data[0].datapoints, function(i,d) {
					datapoints.push(d.count);
					labelpoints.push(new Date(d.date+"Z").getDate());
					if ((minValue > d.min) || (minValue == "nil")) {
						minValue = d.min
					};
					if ((maxValue > d.max) || (maxValue == "nil")) {
						maxValue = d.max
					};
					mydata.push([Date.parse(new Date(d.date+'Z')),d.count]);
				});
				if (json.data[0].search == 0) {
					json.data[0].search = "All";
				} else {
					json.data[0].search = json.data[0].search.join();
				};
				chart = new Highcharts.Chart({
					chart: {
						renderTo: 'graph',
						type: 'spline'
					},
					title: {
						text: "Dashboard Graphing Tool"
					},
					subtitle: {
						text: json.data[0].terms
					},
					xAxis: {
						type: 'datetime',
						dateTimeLabelFormats: { // don't display the dummy year
		                    day: '%b %e'
		                }
					},
					yAxis: {
		                title: {
		                    text: 'Num of alerts'
		                },
		                min: 0
		            },
		            series: [{
			            name: 'Num of alerts',
		                data: mydata
			        }]
				});
		};
		return json.data;
	});
}



