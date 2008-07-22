$(document).ready(function(){
    var read_anchors = document.getElementsByName('message_read_anchor');
    for(var i=0; i<read_anchors.length; i++){
        read_anchors[i].onclick = function(){
            read_message.msg_no.value = this.value;
            read_message.submit();
        }
    }

    var page_anchors = document.getElementsByName('page_anchor');
    for(var i=0; i<page_anchors.length; i++){
        page_anchors[i].onclick = function(){
            move_list.page_no.value = this.value;
            move_list.submit();
        }
    }
    thispage = page_info.thispage.value;
    $("a[name='page_anchor']").addClass("makered");
})
