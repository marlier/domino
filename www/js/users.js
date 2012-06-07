var table = "users";
var id = 0;
var user_list = new Array();

$(document).ready(function(){
	query("#data","#sidebar_data");
});

$(document).bind('cbox_closed', function(){
    query("#data","#sidebar_data");
});

function print_users(users,user_div,sidebar_div) {
	console.debug("Printing users");
	console.debug(users);
	var output = '';
	user_list = new Array();
	
	output = output + '<div class="users">';
	output = output + '<ul id="user_card">';
	$.each(users,function(i,u) {
		//teams.push(u.team.split(","));
		user_list.push(u);
		output = output + '<div class="user_item">';
		output = output + '<span id="user_edit_button" onclick="print_useredit(' + u.id + ')">edit</span>';
		output = output + '<span id="user_delete_button" onclick="delete_user(' + u.id + ')">delete</span>';
		output = output + '<li id="user_card">';
		output = output + '<ul class="user_attributes">';
		output = output + '<li class="name">' + u.name + '</li></br>';
		output = output + '<li>Email: ' + u.email + '</li></br>';
		output = output + '<li>Phone: ' + u.phone + '</li></br>';
		var teams = new Array();
		$.each(u.teams,function(i,t) {
			teams.push(t.name)
		});
		output = output + '<li>Team(s): ' + teams.join(',') + '</li></br>';
		output = output + '</ul>';
		output = output + '</li>';
		output = output + '</div>';
		
	});
	output = output + '</ul>';
	output = output + '</div>';
	$(user_div).html(output);
	
	//teams = $.unique(teams).sort();
	
	var output = '';
	output = output + '<ul>';
	output = output + '<li onclick="print_useredit(0)">Create New User</li>';
	//output = output + '<li><div id="teams_toggle"><img src="images/disclosureTriangle.png" alt="Teams"/> Teams</div></li>';
	//output = output + '<ul id="teams_data" class="filter_data">';
	//$.each($.unique(teams).sort(),function(i,x) {
	//	output = output + '<li onclick="add_search_terms(\'team:' + x + '\')">' + x + '</li>'
	//});
	output = output + '</ul>';
	output = output + '</ul>';
	$(sidebar_div).html(output);
	
	//$('ul#teams_data').hide();
	
	//$('#teams_toggle').click(function(){
    // 	$('ul#teams_data').toggle('medium');
	//});
	
};

function print_useredit(i) {
	if (i > 0) {
		$.each(user_list, function(x,u) {
			if ( i === u.id ) {
				user = u
			}
		});
		var output = '';
		output = output + '<div id="user_edit">';
		output = output + 'Name: <input id="user_name" value="' + user.name + '"></input><br />';
		output = output + 'Email: <input id="user_email" value="' + user.email + '"></input><br />';
		output = output + 'Phone: <input id="user_phone" value="' + user.phone + '"></input>(ex +12223334444)<br />';
		output = output + '</br>';
		output = output + '<button type="button" id="save_user" onclick="save_user(' + user.id + ')">Save</button>';
		output = output + '</div>';
		$.colorbox({html:output, title:user.name, height:"200px", width:"300px"});
	} else {
		var output = '';
		output = output + '<div id="user_edit">';
		output = output + 'Name: <input id="user_name"></input><br />';
		output = output + 'Email: <input id="user_email"></input><br />';
		output = output + 'Phone: <input id="user_phone"></input>(ex +12223334444)<br />';
		output = output + '</br>';
		output = output + '<button type="button" id="save_user" onclick="save_user(0)">Save</button>';
		output = output + '</div>';
		$.colorbox({html:output, title:"New User", height:"200px", width:"300px"});
	};
	
	
};

function save_user(id) {
	if ( validate_email($("input#user_email").val()) == false ) { 
		alert("Invalid email address")
		return
	}
	
	if ( validate_phone($("input#user_phone").val()) == false ) {
		alert("Invalid phone number (ex +12223334444)")
		return
	}
	
	if ( validate_name($("input#user_name").val()) == false ) {
		alert("You must enter a name")
		return
	}
	
	if (id === 0) {
		//creat a new team
		console.debug("creating new user");
		var mode = "create";
	} else {
		//edit a team
		console.debug("saving edits to user");
		var mode = "edit";
	};
	
	var url = base_url+mode+"?target=user&id=" + id + "&name="+ $("input#user_name").val() + "&email=" + $("input#user_email").val() + "&phone=" + $("input#user_phone").val();
	url = url.replace(/\+/g, "%2B");
	$.getJSON(url,function(json){
		if (process_header(json.status, json.status_message)) {
			// done saving
			console.log(json.status);
			console.log(json.status_message);
			alert("Validation Code: "+json.status_message)
			$.colorbox.close();
		};
	});
};

function delete_user(id) {
	var r=confirm("Are you sure you want to delete this user?");
	if (r==true) {
  		//delete a user
		console.debug("deleting user");
		var url = base_url+"delete?target=user&id=" + id;
		$.getJSON(url,function(json){
			if (process_header(json.status, json.status_message)) {
				query("#data","#sidebar_data");
			};
		});
	};
};