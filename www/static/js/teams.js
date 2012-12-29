var table = "team";
var id = 0;
user_list = new Array();
team_list = new Array();
selected = new Array();

$(document).ready(function(){
	query("#data","#sidebar_data");
});

function print_teams(teams,team_div,sidebar_div) {
    showLoading();
	console.debug("Printing teams");

	team_list = new Array();

    $(sidebar_div + ' .data-set').remove();
    $.each(teams,function(i,t) {
        team_list.push(t);
        $(sidebar_div).append('<li class="data-set"><a class="team_name" href="#" id="'+t.id+'">'+t.name+'</a></li>');
    });

    $(".team_name").click(function() {
        id = $(this).attr('id');
       
        var url = "/api/team/" + id;
        $.getJSON(url,function(json){
            team=json[0];
            console.debug(team);
            $("#teamDetail #name").val(team.name);
            $("#teamDetail #email").val(team.email);
            $("#teamDetail #phone").val(team.phone);
            $("#members").html('');
            $.each(user_list,function(i,u) {
                console.debug(u.name);
                $.each(team.members,function(z,m) {
                    console.debug(m);
                    if ( u.name == m.name ) {
                        $("select#members").append('<option selected>'+u.name+'</option>');
                    } else {
                        $("select#members").append('<option>'+u.name+'</option>');
                    };
                });
            });
            $('select').select2();
            if ( team.catchall == 0 ) {
                $('#teamDetail #catchall').prop('checked', true);
            };
            $("#teamDetail #oncall_count").val(team.oncall_count);
            $("#saveBtn").html('<a onclick="saveTeam();" id="saveBtn" class="btn btn-mini"><i class="icon-pencil"></i> Save</a></div>')
        });
 
    });

	var url = "/api/user";
	$.getJSON(url,function(json){
        user_list = new Array();
	    user_list=json;
        $.each(user_list,function(i,u) {
            $("select#members").append('<option>'+u.name+'</option>');
        });
        $('select').select2();
	});
	hideLoading();
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

function save_team(id) {
	showLoading();
	// gather info from tabs
	var members = new Array();
	var members = $( "#sortable" ).sortable("toArray");
		
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
	
	if ( members.length === 0 ) {
		alert("A team cannot be empty. Pick at least one user on a team.");
		return;
	}
	
	var jsonData = JSON.stringify({
		"name": name,
		"email": email,
		"members": members.join(','),
		"oncall_count": oncall_count,
		"catchall": catchall,
		"phone": phone
	});
	
	var url = base_url+"team/" + id
	
	$.ajax({
        type: 'POST',
        contentType: 'application/json',
        url: url,
        dataType: "json",
        data: jsonData,
        success: function(data, textStatus, jqXHR){
            hideLoading();
			query("#data","#sidebar_data");
        },
        error: function(jqXHR, textStatus, errorThrown){
            hideLoading();
            alert('Update team error: ' + textStatus);
        }
    });

};

function delete_team(id) {
	var r=confirm("Are you sure you want to delete this team?");
	if (r==true) {
        showLoading();
  		//delete a team
		console.debug("deleting team");
		var url = base_url+"team/" + id;
		$.ajax({
			url: url,
			type: "DELETE"
		}).done(function(json){
            hideLoading();
			query("#data","#sidebar_data");
		});
	};
};
