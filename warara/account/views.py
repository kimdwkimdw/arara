from django.template.loader import render_to_string
from django.http import HttpResponse, HttpResponseRedirect
from django.core.mail import EmailMultiAlternatives
from email.MIMEText import MIMEText

import smtplib
import arara
import warara

def register(request):
    sess, r = warara.check_logged_in(request)
    server = arara.get_server()
    if r['logged_in'] == True:
        rendered = render_to_string('already_logged_in.html', r)
        return HttpResponse(rendered)

    if request.method == 'POST':
        username = request.POST['id']
        password = request.POST['password']
        nickname = request.POST['nickname']
        email = request.POST['email']
        signature = request.POST['sig']
        introduction = request.POST['introduce']
        language = request.POST['language']
        user_information_dic = {'username':username, 'password':password, 'nickname':nickname, 'email':email, 'signature':signature, 'self_introduction':introduction, 'default_language':language}
        ret, message = server.member_manager.register(user_information_dic)
        assert ret, message
        #send_mail(email, username, message)
        return HttpResponseRedirect("/")
    
    rendered = render_to_string('account/register.html', r)
    return HttpResponse(rendered)

def send_mail(email, username, confirm_key):
    sender = 'root_id@sparcs.org' #pv457, no_reply, ara, ara_admin
    receiver = email
    content = render_to_string('account/send_mail.html', {'username':username, 'confirm_key':confirm_key})
    subject = "confirm" + username
    msg = EmailMultiAlternatives(subject, '', sender, [receiver])
    msg.attach_alternative(content, "text/html")
    msg.send()
'''

def send_mail(email, username, confirm_key):
    HOST = 'smtp.naver.com'
    sender = 'root_id@sparcs.org'
    content = render_to_string('account/send_mail.html', {'username':username, 'confirm_key':confirm_key})
    title = "confirm"
    msg = MIMEText(content, _subtype="html", _charset='euc_kr')
    msg['Subject'] = title
    msg['From'] = sender
    msg['To'] = email
    s = smtplib.SMTP()
    s.connect(HOST)
    s.login('newtron_star', 'q1q1q1')
    s.sendmail(sender, [email], msg.as_string())
    s.quit()
'''

def confirm_user(request, username, confirm_key):
    server = arara.get_server()

    if request.method == 'POST':
        ret, mes = server.member_manager.confirm(username, confirm_key)
        return HttpResponse(mes)

    rendered = render_to_string('account/mail_confirm.html')
    return HttpResponse(rendered)

def agreement(request):
    sess, r = warara.check_logged_in(request)
    if r['logged_in'] == True:
        rendered = render_to_string('already_logged_in.html', r)
    else:
        rendered = render_to_string('account/register_agreement.html')

    return HttpResponse(rendered)

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        current_page = request.POST['current_page_url']
        client_ip = request.META['REMOTE_ADDR']
        server = arara.get_server()
        ret, session_key = server.login_manager.login(username, password, client_ip)
        assert ret, session_key
        request.session["arara_session_key"] = session_key
        request.session["arara_username"] = username
        return HttpResponseRedirect(current_page)

    return HttpResponseRedirect('/')

def logout(request):
    session_key, r = warara.check_logged_in(request)
    if r['logged_in'] == True:
        server = arara.get_server()
        ret, account = server.login_manager.logout(session_key)
        del request.session['arara_session_key']
        del request.session['arara_username']
        assert ret, account
        return HttpResponseRedirect("/")
    else:
        rendered = render_to_string('not_logged_in.html', r)
        return HttpResponse(rendered)

def account(request):
    session_key, r = warara.check_logged_in(request)
    if r['logged_in'] == True:
        server = arara.get_server()
        ret, account = server.member_manager.get_info(session_key)
        assert ret, account

        account['logged_in'] = True
        rendered = render_to_string('account/myaccount_frame.html', account)
    else:
        rendered = render_to_string('not_logged_in.html', r)
    return HttpResponse(rendered)

def user_information(request):
    if request.method == 'POST':
        session_key, r = warara.check_logged_in(request)
        server = arara.get_server()
        query_user_name = request.POST['query_user_name']
        ret, information = server.member_manager.query_by_username(session_key, query_user_name)
        return HttpResponse(repr(information))
    else:
        return HttpResponse('Must use POST')

def account_modify(request):
    session_key, r = warara.check_logged_in(request)
    if r['logged_in'] == True:
        server = arara.get_server()
        ret, account = server.member_manager.get_info(session_key)
        if request.method == 'POST':
            nickname = request.POST['mynickname']
            signature = request.POST['mysig']
            introduction = request.POST['myintroduce']
            language = request.POST['mylanguage']
            modified_information_dic = {'nickname':nickname, 'signature':signature, 'self_introduction':introduction, 'default_language':language}
            ret, message = server.member_manager.modify(session_key, modified_information_dic)
            assert ret, message
            return HttpResponseRedirect("/account/")
        else:
            account['logged_in'] = True
            rendered = render_to_string('account/myaccount_modify.html', account)
            return HttpResponse(rendered)
    else:
        rendered = render_to_string('not_logged_in.html', r)
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
            ret, message = server.member_manager.modify_password(session_key, user_information_dic)
            assert ret, message
            return HttpResponseRedirect("/account/")
        else:
            rendered = render_to_string('account/myacc_pw_modify.html')
            return HttpResponse(rendered)

    else:
        rendered = render_to_string('not_logged_in.html', r)
        return HttpResponse(rendered)

def account_remove(request):
    session_key, r = warara.check_logged_in(request)
    if r['logged_in'] == True:
        server = arara.get_server()
        if request.method == 'POST':
            ret, message = server.member_manager.remove_user(session_key)
            assert ret, message
            return HttpResponseRedirect("/")
        else:
            account = {}
            account['logged_in'] = True
            rendered = render_to_string('account/myaccount_remove.html', account)
            return HttpResponse(rendered)
    else:
        rendered = render_to_string('not_logged_in.html', r)
        return HttpResponse(rendered)

def id_check(request):
    if request.method == 'POST':
        server = arara.get_server()
        r = {}
        username = request.POST['check_id_field']
        ret = server.member_manager.is_registered(username)
        if ret:
            r = 'The ID is not available'
        else:
            r = 'The ID is available'
        return HttpResponse(r)
    else:
        return HttpResponse('Must use POST')

def nickname_check(request):
    if request.method == 'POST':
        server = arara.get_server()
        r = {}
        username = request.POST['check_nickname_field']
        ret = server.member_manager.is_registered_nickname(username)
        if ret:
            r = 'The nickname is not available'
        else:
            r = 'The nickname is available'
        return HttpResponse(r)
    else:
        return HttpResponse('Must use POST')
    
