$(document).ready(function(){
    var cursor_pos = 1;
    if($("#root_article_info").length){ //if it is a read page
    $root_article_id = parseInt($("#root_article_info").attr("rel"));
    cursor_pos = parseInt($("td.id_col[rel='" + $root_article_id + "']").parent().attr("rel"));
    $root_article_pos = cursor_pos; //naming
    }
    var row_count = $("#article_table tr").length;
	if(!$logged_in){
	cursor_pos = -1;
	}

    update_table(cursor_pos);
    function update_table(cursor_pos) {
        $("#article_table tr").removeClass("row_highlight");
        $("#article_table tr").eq(cursor_pos).addClass("row_highlight");
    }
    function read_article() {
        //$.history.load(cursor_pos);
        var article_link = $("#article_table tr").eq(cursor_pos).children(".title_col").children("a").attr("href");
        location.href = article_link;
    }

    var cursor_sm = 0; //cursor search method
    var length_sm = $("#board_buttons a[name='search_method_select']").length;

    function update_search_method(cursor){
        $("#board_buttons a[name='search_method_select']").removeClass("highlight");
        $("#board_buttons a[name='search_method_select']").eq(cursor).addClass("highlight");
    }

    $("#board_buttons a[name='search_method_select']").click(function(event){
            toggle_search_method($(this));
            event.preventDefault();
            });

    function toggle_search_method($sm){
            $sm.toggleClass("selected");
            if($sm.hasClass("selected")){
            $sm.parent().children("input").attr("name", $sm.attr("rel"));
            }
            else{
            $sm.parent().children("input").removeAttr("name");
            }
            if(!$(".selected").length){
            $("#board_buttons span a[name='search_method_select']").eq(((cursor_pos-1) % 4)).addClass("selected");
            $("#board_buttons span.search_method input").eq(((cursor_pos-1) % 4)).attr("name", $("#board_buttons span a[name='search_method_select']").eq(((cursor_pos-1) % 4)).attr("rel"));
            }
    }

    $(document).keypress(function(event) {
		if($focus_input || event.altKey || event.ctrlKey){
		return;
		}
        if(!$("#list_link").attr("href")){ //move to main page when user press q in article_list page
        switch(event.which){
            case 113:
                location.href = "/main";
                break;
                }
        }
        if($("#board_buttons a.highlight").length){
            switch(event.which){
                case 115:
                    $("#board_buttons a.highlight").removeClass("highlight");
                    $(".hidden_highlight").removeClass("hidden_highlight").addClass("row_highlight");
                    $("#board_buttons input[name='search_word']").focus();
                    cursor_sm = 0;
                    break;
                case 106:
                    cursor_sm -= 1;
                    if (cursor_sm < 0){
                    cursor_sm = 0;
                    }
                    update_search_method(cursor_sm);
                    break;
                case 107:
                    cursor_sm += 1;
                    if (cursor_sm >= length_sm){
                    cursor_sm = length_sm - 1;
                    }
                    update_search_method(cursor_sm);
                    break;
                case 32:
                case 39:
                    $sm = $("#board_buttons a[name='search_method_select']").eq(cursor_sm);
                    toggle_search_method($sm);
                    event.preventDefault();
                    break;
            }
        }
        else{
            switch(event.which){
                case 115:
                    $(".highlight").removeClass("highlight");
                    $(".row_highlight").removeClass("row_highlight").addClass("hidden_highlight");
                    $("#board_buttons a[name='search_method_select']").eq(cursor_sm).addClass("highlight");
                    location.href = "#search_method_select";
                    break;
            }
        }
		if($("#article_table tr.row_highlight").length){
            switch (event.which) {
                case 13:  // enter
                case 32:  // space
                case 39:
                case 105:
                    event.preventDefault();
                    read_article();
                    break;
                case 106:  // j
                    cursor_pos += 1;
                    if (cursor_pos >= row_count) cursor_pos = row_count - 1;
                    update_table(cursor_pos);
                    break;
                case 107:  // k
                    cursor_pos -= 1;
                    if (cursor_pos < 1) cursor_pos = 1;
                    update_table(cursor_pos);
                    break;
                case 98:
                    $show_user_popup($("#article_table tr .username").eq(cursor_pos-1));
                    $focus_user_popup();
                    break;
                case 82:
                    location.href = $("#board_write a").attr("href");
                    break;
                default:
                    //alert(event.which);
            }
		}
    });
});
