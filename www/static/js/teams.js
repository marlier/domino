var table = "team";
var id = 0;
var oncall_count = 1;
user_list = new Array();
team_list = new Array();
selected = new Array();

$(document).ready(function(){
	query("#data","#sidebar_data");

    $("#saveBtn").click(function() {
        console.debug("creating/modifying team");
        save_team();
    });

    $("#teamDetail #oncall_count").change(function() {
        update_oncall($("#teamDetail #oncall_count").val());
    });

    $(".member_tag").live('click', function() {
        $(this).parent().remove();
        update_oncall($("#teamDetail #oncall_count").val());
    });

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
            oncall_count = team.oncall_count
            console.debug(team);
            $("#teamDetail #name").val(team.name);
            $("#teamDetail #email").val(team.email);
            $("#teamDetail #phone").val(team.phone);

            $("#members").html('');
            $.each(team.members,function(i,m) {
                $("#members").append('<li><a id="'+m.id+'" class="member_tag"><i class="icon-white icon-remove"></i> '+m.name+'</a></li>');
            });

            update_oncall(team.oncall_count);
            $(".sortable").sortable({
                update: function( event, ui ) {
                    update_oncall($("#teamDetail #oncall_count").val())
                }
            });
            $(".sortable").disableSelection();


            if ( team.catchall == 0 ) {
                $('#teamDetail #catchall').prop('checked', true);
            };
            $("#teamDetail #oncall_count").val(team.oncall_count);
            $("#saveBtn").html('<a id="saveBtn" class="btn btn-mini"><i class="icon-pencil"></i> Save</a></div>')
        });
 
    });

	var url = "/api/user";
	$.getJSON(url,function(json){
        username_list = new Array();
	    username_list= [];
        user_list=json;
        $.each(json,function(i,u) {
            username_list.push(u.name);
        });
        console.debug(username_list);
        $('.typeahead').typeahead(
            {
                'source': username_list
            }
        );

    $("#addUser").keypress(function(e) {
        if (e.which == 13) {
            console.debug('adding user to list');
            console.debug(user_list);
            $.each(user_list,function(i,u) {
                if ( u.name == $("#addUser").val() ) {
                    $("#members").append('<li><a id="'+u.id+'" class="member_tag"><i class="icon-white icon-remove"></i> '+u.name+'</a></li>');
                    $("#addUser").val('');
                    $(".sortable").sortable({
                        update: function( event, ui ) {
                            update_oncall($("#teamDetail #oncall_count").val())
                        }
                    });
                    $(".sortable").disableSelection();
                    update_oncall($("#teamDetail #oncall_count").val());
                };  
            });     
        }       
    });

	});
	hideLoading();
};

function update_oncall(oncall_num) {
	console.debug("colorizing oncall members");
	console.debug(oncall_num);
	$(".sortable li").each(function(i,item){
		if ((i+1) <= oncall_num) {
            console.debug('adding class');
			$(item).addClass('ui-oncall');
		} else {
            console.debug('remove class');
			$(item).removeClass('ui-oncall');
		}
	});
	
}

function save_team() {
	showLoading();
	members = $.makeArray($(".sortable li a").map(function(){return $(this).attr('id');})).join(',');
	var name = $("input#name").val();
	var email = $("input#email").val();
	var phone = $("input#phone").val();
	var oncall_count = $("input#oncall_count").val();
	var catchall = $("input#catchall").is(':checked');
	if ( catchall == true ) {
		catchall = 0;
	} else {
		catchall = 1;
	}
	
	
	if ( validate_phone(phone) == false ) {
		alert("Invalid phone number (ex +12223334444)");
        hideLoading();
		return;
	}
	
	if ( validate_name(name) == false ) {
		alert("You must enter a name");
        hideLoading();
		return;
	}
	
	if ( members.length === 0 ) {
		alert("A team cannot be empty. Pick at least one user on a team.");
        hideLoading();
		return;
	}
	
	var jsonData = JSON.stringify({
		"name": name,
		"email": email,
		"members": members,
		"oncall_count": oncall_count,
		"catchall": catchall,
		"phone": phone
	});
    console.debug(jsonData);

    if ( id > 0 ) {
        var url = "/api/team/" + id
    } else {
        var url = "/api/team"
    };
	
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
