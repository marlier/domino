var service_attrs;
var id = 0;

$(document).ready(function(){
    detail_attrs = window.location.href.slice(window.location.href.indexOf('?') + 1)
    detail_attrs = detail_attrs.replace(/=/gi, ":").split('&');

    get_detail();

    get_detail_history("#history_table");

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
    showLoading("get detail");
    var url = "/api/alert?search="+detail_attrs.join(",");
    $.getJSON(url,function(json){
        a = json[0]
        id = a.id;
        $("#general #service").text(a.service);
        $("#general #host").text(a.host);
        $("#general #colo").text(a.colo);
        $("#general #environment").text(a.environment);
    
        d = new Date (0);
        d.setUTCSeconds(a.createDate);
        $("#status #date").text(d.toTimeString() + " (" + getRelTime(d) + ")");
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
            hideLoading("get detail");
        });
        graph("#history_graph", a);
    });
};

function print_ackBtn(a) {
    showLoading();
    acktime = new Date (0);
    acktime.setUTCSeconds(a.createDate);
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
    hideLoading();
};

function print_tags(tags) {
    showLoading();
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
    hideLoading();
};

function clean_value(val) {
    if ( val == "None" || val == null || val == '' ) { 
        return '-';
    } else {
        return val;
    };  
}

function get_detail_history(div) {
    showLoading();
    var url = "/api/history?since=30&search="+detail_attrs.join(",");
    console.debug(url);
    $.getJSON(url,function(json){
        $(".data-set").remove();
        $.each(json, function(i,a) {
            console.debug(a);
            row = $('<tr>');
            if ( a.status == "OK" ) {
                bgcolor = "alert-success";
            } else if ( a.status == "Warning" ) {
                bgcolor = "alert-warning";
            } else if ( a.status == "Critical") {
                bgcolor = "alert-danger";
            } else {
                bgcolor = "alert-info";
            };
            row.addClass('data-set alert '+bgcolor);
            d = new Date (0);
            d.setUTCSeconds(a.createDate);
            dateString = d.toTimeString();
            row.append("<td class='span2'>"+dateString+"</td>");
            row.append("<td class='span1'>"+a.status+"</td>");
            row.append("<td>"+a.message+"</td>");
            $(div).append(row);
        });
        hideLoading();
        return json;
    });
};

function graph(div, a) {
    showLoading("graph");
    var url = "/api/graph?segment=30&unit=DAY&search=environment:"+a.environment+"+colo:"+a.colo+"+host:"+a.host+"+service:"+a.service;
    console.debug(url);
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
                dataset.search = dataset.search.join(' + ');
            };  
            tmp = {label: dataset.search, data: mydata, lines: {show: true}, points: {show: true}}
            datasets.push(tmp);
        });
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
                    position: "nw"
                }   
            }   
            );  
            hideLoading('graph');
        return json;
    }); 
}
