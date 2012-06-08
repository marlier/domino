var service_attrs;

$(document).ready(function(){
	detail_attrs = window.location.href.slice(window.location.href.indexOf('?') + 1)
	detail_attrs = detail_attrs.replace(/=/gi, ":").split('&');
	
	get_detail("#current");
	get_detail_graph("#graph");
	get_detail_history("#history");
});


function get_detail(div){
	var url = base_url+"query?target=alerts&search="+detail_attrs.join(",");
	console.debug(url);
	$.getJSON(url,function(json){
		if (process_header(json.status, json.status_message)) {
			if ( json.data.length > 1 ) {
				print_alerts(json.data,div);
			} else if (json.data.length == 1) {
				print_current(json.data[0],div);
			} else {
				alert("Hmmm, can't find any detail on your criteria");
			}
			return json.data;
		};
	});
};

function get_detail_history(div) {
	var url = base_url+"query?target=alerthistory&since=30&search="+detail_attrs.join(",");
	$.getJSON(url,function(json){
		if (process_header(json.status, json.status_message)) {
			print_alerts(json.data,div);
			return json.data;
		};
	});
};

function get_detail_graph(div) {
	var url = base_url+"metric?metric=graph&segment=30&unit=DAY&terms="+detail_attrs.join("%2B");
	$.getJSON(url,function(json){
		if (process_header(json.status, json.status_message)) {
			var datapoints = new Array();
			var labelpoints = new Array();
			var minValue = "nil";
			var maxValue = "nil";
			$.each(json.data[0].data, function(i,d) {
				datapoints.push(d.count);
				labelpoints.push(new Date(d.date).getDate());
				if ((minValue > d.min) || (minValue == "nil")) {
					minValue = d.min
				};
				if ((maxValue > d.max) || (maxValue == "nil")) {
					maxValue = d.max
				};
			});
			if (json.data[0].terms == 0) {
				json.data[0].terms = "All";
			} else {
				json.data[0].terms = json.data[0].terms.join();
			};
			$(div).gchart('destroy');
			$(div).gchart({
				type: 'line',
				title: '30 Day Chart', 
				titleColor: 'black', 
				height: 400, 
				width: 900,
				minValue: minValue,
				maxValue: maxValue,
				series: [$.gchart.series('', datapoints, 'blue', json.data[0].min, json.data[0].max)], 
				axes: [$.gchart.axis('bottom', labelpoints, 'black'), $.gchart.axis('left', json.data[0].min, json.data[0].max, 'black', 'left')], 
				legend: 'right' 
			});
			$( "#tabs" ).tabs();
			return json.data;
		};
	})
}

function graph(div, segment, unit) {
	terms = $("#graph_filter").val();
	console.debug($('select option:selected').text() );
	timeperiod = $("input[name='timeperiod']:checked").val();
	var url = base_url+"metric?metric=graph&segment=" + segment + "&unit=" + unit + "&terms=" + terms;
	$.getJSON(url,function(json){
		if (process_header(json.status, json.status_message)) {
				var datapoints = new Array();
				var labelpoints = new Array();
				var minValue = "nil";
				var maxValue = "nil";
				$.each(json.data[0].data, function(i,d) {
					console.debug(d);
					datapoints.push(d.count);
					labelpoints.push(new Date(d.date).getDate());
					if ((minValue > d.min) || (minValue == "nil")) {
						minValue = d.min
					};
					if ((maxValue > d.max) || (maxValue == "nil")) {
						maxValue = d.max
					};
				});
				if (json.data[0].terms == 0) {
					json.data[0].terms = "All";
				} else {
					json.data[0].terms = json.data[0].terms.join();
				};
				$(div).gchart('destroy');
				$(div).gchart({
					type: 'line',
					title: 'Custom Chart', 
					titleColor: 'black', 
					height: 400, 
					width: 900,
					minValue: minValue,
					maxValue: maxValue,
					series: [$.gchart.series(json.data[0].terms, datapoints, 'blue', json.data[0].min, json.data[0].max)], 
    				axes: [$.gchart.axis('bottom', labelpoints, 'black'), $.gchart.axis('left', json.data[0].min, json.data[0].max, 'black', 'left')], 
    				legend: 'right' 
				});
		};
		return json.data;
	});
}

function print_current(data, div) {
	$(div).html('');
	var output = '';
	console.debug(data);
	output = output + 'Status: '+data.status + '<br />';
	output = output + 'Host: '+data.host + '<br />';
	output = output + 'Service: '+data.service + '<br />';
	output = output + 'Colo: '+data.colo + '<br />';
	output = output + 'Environment: '+data.environment + '<br />';
	output = output + 'Team: '+data.teams[0].name + '<br /></br>';
	
	output = output + 'Date: '+new Date(data.createDate+'Z').toDateString()  + '<br />';
	output = output + 'Message:\
	'+data.message + '<br />';

	$(div).html(output);	
};

function print_alerts(data, div) {
	$(div).html('');
	var output = '';
	
	$.each(data,function(i,a) {
		output = output + '<div class="alert">';
		output = output + '<ul>';
		output = output + '<li onclick="add_search_terms(\'team:' + a.teams[0].name + '\')">' + a.teams[0].name + '</li>';
		output = output + '<li onclick="add_search_terms(\'environment:' + a.environment + '\',\'alerts\')">' + a.environment + '</li>';
		output = output + '<li onclick="add_search_terms(\'colo:' + a.colo + '\')">' + a.colo + '</li>';
		output = output + '<li onclick="add_search_terms(\'host:' + a.host + '\')">' + a.host + '</li>';
		output = output + '<li onclick="add_search_terms(\'service:' + a.service + '\')">' + a.service + '</li>';
		output = output + '<li onclick="add_search_terms(\'status:' + a.status + '\')">' + a.status + '</li>';
		output = output + '</ul>';
		output = output + '<div class="alert_body" id="'+ a.status +'">' + a.summary;
		output = output + '<div class="alert_date">' + new Date(a.createDate+'Z').toDateString() + '</div>';
		output = output + '</div>';
	});
	$(div).html(output);
};

function process_header(status, status_message) {
	if ( status % 100 == 0 ) {
		return new Boolean(1);
	} else {
		console.log(status, status_message);
		return new Boolean(0);
	};
};
