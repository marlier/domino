var table = "alert";

$(document).ready(function(){

    console.debug('starting query')
    $("#loadingDiv").show();
	query("#alerts_data","#sidebar_data");
	
	$("#search_input").keyup(function(event){
    	if(event.keyCode == 13){
			//console.debug($("#search_input").val());
        	add_search_terms($("#search_input").val());
    	}
	});
    alt = false
    $(document).keydown(function(e) {
        if (e.altKey) {
            alt = true
        };
    });
    $(document).keyup(function(e) {
        alt = false
    });

});

$(document).click(function(e) {
    if (e.altKey) {
        var alt = true
    } else {
        var alt = false
    };
});

function print_alerts(alerts,alert_div,sidebar_div) {
    showLoading();
	console.debug("Printing alerts");
	var environments = new Array();
	var colos = new Array();
	var hosts = new Array();
	var services = new Array();
	var statuses = new Array();
	var tags = new Array();

    var ok = 0;
    var warning = 0;
    var critical = 0;
    var unknown = 0;

    //remove any old alerts before trying to update the table
    $(alert_div + " .data-set").remove();
    console.debug($(alert_div).html());
	$("#alert_total").text(alerts.length);
    $("#alert_total").attr('title', alerts.length + " alerts displayed");
	$.each(alerts,function(i,a) {
        if( $.inArray(a.environment, environments) == -1 ){
            environments.push(a.environment);
        };
        if( $.inArray(a.colo, colos) == -1 ){
            colos.push(a.colo);
        };
        if( $.inArray(a.host, hosts) == -1 ){
            hosts.push(a.host);
        };
        if( $.inArray(a.service, services) == -1 ){
            services.push(a.service);
        };
        if( $.inArray(a.status, statuses) == -1 ){
            statuses.push(a.status);
        };
        $.each(a.tags.split(','),function(i,t) {
            if( $.inArray(t, tags) == -1 ){
                tags.push(t);
            };
        });
        if (a.status == "OK") {
            ++ok;
            class_name = "-success";
        } else if ( a.status == "Warning" ) {
            ++warning;
            class_name = "-warning";
        } else if ( a.status == "Critical" ) {
            ++critical;
            class_name = "-danger";
        } else {
            ++unknown;
            class_name = ""
        };

        if (i <= 100) {
            o = $('<li>');
            o.addClass('data-set');
            btns = $('<div>');
            btns.addClass("btn-group");
            btns.append('<a href="#" term="environment" tag="'+a.environment+'" class="btn btn-large btn-info addSearch">'+a.environment+'</a>');
            btns.append('<a href="#" term="colo" tag="'+a.colo+'" class="btn btn-large btn-info addSearch">'+a.colo+'</a>');
            btns.append('<a href="#" term="host" tag="'+a.host+'" class="btn btn-large btn-info addSearch">'+a.host+'</a>');
            btns.append('<a href="#" term="service" tag="'+a.service+'" class="btn btn-large btn-info addSearch">'+a.service+'</a>');
            btns.append('<a href="#" term="status" tag="'+a.status+'" class="btn btn-large btn'+class_name+' addSearch">'+a.status+'</a>');
            tagBtns = $('<ul>');
            tagBtns.addClass('nav nav-pills');
            $.each(a.tags.split(','),function(i,t) {
                tagBtns.append('<li class="grey active"><a href="#" class="addSearch" term="tags" tag="'+t+'" >'+t+'</a></li>');
            });
            body = $('<p style="margin-bottom: 0px;">');
            body.addClass('well well-small');
            body.text(a.summary);
	    	d = new Date(a.createDate+"Z");
            relDate = getRelTime(a.createDate+"Z");
            d = $('<div>');
            d.html('<i class="icon icon-time"></i> '+relDate);
            o.append(btns);
            o.append('<a href="/detail?host='+a.host+'&environment='+a.environment+'&colo='+a.colo+'&service='+a.service+'" class="btn btn-large btn-primary pull-right"><i class="icon-white icon-share"></i> Go</a>');
            o.append(d);
            o.append(body);
            o.append(tagBtns);
            $(alert_div).append(o);
        };
	});

    console.debug('done printing alerts');

    // print sidebar
    $(sidebar_div + " .data-set").remove();

    build_sidebar_item(sidebar_div,environments,'icon-globe','Environments', 'environment');
    build_sidebar_item(sidebar_div,colos,'icon-tasks','Colos', 'colo');
    build_sidebar_item(sidebar_div,hosts,'icon-hdd','Hosts', 'host');
    build_sidebar_item(sidebar_div,services,'icon-th-list','Services', 'service');
    build_sidebar_item(sidebar_div,statuses,'icon-certificate','Statuses', 'status');
    build_sidebar_item(sidebar_div,tags,'icon-tags','Tags', 'tags');

    $(".addSearch").click(function(e) {
        term = $(this).attr('term');
        if (alt == true) {
            tag = "-" + $(this).attr('tag');
        } else {
            tag = $(this).attr('tag');
        };
        add_search_terms(term+':'+tag);
    });

    // load unicorn.js now that we've finished building our sidebar
    $.getScript("/static/js/unicorn.js", function(data, textStatus, jqxhr) {});
    
    total = ok + warning + critical + unknown

    $("#statebar .progress #ok").css('width', ((ok / total) * 100)+"%");
    $("#statebar .progress #warning").css('width', ((warning / total) * 100)+"%");
    $("#statebar .progress #critical").css('width', ((critical / total) * 100)+"%");
    $("#statebar .progress #unknown").css('width', ((unknown / total) * 100)+"%");

    $("#statebar .stats-plain #ok").text(ok);
    $("#statebar .stats-plain #warning").text(warning);
    $("#statebar .stats-plain #critical").text(critical);
    $("#statebar .stats-plain #unknown").text(unknown);    
    $("#statebar .stats-plain #total").text(total);

    console.debug("done printing sidebar");
    hideLoading();
};

function build_sidebar_item(div,objs,icon,title,search_term) {
    s = $('<li>');
    s.addClass('submenu data-set');
    s.append('<a href="#"><i class="icon '+icon+'"></i> <span>'+title+'</span> <span class="label">'+objs.length+'</span></a>');
    s_list = $('<ul>');
    $.each(objs,function(i,x) {
        s_list.append('<li><a href="#" class="addSearch" term="'+search_term.toLowerCase()+'" tag="'+x+'">' + x + '</a></li>')
    });
    s.append(s_list);
    $(div).append(s);
};

function add_search_terms(term) {
    console.debug("adding search term:" + term);
    term = term.split('+');
    search_terms.push(term);
    search_terms = $.unique(search_terms);
    print_search_terms();
    query("#alerts_data","#sidebar_data");
};

function del_search_terms(term) {
    console.debug("deleting search term:" + term);
    search_terms = jQuery.grep(search_terms, function(value) {
        return value != term;
    }); 
    print_search_terms();
    query("#alerts_data","#sidebar_data");
};

function print_search_terms() {
    showLoading();
    console.debug("printing search terms");
    $('#search_terms').html('');
    o = $("<ul>");
    $("#filter_total").text(search_terms.length);
    $("#filter_total").attr('title', search_terms.length + " filters applied");
    $.each(search_terms,function(i,s) {
        o.append('<li><a href="#" class="btn" onclick="del_search_terms(\'' + s + '\')">' + s + '</a></li>');
    }); 
    $('#search_terms').append(o);
    console.debug('done adding search terms');
    hideLoading();
};
