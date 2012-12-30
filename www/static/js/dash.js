$(document).ready(function(){
    console.debug('foo dash');
	chronological("#new_data", "newest");
	chronological("#old_data", "oldest");
	frequent("#frequent_data");
	graph("#graph", 7, "DAY") 
    $("#custom_graph #updateBtn").click(function() {
        get_graph_data("#graph") 
    });
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

function print_frequent_alert_list(alerts,div) {
    console.debug('Print frequent alerts');
    showLoading("print freq");
	$(div + " .data-set").remove();
	$.each(alerts,function(i,a) {
        o = $('<tr class="data-set">');
        o.append('<td><a href="/detail?host='+a.host+'&environment='+a.environment+'&colo='+a.colo+'&service='+a.service+'" class="btn btn-primary btn-small"><i class="icon-white icon-share"></i> Go</a></td>');
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
        d = new Date(0);
        d.setUTCSeconds(a.createDate);
        o.append('<td>' + getRelTime(d) + '</td>')
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
    showLoading("graph");
	var url = "/api/graph?segment=" + segment + "&unit=" + unit + "&search=" + $("#graph_filter").val();
	$.getJSON(url,function(json){
        var datasets = [];
        $.each(json, function(i,dataset) {
        	var mydata = new Array();
	    	$.each(dataset.datapoints, function(i,d) {
                myDate = new Date(0);
                myDate.setUTCSeconds(d.date);
		    	mydata.push([myDate,d.count]);
    		});
	    	if (dataset.search == 0) {
		    	dataset.search = "All";
    		} else {
                console.debug(dataset);
	    		dataset.search = dataset.search.join('+');
		    };
            tmp = {label: dataset.search, data: mydata, lines: {show: true}, points: {show: true}}
            datasets.push(tmp);
        });
        console.debug(datasets);
        $.plot(
            $(div),
            datasets,
            {
                xaxis: {
                   mode: "time",
                   timeformat: "%b %d %h:%M:%S"
                },
                legend: {
                   show: true,
                }
            }
            );
            hideLoading('graph');
		return json;
	});
}



