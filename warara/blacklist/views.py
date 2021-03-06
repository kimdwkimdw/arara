from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect

from arara_thrift.ttypes import *

import warara
from warara import warara_middleware

def get_various_info(request):
    server = warara_middleware.get_server()
    sess = test.login()
    r['num_blacklist_member'] = 0
    return r

@warara.wrap_error
def add(request):
    if request.method == 'POST':
        blacklist_id = request.POST['blacklist_id']
        server = warara_middleware.get_server()
        sess, r = warara.check_logged_in(request)
        id_converting = server.member_manager.search_user(sess, blacklist_id, "") 
        if len(id_converting) == 0:
            # XXX combacsa's DdamBbang.
            raise InvalidOperation("ID not exist!")
        converted_id =  id_converting[0].username
        try:
            server.blacklist_manager.add_blacklist(sess, converted_id, True, True) 
            message = '1'
        except InvalidOperation as e:
            message = e.why
        if request.POST.get('ajax', 0):
            return HttpResponse(message)
        return HttpResponseRedirect("/blacklist/")
    else:
        return HttpResponse('Must use POST')

@warara.wrap_error
def delete(request):
    if request.method == 'POST':
        username = request.POST['username']
        server = warara_middleware.get_server()
        sess, r = warara.check_logged_in(request)
        server.blacklist_manager.delete_blacklist(sess, username)
        return HttpResponseRedirect("/blacklist/")
    # Why not return HttpResponse('Must use POST') ? XXX combacsa

@warara.wrap_error
def update(request):
    server = warara_middleware.get_server()
    sess, r = warara.check_logged_in(request)
    blacklist = server.blacklist_manager.get_blacklist(sess)
    bl_submit_chooser = request.POST['bl_submit_chooser']
    if bl_submit_chooser == "update":
        for b in blacklist:
            article_bl_key = 'blacklist_article_%s' % b.blacklisted_user_username
            if article_bl_key in request.POST:
                b.block_article = True
            else:
                b.block_article = False
            message_bl_key = 'blacklist_message_%s' % b.blacklisted_user_username
            if message_bl_key in request.POST:
                b.block_message = True
            else:
                b.block_message = False

            server.blacklist_manager.modify_blacklist(sess, BlacklistRequest(
                blacklisted_user_username = b.blacklisted_user_username,
                block_article = b.block_article,
                block_message = b.block_message))
    if bl_submit_chooser == "delete":
        for b in blacklist:
            delete_user = request.POST.get('bl_%s_delete' % b.blacklisted_user_username, "")
            if delete_user != "":
                server.blacklist_manager.delete_blacklist(sess, delete_user)

    return HttpResponseRedirect("/blacklist/")

@warara.wrap_error
def index(request):
    server = warara_middleware.get_server()
    sess, _ = warara.check_logged_in(request)
    r = {}
    r['logged_in'] = True
    blacklist = server.blacklist_manager.get_blacklist(sess)
    r['blacklist'] = blacklist

    if 'search' in request.GET:
        search_user_info = request.GET['search']
        user_id = server.member_manager.search_user(sess, search_user_info, "")
        r['search_result'] = user_id

    rendered = render_to_string('blacklist/index.html', r)
    return HttpResponse(rendered)
