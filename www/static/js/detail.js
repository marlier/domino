var service_attrs;
var id = 0;

$(document).ready(function(){
    detail_attrs = window.location.href.slice(window.location.href.indexOf('?') + 1)
    detail_attrs = detail_attrs.replace(/=/gi, ":").split('&');
    
    get_detail();
//  get_detail_graph("#graph");
//  get_detail_history("#history");

    $("#addTagBtn").click(function() {
        console.debug("adding tag");
        tag = $("input#addatag").val();

        $.ajax({
            type: 'POST',
            contentType: 'application/json',
            url: "/api/alert/"+id+"/addtag/"+tag,
            dataType: "json",
            data: {},
            success: function(data, textStatus, jqXHR){
                print_tags(data[0].tags.split(','));
            },    
            error: function(jqXHR, textStatus, errorThrown){
            }     
        }); 
    });

});


function get_detail(){
    var url = "/api/alert?search="+detail_attrs.join(",");
    $.getJSON(url,function(json){
        a = json[0]
        id = a.id;
        $("#general #service").text(a.service);
        $("#general #host").text(a.host);
        $("#general #colo").text(a.colo);
        $("#general #environment").text(a.environment);
    
        $("#status #date").text(a.createDate);
        $("#status #status").text(a.status);
        $("#status #message").text(a.message);
        if ( a.status == "OK" ) {
            $("#status .widget-content").addClass("alert alert-success");
        } else if ( a.status == "Warning" ) {
            $("#status .widget-content").addClass("alert alert-warning");
        } else if ( a.status == "Critical" ) {
            $("#status .widget-content").addClass("alert alert-error");
        } else {
            $("#status .widget-content").addClass("alert alert-info");
        };

        console.debug(a);

        print_tags(a.tags.split(','));
        print_ackBtn(a);

        var url = "/api/rule?environment="+a.environment+"&colo="+a.colo+"&host="+a.host+"&service="+a.service+"&status="+a.status+"&tag="+a.tags;
        $.getJSON(url,function(json) {
            rules = json;
            $('#rules_rows .data-set').remove();
            $("#rules_total").text(rules.length);
            $("#rules_total").attr('title', rules.length + " rules displayed");
            $.each(rules,function(i,r) {
                console.debug(r);
                row = $('<tr>');
                row.addClass('data-set');
                row.append('<td class="alert-info">' + clean_value(r['environment']) + '</td>');
                row.append('<td class="alert-info">' + clean_value(r['colo']) + '</td>');
                row.append('<td class="alert-info">' + clean_value(r['host']) + '</td>');
                row.append('<td class="alert-info">' + clean_value(r['service']) + '</td>');
                row.append('<td class="alert-info">' + clean_value(r['state']) + '</td>');
                row.append('<td class="alert-info">' + clean_value(r['tag']) + '</td>');
                row.append('<td class="alert-success">' + clean_value(r['addTag']) + '</td>');
                row.append('<td class="alert-success">' + clean_value(r['removeTag']) + '</td>');
                $("#rules_rows").append(row);
            });
        });
    });
};

function print_ackBtn(a) {
    acktime = new Date(a.acktime+"Z");
    $(".ack-data-set").remove();
    if (a.ack == 0) {
        $("#status .widget-title").append('<div class="buttons ack-data-set"><a id="'+a.id+'" class="btn btn-mini active"><i class="icon-ok-sign"></i> Acknowledge</a></div>');
    } else {
        $("#status .widget-title").append('<div class="buttons ack-data-set"><a id="'+a.id+'" class="ack-data-set btn btn-mini"><i class="icon-ok-sign"></i> Acknowledge</a></div>');
    };

    $("a.ack-data-set").click(function() {
        console.debug("acking...");

        $.ajax({
            type: 'POST',
            contentType: 'application/json',
            url: "/api/alert/"+id+"/ack",
            dataType: "json",
            data: {},
            success: function(data, textStatus, jqXHR){
                print_ackBtn(data[0]);
            },
            error: function(jqXHR, textStatus, errorThrown){
            }
        });
    });

};

function print_tags(tags) {
    tagBtns = $('<ul>');
    tagBtns.addClass('nav nav-pills');
    $.each(tags,function(i,t) {
        tagBtns.append('<li class="grey active"><a class="remove_tag" tag="'+t+'" id="'+a.id+'" href="#"><i class="icon-white icon-remove"></i> '+t+'</a></li>');
    });
    $('#tags .widget-content').html(tagBtns);

    $(".remove_tag").click(function() {
        id = $(this).attr('id');
        tag = $(this).attr('tag');
        $.ajax({
            type: 'POST',
            contentType: 'application/json',
            url: "/api/alert/"+id+"/removetag/"+tag,
            dataType: "json",
            data: {},
            success: function(data, textStatus, jqXHR){
                print_tags(data[0].tags.split(','));
            },
            error: function(jqXHR, textStatus, errorThrown){
            }
        });
    });
};

function clean_value(val) {
    if ( val == "None" || val == null || val == '' ) { 
        return '-';
    } else {
        return val;
    };  
}

function get_detail_history(div) {
    var url = base_url+"history?since=30&search="+detail_attrs.join(",");
    $.getJSON(url,function(json){
        print_alerts(json,div);
        return json;
    });
};

function get_detail_graph(div) {
    var url = base_url+"graph?segment=30&unit=DAY&terms="+detail_attrs.join("%2B");
    $.getJSON(url,function(json){
        if (process_header(json.status, json.status_message)) {
            var datapoints = new Array();
            var labelpoints = new Array();
            var minValue = "nil";
            var maxValue = "nil";
            $.each(json.data[0].datapoints, function(i,d) {
                datapoints.push(d.count);
                labelpoints.push(new Date(d.date).getDate());
                if ((minValue > d.min) || (minValue == "nil")) {
                    minValue = d.min
                };
                if ((maxValue > d.max) || (maxValue == "nil")) {
                    maxValue = d.max
                };
            });
            console.debug(json.data[0]);
            if (json.data[0].terms == 0) {
                json.data[0].terms = "All";
            } else {
                json.data[0].terms = json.data[0].search.join();
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
    search = $("#graph_filter").val();
    console.debug($('select option:selected').text() );
    timeperiod = $("input[name='timeperiod']:checked").val();
    var url = base_url+"graph?segment=" + segment + "&unit=" + unit + "&search=" + search;
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
                    title: 'Custom Chart', 
                    titleColor: 'black', 
                    height: 400, 
                    width: 700,
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
        output = output + '<div class="alert_detail">';
        output = output + '<ul>';
        output = output + '<li>' + a.teams[0].name + '</li>';
        output = output + '<li>' + a.status + '</li>';
        output = output + '</ul>';
        output = output + '<div class="alert_detail_msg" id="'+ a.status +'">' + a.summary;
        output = output + '<div class="alert_detail_date">' + new Date(a.createDate+'Z').toDateString() + '</div>';
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
