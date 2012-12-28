var table = "alert";

$(document).ready(function(){
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
	console.debug("Printing alerts");
	var output = '';
	var environments = new Array();
	var colos = new Array();
	var hosts = new Array();
	var services = new Array();
	var statuses = new Array();
	var tags = new Array();

    //remove any old alerts before trying to update the table
    $(alert_div + " .data-set").remove();
    console.debug($(alert_div).html());
	$("#alert_total").text(alerts.length);
    $("#alert_total").attr('title', alerts.length + " alerts displayed");
	$.each(alerts,function(i,a) {
		environments.push(a.environment);
		colos.push(a.colo);
		hosts.push(a.host);
		services.push(a.service);
		statuses.push(a.status);
		tags=tags.concat(a.tags.split(','));
        o = $('<li>');
        o.addClass('data-set');
        btns = $('<div>');
        btns.addClass("btn-group");
        btns.append('<a href="#" term="environment" tag="'+a.environment+'" class="btn btn-large btn-info addSearch">'+a.environment+'</a>');
        btns.append('<a href="#" term="colo" tag="'+a.colo+'" class="btn btn-large btn-info addSearch">'+a.colo+'</a>');
        btns.append('<a href="#" term="host" tag="'+a.host+'" class="btn btn-large btn-info addSearch">'+a.host+'</a>');
        btns.append('<a href="#" term="service" tag="'+a.service+'" class="btn btn-large btn-info addSearch">'+a.service+'</a>');
        if (a.status == "OK") {
            btns.append('<a href="#" term="status" tag="'+a.status+'" class="btn btn-large btn-success addSearch">'+a.status+'</a>');
        } else if ( a.status == "Warning" ) {
            btns.append('<a href="#" term="status" tag="'+a.status+'" class="btn btn-large btn-warning addSearch">'+a.status+'</a>');
        } else if ( a.status == "Critical" ) {
            btns.append('<a href="#" term="status" tag="'+a.status+'" class="btn btn-large btn-danger addSearch">'+a.status+'</a>');
        } else {
            btns.append('<a href="#" term="status" tag="'+a.status+'" class="btn btn-large addSearch">'+a.status+'</a>');
        };
        tagBtns = $('<ul>');
        tagBtns.addClass('nav nav-pills');
        $.each(a.tags.split(','),function(i,t) {
            tagBtns.append('<li class="grey active"><a href="#" class="addSearch" term="tags" tag="'+t+'" >'+t+'</a></li>');
        });
        body = $('<p>');
        body.text(a.summary);
		d = new Date(a.createDate+"Z");		
		//console.info(a.createDate);
		output = output + '<div class="alert_date">' + new Date(a.createDate+"Z").toString() + '</div>';
		output = output + '</div>';
        o.append(btns);
        o.append('<a href="/detail?host='+a.host+'&environment='+a.environment+'&colo='+a.colo+'&service='+a.service+'" class="btn btn-large btn-primary pull-right"><i class="icon-white icon-share"></i> Go</a>');
        o.append(body);
        o.append(tagBtns);
        $(alert_div).append(o);
	});

	environments = unique(environments);
	colos = unique(colos);
	hosts = unique(hosts);
	services = unique(services);
	statuses = unique(statuses);
	tags = unique(tags);
	
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
    console.debug("printing search terms");
    $('#search_terms').html('');
    o = $("<ul>");
    $("#filter_total").text(search_terms.length);
    $("#filter_total").attr('title', search_terms.length + " filters applied");
    $.each(search_terms,function(i,s) {
        o.append('<li><a href="#" class="btn" onclick="del_search_terms(\'' + s + '\')">' + s + '</a></li>');
    }); 
    $('#search_terms').append(o);
};
