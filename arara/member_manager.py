# -*- coding: utf-8 -*-

import md5

from arara.util import require_login, filter_dict, is_keys_in_dict
from arara import model
from sqlalchemy.exceptions import InvalidRequestError

class NoPermission(Exception):
    pass

class WrongPassword(Exception):
    pass

class NotLoggedIn(Exception):
    pass

USER_PUBLIC_KEYS = ['username', 'password', 'nickname', 'email',
        'signature', 'self_introduction', 'default_language']
USER_QUERY_WHITELIST = ('username', 'nickname', 'email',
        'signature', 'self_introduction')
USER_PUBLIC_WHITELIST= ('username', 'password', 'nickname', 'email',
        'signature', 'self_introduction', 'default_language', 'activated')
USER_PUBLIC_MODIFIABLE_WHITELIST= ('nickname', 'email',
        'signature', 'self_introduction', 'default_language')

class MemberManager(object):
    '''
    회원 가입, 회원정보 수정, 회원정보 조회, 이메일 인증등을 담당하는 클래스
    '''

    def __init__(self):
        # mock data
        self.member_dic = {}  # DB에서 member table를 read해오는 부분

    def _set_login_manager(self, login_manager):
        self.login_manager = login_manager

    def _authenticate(self, username, password):
        session = model.Session()
        try:
            user = session.query(model.User).filter_by(username=username).one()
            if user.compare_password(password):
                return True, None
            else:
                return False, 'WRONG_PASSWORD'
        except InvalidRequestError:
            return False, 'WRONG_USERNAME'


    def register(self, user_reg_dic):
        '''
        DB에 회원 정보 추가. activation code를 발급한다.

        >>> user_reg_dic = { 'username':'mikkang', 'password':'mikkang', 'nickname':'mikkang', 'email':'mikkang', 'sig':'mikkang', 'self_introduce':'mikkang', 'default_language':'english' }
        >>> member_manager.register(user_reg_dic)
        (True, '12tge8r9ytu23oytw8')

        - Current User Dictionary { username, password, nickname, email, sig, self_introduce, default_language }

        @type  user_reg_dic: dictionary
        @param user_reg_dic: User Dictionary
        @rtype: string
        @return:
            1. register 성공: True, self.member_dic[user_reg_dic['username']]['activation_code']
            2. register 실패:
                1. 양식이 맞지 않음(부적절한 NULL값 등): 'WRONG_DICTIONARY'
                2. 데이터베이스 오류: False, 'DATABASE_ERROR'
        '''

        if not is_keys_in_dict(user_reg_dic, USER_PUBLIC_KEYS):
            return False, 'WRONG_DICTIONARY'

        if user_reg_dic['username'].lower() == 'sysop':
            return False, 'PERMISSION_DENIED'

        activation_code = md5.md5(user_reg_dic['username']+
                user_reg_dic['password']+user_reg_dic['nickname']).hexdigest()
        
        try:
            # Register user to db
            user = model.User(**user_reg_dic)
            session = model.Session()
            session.save(user)
            # Register activate code to db
            user_activation = model.UserActivation(user, activation_code)
            session.save(user_activation)
            session.commit()
        except Exception, e:
            session.rollback()
            return False, e

        return True, activation_code


    def confirm(self, username_to_confirm, confirm_key):
        '''
        인증코드(activation code) 확인.

        >>> member_manager.confirm('mikkang', register_key)
        (True, 'OK')
        >>> member_manager.confirm('mikkang', 'asdfasdfasdfsd')
        (False, 'WRONG_CONFIRM_KEY')

        @type  username_to_confirm: string
        @param username_to_confirm: Confirm ID
        @type  confirm_key: integer
        @param confirm_key: Confirm Key
        @rtype: string
        @return:
            1. 인증 성공: True, 'OK'
            2. 인증 실패:
                1. 잘못된 인증코드: False, 'WRONG_CONFIRM_KEY'
                2. 데이터베이스 오류: False, 'DATABASE_ERROR'
        '''
        
        session = model.Session()
        user = session.query(model.User).filter(model.User.username == username_to_confirm).one()
        user_activation = session.query(model.UserActivation).filter_by(user_id=user.id).one()

        if user_activation.activation_code == confirm_key:
            user_activation.user.activated = True
            session.delete(user_activation)
            session.commit()
            return True, 'OK'
        else:
            return False, 'WRONG_CONFIRM_KEY'
        

    def is_registered(self, user_username):
        '''
        등록된 사용자인지의 여부를 알려준다.
        Confirm은 하지 않았더라도 등록되어있으면 True를 리턴한다.

        @type  user_username: string
        @param user_username: ID to check whether is registered or not
        @rtype: bool
        @return:
            1. 존재하는 사용자: True
            2. 존재하지 않는 사용자: False

        >>> member_manager.is_registered('mikkang')
        True
        '''
        #remove quote when MD5 hash for UI is available
        #

        session = model.Session()
        query = session.query(model.User).filter_by(username=user_username)
        try:
            user = query.one()
            return True
        except InvalidRequestError:
            return False

    def get_info(self, session_key):
        '''
        회원 정보 수정을 위해 현재 로그인된 회원의 정보를 가져오는 함수.
        다른 사용자의 정보를 열람하는 query와 다름.

        @type  session_key: string
        @param session_key: User Key
        @rtype: dictionary
        @return:
            1. 가져오기 성공: True, user_dic
            2. 가져오기 실패:
                1. 로그인되지 않은 유저: False, 'NOT_LOGGEDIN'
                2. 존재하지 않는 회원: False, 'MEMBER_NOT_EXIST'
                3. 데이터베이스 오류: False, 'DATABASE_ERROR'
        '''
        try:
            session = model.Session()
            username = self.login_manager.get_session(session_key)[1]['username']
            user = session.query(model.User).filter_by(username=username).one()
            user_dict = filter_dict(user.__dict__, USER_PUBLIC_WHITELIST)
            return True, user_dict
        except InvalidRequestError:
            return False, "MEMBER_NOT_EXIST"

        
    def modify_password(self, session_key, user_password_dict):
        '''
        회원의 password를 수정.

        ---user_password_dict {username, current_password, new_password}

        @type  session_key: string
        @param session_key: User Key
        @type  user_password_dict: Dictionary
        @param user_password_dict: User Dictionary
        @rtype: string
        @return:
            1. modify 성공: True, 'OK'
            2. modify 실패:
                1. 수정 권한 없음: 'NO_PERMISSION'
                2. 잘못된 현재 패스워드: 'WRONG_PASSWORD'
                3. 로그인되지 않은 유저: False, 'NOT_LOGGEDIN'
                4. 데이터베이스 오류: False, 'DATABASE_ERROR'
        '''
        session_info = self.login_manager.get_session(session_key)[1]
        username = session_info['username']
        session = model.Session()
        user = session.query(model.User).filter_by(username=username).one()
        try:
            if not username == user_password_dict['username']:
                raise NoPermission()
            if not user.compare_password(user_password_dict['current_password']):
                raise WrongPassword()
            user.password = user_password_dict['new_password']
            return True, 'OK'
            
        except NoPermission:
            return False, 'NO_PERMISSION'

        except WrongPassword:
            return False, 'WRONG_PASSWORD'

        except KeyError:
            return False, 'NOT_LOGGEDIN'


    @require_login
    def modify(self, session_key, user_reg_dict):
        '''
        password를 제외한 회원 정보 수정

        @type  session_key: string
        @param session_key: User Key
        @type  user_reg_dict: dictionary
        @param user_reg_dict: User Dictionary
        @rtype: string
        @return:
            1. modify 성공: True, 'OK'
            2. modify 실패:
                1. 로그인되지 않은 유저: False, 'NOT_LOGGEDIN'
                2. 데이터베이스 오류: False, 'DATABASE_ERROR'
                3. 양식이 맞지 않음(부적절한 NULL값 등): 'WRONG_DICTIONARY'
        '''
        session_info = self.login_manager.get_session(session_key)[1]
        username = session_info['username']

        if not is_keys_in_dict(user_reg_dict, USER_PUBLIC_KEYS):
            return False, 'WRONG_DICTIONARY'
        user_modify_dict = filter_dict(user_reg_dict, USER_PUBLIC_MODIFIABLE_WHITELIST)
        session = model.Session()
        user = session.query(model.User).filter_by(username=username).one()
        for key, value in user_modify_dict.items():
            setattr(user, key, value)
        session.commit()
        return True, 'OK'

    @require_login
    def query_by_username(self, session_key, query_username):
        '''
        쿼리 함수

        member.query_by_username(session_key, 'pv457')
        True, {'user_username': 'pv457', 'user_nickname': '심영준',
        'self_introduce': '...', 'user_ip': '143.248.234.111'}

        ---query_dic { user_username, user_nickname, self_introduce, user_ip }

        @type  session_key: string
        @param session_key: User Key
        @type  query_username: string
        @param query_username: User ID to send Query
        @rtype: dictionary
        @return:
            1. 쿼리 성공: True, query_dic
            2. 쿼리 실패:
                1. 존재하지 않는 아이디: False, 'QUERY_ID_NOT_EXIST'
                2. 로그인되지 않은 유저: False, 'NOT_LOGGEDIN'
                3. 데이터베이스 오류: False, 'DATABASE_ERROR'
        '''
        try:
            session = model.Session()
            query_user = session.query(model.User).filter_by(username=query_username).one()
            query_user_dict = filter_dict(query_user.__dict__, USER_QUERY_WHITELIST)
            return True, query_user_dict
        except InvalidRequestError:
            return False, "QUERY_ID_NOT_EXIST"

    @require_login
    def query_by_nick(self, session_key, query_nickname):
        '''
        쿼리 함수

        member.query_by_nick(session_key, '심영준')
        True, {'user_username': 'pv457', 'user_nickname': '심영준',
        'self_introduce': '...', 'user_ip': '143.248.234.111'}

        ---query_dic { user_username, user_nickname, self_introduce, user_ip }

        @type  session_key: string
        @param session_key: User Key
        @type  query_nickname: string
        @param query_nickname: User Nickname to send Query
        @rtype: dictionary
        @return:
            1. 쿼리 성공: True, query_dic
            2. 쿼리 실패:
                1. 존재하지 않는 닉네임: False, 'QUERY_NICK_NOT_EXIST'
                2. 로그인되지 않은 유저: False, 'NOT_LOGGEDIN'
                3. 데이터베이스 오류: False, 'DATABASE_ERROR'
        '''
        try:
            session = model.Session()
            query_user = session.query(model.User).filter_by(nickname=query_nickname).one()
            query_user_dict = filter_dict(query_user.__dict__, USER_QUERY_WHITELIST)
            return True, query_user_dict
        except InvalidRequestError:
            return False, "QUERY_NICK_NOT_EXIST"

    @require_login
    def remove_user(self, session_key):
        '''
        session key로 로그인된 사용자를 등록된 사용자에서 제거한다' - 회원탈퇴

        @type  session_key: string
        @param session_key: User Key
        @rtype: String
        @return:
            1. 성공시: True, 'OK'
            2. 실패시: False, 'NOT_LOGGEDIN'
        '''

        session = model.Session()
        username = self.login_manager.get_session(session_key)[1]['username']
        try:
            user = session.query(model.User).filter_by(username=username).one()
            user.activated = False
            session.commit()

            return True, 'OK'
        except KeyError:
            return False, 'NOT_LOGGEDIN'
        
    @require_login
    def search_user(self, session_key, search_user_info):
        '''
        member_dic 에서 찾고자 하는 username와 nickname에 해당하는 user를 찾아주는 함수

        @type  session_key: string
        @param session_key: User Key
        @type  search_user_info: dictionary
        @param search_user_info: User Info(username or nickname)
        @rtype: String
        @return:
            1. 성공시: True, USERNAME
            2. 실패시: False, 'NOT_EXIST_USER'
        '''

        try:
            session = model.Session()
            assert len(search_user_info.keys()) == 1
            key = search_user_info.keys()[0]
            assert key == 'username' or key == 'nickname'
            import sys
            user = session.query(model.User).filter_by(**search_user_info).one()
            return True, user.username
        except InvalidRequestError:
            return False, 'NOT_EXIST_USER'
        except AssertionError:
            return False, 'INVALID_KEY'

    @require_login
    def is_sysop(self, session_key):
        '''
        로그인한 user가 SYSOP인지 아닌지를 확인하는 함수
        
        @type  session_key: string
        @param session_key: User Key
        @rtype: String
        @return:
            1. SYSOP일시: True
            2. SYSOP이 아닐시: False
        '''

        if self.login_manager.get_session(session_key)[1]['username'] == 'SYSOP':
            return True
        else:
            return False

# vim: set et ts=8 sw=4 sts=4
