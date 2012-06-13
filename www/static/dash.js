$(document).ready(function(){
	chronological("#new", "new");
	chronological("#old", "old");
	frequent("#frequent");
	graph("#graph", 7, "DAY") 
});

function chronological(div, direction) {
	var url = base_url+"alert?limit=10&sort=" + direction;
	$.getJSON(url,function(json){
		if (process_header(json.status, json.status_message)) {
				print_alert_list(json.data,div);
		};
		return json.data;
	});
};

function frequent(div) {
	var url = base_url+"analytics?name=frequent&limit=10";
	$.getJSON(url,function(json){
		if (process_header(json.status, json.status_message)) {
				print_frequent_alert_list(json.data,div);
		};
		return json.data;
	});
};

function status(div) {
	var url = base_url+"metric?metric=status";
	$.getJSON(url,function(json){
		if (process_header(json.status, json.status_message)) {
				print_frequent_alert_list(json.data,div);
		};
		return json.data;
	});
};

function print_frequent_alert_list(alerts,div) {
	var output = '';
	output = output + '<div id="dash_list">';
	$.each(alerts,function(i,a) {
		output = output + '<div>';
		output = output + '<ul>';
		output = output + '<li>' + a.count + '</li><li>' + a.environment + '</li><li>'+ a.colo +'</li><li>'+ a.host +'</li><li>'+ a.service +'</li>';
		output = output + '</ul>';
		output = output + '</div>';
	});
	output = output + '</div>';
	$(div).html(output);
};

function print_alert_list(alerts,div) {
	var output = '';
	output = output + '<div id="dash_list">';
	$.each(alerts,function(i,a) {
		output = output + '<div>';
		output = output + '<ul>';
		output = output + '<li>' + new Date(a.createDate+"Z").toDateString() + '</li><li>' + a.environment + '</li><li>'+ a.colo +'</li><li>'+ a.host +'</li><li>'+ a.service +'</li>';
		output = output + '</ul>';
		output = output + '</div>';
	});
	output = output + '</div>';
	$(div).html(output);
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



