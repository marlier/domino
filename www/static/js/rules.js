var table = "team";
var id = 0;
rules_list = new Array();

$(document).ready(function(){
    getRules();
    $("#saveBtn").click(function() {
        console.debug('button clicked');
        saveRule();
    });
});

function getRules() {
    showLoading();
    var div = "#rules_rows";
    environment = $(div+' #environment').val();
    colo = $(div+' #colo').val();
    host = $(div+' #host').val();
    service = $(div+' #service').val();
    status = $(div+' #status').val();
    tag = $(div+' #tag').val();
    var url = "/api/rule?environment="+environment+"&colo="+colo+"&host="+host+"&service="+service+"&status="+status+"&tag="+tag
    $.getJSON(url,function(json){
        print_rules(json, div);
        hideLoading();
    });
};

function print_rules(rules, rules_div) {
    showLoading();
    console.debug("Printing rules to "+rules_div);
    rules_list = new Array();
    $(rules_div + ' .data-set').remove();
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
        row.append('<td class="alert-info">' + clean_value(r['status']) + '</td>');
        row.append('<td class="alert-info">' + clean_value(r['tag']) + '</td>');
        row.append('<td class="alert-success">' + clean_value(r['addTag']) + '</td>');
        row.append('<td class="alert-success">' + clean_value(r['removeTag']) + '</td>');
        row.append('<td><div class="btn-group"><a href="#" id="'+r['id']+'" title="Edit" class="tip-top editBtn btn btn-info btn-small"><i class="icon-white icon-pencil"></i></a><a href="#" id="'+r['id']+'" title="Delete" class="tip-top delBtn btn btn-danger btn-small"><i class="icon-white icon-remove-sign"></i></a></div></td>');
        $(rules_div).append(row);
    });
    
    $("a#saveBtn").html('<i class="icon-white icon-certificate"></i> Save');
    id = 0;
    
    $(rules_div + ' input').change(function() {
        getRules();
    });

    $(rules_div + ' .editBtn').click(function() {
        id = $(this).attr('id');
        $("a#saveBtn").html('<i class="icon-white icon-pencil"></i> Overwrite');
        var url = "/api/rule/" + id; 
        $.getJSON(url,function(json){
            if (process_header(json.status, json.status_message)) {
                r = json.data[0];
                console.debug(r);
                $(rules_div+' #environment').val(r['environment']);
                $(rules_div+' #colo').val(r['colo']);
                $(rules_div+' #host').val(r['host']);
                $(rules_div+' #service').val(r['service']);
                $(rules_div+' #status').val(r['status']);
                $(rules_div+' #tag').val(r['tag']);
                $(rules_div+' #addtag').val(r['addTag']);
                $(rules_div+' #removetag').val(r['removeTag']);
                getRules();
            };
        });
        
    });

    $(rules_div + ' .delBtn').click(function() {
        delRule($(this).attr('id'));
        getRules();
    });
    hideLoading();
};

function delRule(id) {
    var r=confirm("Are you sure you want to delete this rule?");
    if (r==true) {
        showLoading();
        //delete a rule
        $.ajax({
            url: "/api/rule/" + id,
            type: "DELETE"
        }).done(function(json){
            hideLoading();
            getRules();
        }); 
    };
};

function saveRule() {
    console.debug('saving rule');
    showLoading('saving rule');
    var div = "#rules_rows";

    $('input').blur();

    var jsonData = JSON.stringify({
        "environment": $(div+' #environment').val(),
        "colo": $(div+' #colo').val(),
        "host": $(div+' #host').val(),
        "service": $(div+' #service').val(),
        "status": $(div+' #status').val(),
        "tag": $(div+' #tag').val(),
        "addTag": $(div+' #addtag').val(),
        "removeTag": $(div+' #removetag').val()
    });

    if ( id > 0 ) {
        var url = "/api/rule/" + id
    } else {
        var url = "/api/rule"
    };
    console.debug(url);
    console.debug(jsonData);
    $.ajax({
        type: 'POST',
        contentType: 'application/json',
        url: url,
        dataType: "json",
        data: jsonData,
        success: function(data, textStatus, jqXHR){
            hideLoading();
            getRules();
        },      
        error: function(jqXHR, textStatus, errorThrown){
            console.debug(textStatus);
            hideLoading();
        }       
    });    
};

function clean_value(val) {
    if ( val == "None" || val == null || val == '' ) {
        return '-';
    } else {
        return val;
    };
}
