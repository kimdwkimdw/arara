from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect

from arara_thrift.ttypes import *

import arara
import warara

def register(request):
    sess, r = warara.check_logged_in(request)
    server = arara.get_server()
    if r['logged_in'] == True:
        assert None, "ALEADY_LOGGED_IN"

    if request.method == 'POST':
        username = request.POST['id']
        password = request.POST['password']
        nickname = request.POST['nickname']
        email = request.POST['email']
        signature = request.POST['sig']
        introduction = request.POST['introduce']
        language = request.POST['language']
        user_information_dict = {'username':username, 'password':password, 'nickname':nickname, 'email':email, 'signature':signature, 'self_introduction':introduction, 'default_language':language}
        message = server.member_manager.register(UserRegistration(**user_information_dict))
        return HttpResponseRedirect("/main/")
    
    rendered = render_to_string('account/register.html', r)
    return HttpResponse(rendered)

def confirm_user(request, username, confirm_key):
    server = arara.get_server()

    mes = server.member_manager.confirm(username, confirm_key)
    return HttpResponse(mes)

def reconfirm_user(request, username):
    rendered = render_to_string('account/mail_confirm.html',
            {'username': username})
    return HttpResponse(rendered)

def agreement(request):
    sess, r = warara.check_logged_in(request)
    if r['logged_in'] == True:
        assert None, "ALREADY_LOGGED_IN"
    else:
        rendered = render_to_string('account/register_agreement.html')

    return HttpResponse(rendered)

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        current_page = request.POST.get('current_page_url', 0)
        client_ip = request.META['REMOTE_ADDR']
        server = arara.get_server()

        try:
            session_key = server.login_manager.login(username, password, client_ip)
        except InvalidOperation, e:
            if request.POST.get('precheck', 0):
                return HttpResponse(e)
            else:
                #XXX: (pipoket) Ugly hack for showing nickname while not logged in.
                print e.why
                splited = e.why.splitlines()
                if splited[0] == 'not activated':
                    username = splited[1]
                    nickname = splited[2]
                    rendered = render_to_string('account/mail_confirm.html', {
                        'username': username, 'nickname': nickname})
                    return HttpResponse(rendered)
                else:
                    return HttpResponse('<script>alert("Login failed!"); history.back()</script>');

        if request.POST.get('precheck', 0):
            return HttpResponse("OK")

        User_Info = server.member_manager.get_info(session_key)
        if User_Info.default_language == "kor":
            request.session["django_language"] = "ko"
        elif User_Info.default_language == "eng":
            request.session["django_language"] = "en"
        request.session["arara_session_key"] = session_key
        request.session["arara_username"] = username

        if current_page.find('register')+1:
            return HttpResponseRedirect('/main')
        return HttpResponseRedirect(current_page)

    return HttpResponseRedirect('/')

def logout(request):
    if request.session.get('arara_session_key', 0):
        del request.session['arara_session_key']
        del request.session['arara_username']
        return HttpResponseRedirect("/")
    session_key, r = warara.check_logged_in(request)
    if r['logged_in'] == True:
        server = arara.get_server()
        account = server.login_manager.logout(session_key)
        del request.session['arara_session_key']
        del request.session['arara_username']
        request.session.clear()
        return HttpResponseRedirect(current_page)
    else:
        if request.session.get('arara_session_key', 0):
            del request.session['arara_session_key']
            del request.session['arara_username']
        assert None, "NOT_LOGGED_IN"

def account(request):
    session_key, r = warara.check_logged_in(request)
    if r['logged_in'] == True:
        server = arara.get_server()
        account = server.member_manager.get_info(session_key)

        account.logged_in = True
        rendered = render_to_string('account/myaccount_frame.html', account.__dict__)
    else:
        assert None, "NOT_LOGGED_IN"
    return HttpResponse(rendered)

def account_modify(request):
    session_key, r = warara.check_logged_in(request)
    if r['logged_in'] == True:
        server = arara.get_server()
        account = server.member_manager.get_info(session_key)
        if request.method == 'POST':
            nickname = request.POST['mynickname']
            signature = request.POST['mysig']
            introduction = request.POST['myintroduce']
            language = request.POST['mylanguage']
            modified_information_dic = {'nickname': nickname, 'signature': signature, 'self_introduction': introduction, 'default_language': language, 'widget': 0, 'layout': 0}
            server.member_manager.modify(session_key, UserModification(**modified_information_dic))
            if language == "kor":
                request.session["django_language"] = "ko"
            elif language == "eng":
                request.session["django_language"] = "en"
            return HttpResponseRedirect("/account/")
        else:
            account.logged_in = True
            rendered = render_to_string('account/myaccount_modify.html', account.__dict__)
            return HttpResponse(rendered)
    else:
        assert None, "NOT_LOGGED_IN"
        return HttpResponse(rendered)

def password_modify(request):
    session_key, r = warara.check_logged_in(request)
    if r['logged_in'] == True:
        server = arara.get_server()
        if request.method == 'POST':
            username = request.session['arara_username']
            last_password = request.POST['last_password']
            password = request.POST['password']
            user_information_dic = {'username':username, 'current_password':last_password, 'new_password':password}
            server.member_manager.modify_password(session_key, UserPasswordInfo(**user_information_dic))
            return HttpResponseRedirect("/account/")
        else:
            rendered = render_to_string('account/myacc_pw_modify.html', r)
            return HttpResponse(rendered)

    else:
        assert None, "NOT_LOGGED_IN"

def account_remove(request):
    session_key, r = warara.check_logged_in(request)
    if r['logged_in'] == True:
        server = arara.get_server()
        if request.method == 'POST':
            server.member_manager.remove_user(session_key)
            return HttpResponseRedirect("/")
        else:
            account = server.member_manager.get_info(session_key)
            account.logged_in = True
            rendered = render_to_string('account/myaccount_remove.html', account.__dict__)
            return HttpResponse(rendered)
    else:
        assert None, "NOT_LOGGED_IN"
        return HttpResponse(rendered)

def wrap_error(f):
    def check_error(*args, **argv):
        r = {} #render item
        try:
            return f(*args, **argv)
        except StandardError, e:
            if e.message == "NOT_LOGGED_IN":
                r['error_message'] = e.message
                rendered = render_to_string("error.html", r)
                return HttpResponse(rendered)
            elif e.message == "arara_session_key":
                r['error_message'] = "NOT_LOGGED_IN"
                rendered = render_to_string("error.html", r)
                return HttpResponse(rendered)
            else:
                r['error_message'] = e.message
                rendered = render_to_string("error.html", r)
                return HttpResponse(rendered)

    return check_error

#login = wrap_error(login)
#logout = wrap_error(logout)
#account = wrap_error(account)
#register = wrap_error(register)
#agreement = wrap_error(agreement)
#confirm_user = wrap_error(confirm_user)
#account_modify = wrap_error(account_modify)
#account_remove = wrap_error(account_remove)
#password_modify = wrap_error(password_modify)

def id_check(request):
    if request.method == 'POST':
        server = arara.get_server()
        r = {}
        check_id_field = request.POST['check_field']
        ret = server.member_manager.is_registered(check_id_field)
        if(request.POST.get('from_message_send', 0)):
            if ret:
                return HttpResponse(1)
            else:
                return HttpResponse(0)
        if ret:
            r = 1
        else:
            r = 0
        return HttpResponse(r)
    else:
        return HttpResponse('Must use POST')

def nickname_check(request):
    if request.method == 'POST':
        server = arara.get_server()
        r = {}
        check_nickname_field = request.POST['check_field']
        ret = server.member_manager.is_registered_nickname(check_nickname_field)

        if(request.POST.get('from_message_send', 0)): #check from message send or nickname modify
            if ret:
                return HttpResponse(1)
            else:
                return HttpResponse(0)

        if ret:
            r = 1
        else:
            r = 0
        return HttpResponse(r)
    else:
        return HttpResponse('Must use POST')

def email_check(request):
    if request.method == 'POST':
        server = arara.get_server()
        r = {}
        check_email_field = request.POST['check_email_field']
        ret = server.member_manager.is_registered_email(check_email_field)
        if ret:
            r = 1
        else:
            r = 0
        return HttpResponse(r)
    else:
        return HttpResponse('Must use POST')

def mail_resend(request):
    rendered = render_to_string('account/mail_confirm.html')
    return HttpResponse(rendered)
