var table = "user";
var id = 0;
var user_list = new Array();

$(document).ready(function(){
	query("#data","#sidebar_data");

    $("#register").click(function() {
        console.debug('register phone');
        var url = "/api/user/"+id+"/phone/register"
        showLoading();
        $.ajax({
            type: 'POST',
            contentType: 'application/json',
            url: url,
            dataType: "json",
            data: {},
            success: function(data, textStatus, jqXHR){
                hideLoading();
                alert("Your verification code is "+data['verification_code']);
            },  
            error: function(jqXHR, textStatus, errorThrown){
                hideLoading();
                alert("Failed to register your phone")
            }   
        });         
    });

    $("#test").click(function() {
        console.debug('testing phone');

        var url = "/api/user/"+id+"/phone/smstest"
        showLoading();
        $.ajax({
            type: 'POST',
            contentType: 'application/json',
            url: url,
            dataType: "json",
            data: {},
            success: function(data, textStatus, jqXHR){
                hideLoading();
                alert("Test SMS message sent, hopefully you'll get it in a second.");
            },
            error: function(jqXHR, textStatus, errorThrown){
                hideLoading();
                alert("Failed to send test SMS message")
            } 
        });
    });

    $("#createBtn").click(function() {
        console.debug('creating/modifying user');
        saveUser();
    });

});

function print_users(users,user_div,sidebar_div) {
    showLoading('print users');
	console.debug("Printing users");
	var output = '';
	user_list = new Array();

    $(sidebar_div + ' .data-set').remove();
    $.each(users,function(i,u) {
        user_list.push(u);
        $(sidebar_div).append('<li class="data-set"><a class="user_name" href="#" id="'+u.id+'">'+u.name+'</a></li>');
    }); 
    hideLoading('print users');	
    $(".user_name").click(function() {
        id = $(this).attr('id');

        var url = "/api/user/" + id; 
        $.getJSON(url,function(json){
            user=json[0];
            $("#teamDetail #name").val(user.name);
            $("#teamDetail #email").val(user.email);
            $("#teamDetail #phone").val(user.phone);
            $("#saveBtn").html('<a id="saveBtn" class="btn btn-mini"><i class="icon-pencil"></i> Save</a></div>')
	    $("#saveBtn").click(function() {
        	console.debug('creating/modifying user');
	        saveUser(user.id);
	    });
        });        
    });

};

function delUser(id) {
    var r=confirm("Are you sure you want to delete this user?");
    if (r==true) {
        showLoading();
        //delete a user
        console.debug("deleting user");
        var url = "/api/user/" + id; 
        $.ajax({
            url: url,
            type: "DELETE"
        }).done(function(json){
            hideLoading();
            query("#data","#sidebar_data");
        }); 
    };  
};

function saveUser(id) {
	if ( validate_email($("input#email").val()) == false ) { 
		alert("Invalid email address")
		return
	}
	
	if ( validate_phone($("input#phone").val()) == false ) {
		alert("Invalid phone number (ex +12223334444)")
		return
	}
	
	if ( validate_name($("input#name").val()) == false ) {
		alert("You must enter a name")
		return
	}
	
	var jsonData = JSON.stringify({
		"name": $("input#name").val(),
		"email": $("input#email").val(),
		"phone": $("input#phone").val()
	});
	
    if (id > 0) {
   	    var url = "/api/user/" + id
    } else {
        var url = "/api/user"
    };
	showLoading();
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
        }
    });
};

