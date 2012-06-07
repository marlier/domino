var table = "teams";
var id = 0;
user_list = new Array();
team_list = new Array();
selected = new Array();

$(document).ready(function(){
	query("#data","#sidebar_data");
});

function print_teams(teams,team_div,sidebar_div) {
	console.debug("Printing teams");

	team_list = new Array();

	var output = '';
	output = output + '<div class="teams">';
	output = output + '<ul>';
	output = output + '<li onclick="print_teamedit(0)">Create New Team</li>';
	$.each(teams,function(i,t) {
		team_list.push(t);
		output = output + '<li class="name" onclick="print_teamedit(' + t.id + ')">' + t.name + '</li>';
	});
	output = output + '</ul>';
	output = output + '</div>';
	$(sidebar_div).html(output);
	
	var url = base_url+"query?target=users";
	$.getJSON(url,function(json){
		if (process_header(json.status, json.status_message)) {
			user_list=json.data;
		};
	});
	
};

function update_oncall(oncall_num) {
	console.debug("Printing oncall members");
	console.debug(oncall_num);
	$("#sortable li").each(function(i,item){
		if ((i+1) <= oncall_num) {
			$(item).addClass('ui-oncall');
		} else {
			$(item).removeClass('ui-oncall');
		}
	});
	
}

function print_teamedit(id) {
	console.debug(id);
	var output = '';
	output = output + '<div id="tabs">\
	<ul>\
	<li><a href="#tabs-1">General</a></li>\
	<li><a href="#tabs-2">Members</a></li>\
	<li><a href="#tabs-3">On Call</a></li>\
	</ul>';
	if (id > 0) {
		$.each(team_list, function(x,t) {
			if ( id === t.id ) {
				team = t
			}
		});
		console.debug(team)
		
		//output = output + '<div id="team_edit">';
		output = output + '<div id="tabs-1">\
		<p>Name: <input id="team_name" value="'+team.name+'"></input><br />\
		Email: <input id="team_email" value="'+team.email+'"></input></p><br />\
		<span title="This team is the catchall for orphaned alerts.">Catchall<input type="checkbox" id="catchall"></input></span><br />\
		Phone Number: <input id="team_phone" value="'+team.phone+'"></input><span class="note">(ex +12223334444)</span><br />\
		</div>';
		
		output = output + '<div id="tabs-2">\
		<h3>Members</h3>';
		
		output = output + '<ol id="selectable">';
		team_members_id = new Array();
		$.each(team.members,function(i,t) {
			team_members_id.push(t.id);
		});
		
		$.each(user_list,function(i,u) {
			if ( $.inArray(u.id, team_members_id) > -1 ) {
				output = output + '<li id=' + u.id + ' class="ui-selected">' + u.name + '</li>';
			} else {
				output = output + '<li id=' + u.id + '>' + u.name + '</li>';
			}
		});
		output = output + '</ol>\
		<span class="note">To select multiple users, control click (or command click for Mac users)</span>\
		</div>';
		
		output = output + '<div id="tabs-3"><h3>On Call</h3>\
		Oncall Count: <input id="oncall_count" value="'+team.oncall_count+'"></input><span class="note">(integers only)</span><br />';
		if (team.members.length === 0) {		
			output = output + '<div id="tabs-3"><h3>On Call</h3>\
			<br />No team members</div>';
		} else {
			output = output + '<ul id="sortable">';
			$.each(team.members,function(i,t) {
				$.each(user_list, function(x,u) {
					if ( t.id == u.id ) {
						output = output + '<li id=' + u.id + '>' + u.name + '</li>';
					}
				});
			});
			output = output + '</ul>';
		}
		output = output + '</div>';
	
		//end of tabs
		output = output + '</div>';
		
		output = output + '<button type="button" id="save_team" onclick="save_team('+ team.id +')">Save All</button>';
		output = output + '<button type="button" id="delete_team" onclick="delete_team('+ team.id +')">Delete Team</button>';
		//output = output + '</div>';
		$("#data").html(output);
		update_oncall(team.oncall_count);
		//$.colorbox({html:output, title:"New Team", height:"600px", width:"800px"});
		if ( team.catchall === 0 ) {
			$("#catchall").prop("checked", true);	
		} else {
			$("#catchall").prop("checked", false);
		}
		
	} else {
	
		//output = output + '<div id="team_edit">';
		output = output + '<div id="tabs-1">\
		<p>Name: <input id="team_name"></input><br />\
		Email: <input id="team_email"></input></p><br />\
		<span title="This team is the catchall for orphaned alerts.">Catchall<input type="checkbox" value="false" id="catchall"></input></span><br />\
		Phone Number: <input id="team_phone"></input><span class="note">(ex +12223334444)</span><br />\
		</div>';
		
		output = output + '<div id="tabs-2">\
		<h3>Members</h3>';
		
		output = output + '<ol id="selectable">';
		$.each(user_list,function(i,u) {
			output = output + '<li id=' + u.id + '>' + u.name + '</li>';
		});
		output = output + '</ol>\
		<span class="note">To select multiple users, control click (or command click for Mac users)</span>\
		</div>';

		output = output + '<div id="tabs-3"><h3>On Call</h3>\
		<br />No team members</div>';

		//end of tabs
		output = output + '</div>';
		
		output = output + '<button type="button" id="save_team" onclick="save_team(0)">Save All</button>';
		//output = output + '</div>';
		$("#data").html(output);
		//$.colorbox({html:output, title:"New Team", height:"600px", width:"800px"});
	};

	$('#oncall_count').keyup(function () { 
    	this.value = this.value.replace(/[^0-9]/g,'');
    	if ( this.value == "" ) {
	    	this.value = 1
    	}
    	update_oncall(this.value);
    });

	$( "#tabs" ).tabs();
	$( "#sortable" ).sortable({
		update: function() {
			update_oncall($("input#oncall_count").val());
		}
	});
	$( "#sortable" ).disableSelection();
	$( "#selectable" ).selectable({
		stop: function() {
			var members = new Array();
			var members_names = new Array();
			$( ".ui-selected", this ).each(function() {
				var id = $( this ).attr('id');
				var name = $( this ).text();
				members.push(id);
				members_names.push(name); 
			});
			
			var output = '';
			output = output + '<h3>On Call</h3>\
			Oncall Count: <input id="oncall_count" value="'+$("input#oncall_count").val()+'"></input><span class="note">(integers only)</span><br />';
			
			output = output + '<ul id="sortable">';			
			$.each(members_names,function(i,u) {
				output = output + '<li id=' + members[i] + '>' + members_names[i] + '</li>';
			});
			output = output + '</ul>';
			$('#tabs-3').html(output);
			$( "#sortable" ).sortable();
			$( "#sortable" ).sortable('refresh');
			update_oncall($("input#oncall_count").val());
		}
	});
};

function save_team(id) {
	
	// gather info from tabs
	var members = new Array();
	var members = $( "#sortable" ).sortable("toArray");
	//console.debug("Sorted Members: "+members);
		
	var name = $("input#team_name").val();
	var email = $("input#team_email").val();
	var phone = $("input#team_phone").val();
	var oncall_count = $("input#oncall_count").val();
	//var oncall = members.splice(0,oncall_count);
	//console.debug("Oncall: " +oncall)
	var catchall = $("input#catchall").is(':checked');
	if ( catchall == true ) {
		catchall = 0;
	} else {
		catchall = 1;
	}
	
	
	if ( validate_email(email) == false ) { 
		alert("Invalid email address");
		return;
	}
	
	if ( validate_phone(phone) == false ) {
		alert("Invalid phone number (ex +12223334444)");
		return;
	}
	
	if ( validate_name(name) == false ) {
		alert("You must enter a name");
		return;
	}
	
	
	if (id === 0) {
		//creat a new team
		console.debug("creating new team");
		var mode = "create";
	} else {
		//edit a team
		console.debug("saving edits to team");
		var mode = "edit";
	};
	
	var url = base_url+mode+"?target=team&id="+id+"&name="+ name + "&email=" + email + "&members=" + members.join(',') + "&oncall_count=" + oncall_count + "&catchall=" + catchall + "&phone=" + phone;
	url = url.replace(/\+/g, "%2B");
	
	console.debug(url);
	$.getJSON(url,function(json){
		if (process_header(json.status, json.status_message)) {
			query("#data","#sidebar_data");
			//$.colorbox.close("Team edited succesfully");
		};
	});

};

function delete_team(id) {
	var r=confirm("Are you sure you want to delete this team?");
	if (r==true) {
  		//delete a user
		console.debug("deleting team");
		var url = base_url+"delete?target=team&id=" + id;
		$.getJSON(url,function(json){
			if (process_header(json.status, json.status_message)) {
				query("#data","#sidebar_data");
				//$.colorbox.close("Team deleted succesfully");
			};
		});
	};
};