var table = "alert";

$(document).ready(function(){
	query("#data","#sidebar_data");
	
	$("#search_input").keyup(function(event){
    	if(event.keyCode == 13){
			//console.debug($("#search_input").val());
        	add_search_terms($("#search_input").val());
    	}
	});
});

function print_alerts(alerts,alert_div,sidebar_div) {
	console.debug("Printing alerts");
	var output = '';
	var teams = new Array();
	var environments = new Array();
	var colos = new Array();
	var hosts = new Array();
	var services = new Array();
	var statuses = new Array();
	var tags = new Array();
	
	$.each(alerts,function(i,a) {
		//console.debug(a);
		teams.push(a.teams[0].name);
		environments.push(a.environment);
		colos.push(a.colo);
		hosts.push(a.host);
		services.push(a.service);
		statuses.push(a.status);
		tags=tags.concat(a.tags.split(','));
		output = output + '<div class="alert">';
		output = output + '<ul>';
		output = output + '<li onclick="add_search_terms(\'teams:' + a.teams[0].name + '\')">' + a.teams[0].name + '</li>';
		output = output + '<li onclick="add_search_terms(\'environment:' + a.environment + '\',\'alerts\')">' + a.environment + '</li>';
		output = output + '<li onclick="add_search_terms(\'colo:' + a.colo + '\')">' + a.colo + '</li>';
		output = output + '<li onclick="add_search_terms(\'host:' + a.host + '\')">' + a.host + '</li>';
		output = output + '<li onclick="add_search_terms(\'service:' + a.service + '\')">' + a.service + '</li>';
		output = output + '<li onclick="add_search_terms(\'status:' + a.status + '\')">' + a.status + '</li>';
		output = output + '<li><a href="./detail?host='+a.host+'&environment='+a.environment+'&colo='+a.colo+'&service='+a.service+'">View</a></li>';
		output = output + '</ul>';
		output = output + '<div class="alert_body" id="'+ a.status +'">' + a.summary;
		d = new Date(a.createDate+"Z");		
		//console.info(a.createDate);
		output = output + '<div class="alert_date">' + new Date(a.createDate+"Z").toString() + '</div>';
		output = output + '</div>';
	});
	
	$(alert_div).html(output);
	
	teams = unique(teams);
	environments = unique(environments);
	colos = unique(colos);
	hosts = unique(hosts);
	services = unique(services);
	statuses = unique(statuses);
	tags = unique(tags);
	
	output = '';
	output = output + '<ul>';
	output = output + '<li><div id="teams_toggle"><img src="static/img/disclosureTriangle.png" alt="Teams"/> Teams</div></li>';
	output = output + '<ul id="teams_data" class="filter_data">';
	$.each(teams,function(i,x) {
		output = output + '<li onclick="add_search_terms(\'teams:' + x + '\')">' + x + '</li>'
	});
	output = output + '</ul>';
	output = output + '<li><div id="environments_toggle"><img src="static/img/disclosureTriangle.png" alt="Environments"/> Environments</div></li>';
	output = output + '<ul id="environments_data" class="filter_data"">';
	$.each(environments,function(i,x) {
		output = output + '<li onclick="add_search_terms(\'environment:' + x + '\')">' + x + '</li>'
	});
	output = output + '</ul>';
	output = output + '<li><div id="colos_toggle"><img src="static/img/disclosureTriangle.png" alt="Colos"/> Colos</div></li>';
	output = output + '<ul id="colos_data" class="filter_data"">';
	$.each(colos,function(i,x) {
		output = output + '<li onclick="add_search_terms(\'colo:' + x + '\')">' + x + '</li>'
	});
	output = output + '</ul>';
	output = output + '<li><div id="hosts_toggle"><img src="static/img/disclosureTriangle.png" alt="Hosts"/> Hosts</div></li>';
	output = output + '<ul id="hosts_data" class="filter_data"">';
	$.each(hosts,function(i,x) {
		output = output + '<li onclick="add_search_terms(\'host:' + x + '\')">' + x + '</li>'
	});
	output = output + '</ul>';
	output = output + '<li><div id="services_toggle"><img src="static/img/disclosureTriangle.png" alt="Services"/> Services</div></li>';
	output = output + '<ul id="services_data" class="filter_data"">';
	$.each(services,function(i,x) {
		output = output + '<li onclick="add_search_terms(\'service:' + x + '\')">' + x + '</li>'
	});
	output = output + '</ul>';
	output = output + '<li><div id="statuses_toggle"><img src="static/img/disclosureTriangle.png" alt="Statuses"/> Statuses</div></li>';
	output = output + '<ul id="statuses_data" class="filter_data"">';
	$.each(statuses,function(i,x) {
		output = output + '<li onclick="add_search_terms(\'status:' + x + '\')">' + x + '</li>'
	});
	output = output + '</ul>';
	output = output + '<li><div id="tags_toggle"><img src="static/img/disclosureTriangle.png" alt="Tags"/> Tags</div></li>';
	output = output + '<ul id="tags_data" class="filter_data"">';
	$.each(tags,function(i,x) {
		output = output + '<li onclick="add_search_terms(\'tags:' + x + '\')">' + x + '</li>'
	});
	output = output + '</ul>';
	output = output + '</ul>';
	$(sidebar_div).html(output);
	
	$('ul#teams_data').hide();
	$('ul#environments_data').hide();
	$('ul#colos_data').hide();
	$('ul#hosts_data').hide();
	$('ul#services_data').hide();
	$('ul#statuses_data').hide();
	$('ul#tags_data').hide();
	
	$('#teams_toggle').click(function(){
     	$('ul#teams_data').toggle('medium');
	});
	$('#environments_toggle').click(function(){
     	$('ul#environments_data').toggle('medium');
	});
	$('#colos_toggle').click(function(){
     	$('ul#colos_data').toggle('medium');
	});
	$('#hosts_toggle').click(function(){
     	$('ul#hosts_data').toggle('medium');
	});
	$('#services_toggle').click(function(){
     	$('ul#services_data').toggle('medium');
	});
	$('#statuses_toggle').click(function(){
     	$('ul#statuses_data').toggle('medium');
	});
	$('#tags_toggle').click(function(){
     	$('ul#tags_data').toggle('medium');
	});
};
