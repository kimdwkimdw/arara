# -*- coding: utf-8 -*-

import datetime
import time

from sqlalchemy.exceptions import InvalidRequestError, IntegrityError
from arara import model
from arara.util import filter_dict, require_login, is_keys_in_dict
from arara.util import log_method_call_with_source, log_method_call_with_source_important
from arara.util import smart_unicode, datetime2timestamp

from arara_thrift.ttypes import *
from arara.server import get_server

log_method_call = log_method_call_with_source('blacklist_manager')
log_method_call_important = log_method_call_with_source_important('blacklist_manager')

class AlreadyAddedException(Exception):
    pass

class NotExistUSERNAMEException(Exception):
    pass

class NotLoggedIn(Exception):
    pass

BLACKLIST_DICT = ['blacklist_username', 'block_article', 'block_message']
BLACKLIST_LIST_DICT = ['id', 'blacklisted_user_nickname', 'blacklisted_user_username', 'blacklisted_date', 'last_modified_date', 'block_article', 'block_message']

class BlacklistManager(object):
    '''
    블랙리스트 처리 관련 클래스

    TThreadedServer, TThreadPoolServer, TForkingServer 가 가능하다.
    '''
    def __init__(self):
        pass

    def _get_dict(self, item, whitelist):
        item_dict = item.__dict__
        if item_dict['user_id']:
            item_dict['username'] = item.user.username
            del item_dict['user_id']
        if item_dict['blacklisted_user_id']:
            item_dict['blacklisted_user_username'] = item.target_user.username
            item_dict['blacklisted_user_nickname'] = item.target_user.nickname
            del item_dict['blacklisted_user_id']
        item_dict['last_modified_date'] = \
                datetime2timestamp(item_dict['last_modified_date'])
        item_dict['blacklisted_date'] = \
                datetime2timestamp(item_dict['blacklisted_date'])
        filtered_dict = filter_dict(item_dict, whitelist)

        return BlacklistInformation(**filtered_dict)

    def _get_dict_list(self, raw_list, whitelist):
        return [self._get_dict(item, whitelist) for item in raw_list]

    def _get_user(self, session, username):
        try:
            user = session.query(model.User).filter_by(username=smart_unicode(username)).one()
        except InvalidRequestError:
            session.close()
            raise InvalidOperation('username not exist')
        return user

    @require_login
    @log_method_call_important
    def add(self, session_key, username, block_article=True, block_message=True):
        '''
        블랙리스트 username 추가

        default 값: article과 message 모두 True

        @type  session_key: string
        @param session_key: User Key
        @type  username: stirng
        @param username: Blacklist Username
        @rtype: void
        @return:
            1. 추가 성공: void
            2. 추가 실패:
                1. Wrong Dictionary: InvalidOperation Exception
                2. 존재하지 않는 아이디: InvalidOperation Exception 
                3. 자기 자신은 등록 불가: InvalidOperation Exception 
                4. 이미 추가되어있는 아이디: InvalidOperation Exception
                5. 로그인되지 않은 사용자: NotLoggedIn Exception
                6. 데이터베이스 오류: InternalError Exception 
        '''
        user_info = get_server().login_manager.get_session(session_key)
        username = smart_unicode(username)
        if username == user_info.username:
            raise InvalidOperation('cannot add yourself')

        session = model.Session()
        user = self._get_user(session, user_info.username)
        target_user = self._get_user(session, username)

        integrity_chk = session.query(model.Blacklist).filter_by(user_id=user.id, 
                        blacklisted_user_id=target_user.id).all()
        if integrity_chk:
            session.close()
            raise InvalidOperation('already added')
        new_blacklist = model.Blacklist(user, target_user, block_article, block_message)
        session.add(new_blacklist)
        session.commit()
        session.close()
        return
       
    @require_login
    @log_method_call_important
    def delete_(self, session_key, username):
        '''
        블랙리스트 username 삭제 

        >>> blacklist.delete(session_key, 'pv457')
        True, 'OK'

        @type  session_key: string
        @param session_key: User Key
        @type  username: string
        @param blacklist_id: Blacklist USERNAME
        @rtype: void
        @return:
            1. 삭제 성공: void 
            2. 삭제 실패:
                1. 블랙리스트에 존재하지 않는 아이디: InvalidOperation Exception 
                2. 로그인되지 않은 사용자: InvalidOperation Exception
                3. 데이터베이스 오류: InternalError Exception
        '''
        
        user_id = get_server().login_manager.get_user_id(session_key)
        username = smart_unicode(username)

        session = model.Session()
        blacklisted_user = self._get_user(session, username)

        try:
            blacklist_to_del = session.query(model.Blacklist).filter_by(user_id=user_id,
                                blacklisted_user_id=blacklisted_user.id).one()
        except InvalidRequestError:
            session.close()
            raise InvalidOperation('username not in blacklist')
        session.delete(blacklist_to_del)
        session.commit()
        session.close()
        return

    @require_login
    @log_method_call_important
    def modify(self, session_key, blacklist_info):
        '''
        블랙리스트 id 수정 

        >>> blacklist.modify(session_key, {'blacklisted_user_username': 'pv457', 
        'block_article': 'False', 'block_message': 'True'})

        @type  session_key: string
        @param session_key: User Key
        @type  blacklist_dic: dictionary
        @param blacklist_dic: Blacklist Dictionary
        @rtype: void
        @return:
            1. 수정 성공: void
            2. 수정 실패:
                1. 블랙리스트에 존재하지 않는 아이디: InvalidOperation Exception 
                2. 로그인되지 않은 사용자: InvalidOperation Exception
                3. 데이터베이스 오류: InternalError Exception
        '''
        
        #if not is_keys_in_dict(blacklist_dict, BLACKLIST_DICT):
        #    return False, 'WRONG_DICTIONARY'

        user_id = get_server().login_manager.get_user_id(session_key)

        session = model.Session()
        target_user = self._get_user(session, blacklist_info.blacklisted_user_username)
        try:
            blacklist_to_modify = session.query(model.Blacklist).filter_by(user_id=user_id,
                                    blacklisted_user_id=target_user.id).one()
        except InvalidRequestError:
            session.close()
            raise InvalidOperation('username not in blacklist')
        blacklist_to_modify.block_article = blacklist_info.block_article
        blacklist_to_modify.block_message = blacklist_info.block_message
        blacklist_to_modify.last_modified_date = datetime.datetime.fromtimestamp(time.time())
        session.commit()
        session.close()
        return

    @require_login
    @log_method_call
    def list_(self,session_key):
        '''
        블랙리스트로 설정한 사람의 목록을 보여줌

        >>> blacklist.list_show(session_key)
        True, [{'blacklisted_user_username': 'pv457', 'blacklisted_user_nickname': 'pv457',
        'last_modified_date': 1020308.334, 'blacklisted_date': 1010308.334,
        'block_article': False, 'block_message': True, id: 1},

        @type  session_key: string
        @param session_key: User Key
        @rtype: list
        @return:
            1. 성공: True, Blacklist Dictionary List
            2. 실패:
                1. 로그인되지 않은 사용자: False, 'NOT_LOGGEDIN'
                2. 데이터베이스 오류: False, 'DATABASE_ERROR'
        '''

        user_id = get_server().login_manager.get_user_id(session_key)
        try:
            session = model.Session()
            blacklist_list = session.query(model.Blacklist).filter_by(user_id=user_id).all()
            session.close()
            blacklist_list = self._get_dict_list(blacklist_list, BLACKLIST_LIST_DICT)
        except:
            session.close()
            raise InternalError('database error')
        return blacklist_list

    @require_login
    @log_method_call
    def get_article_blacklisted_userid_list(self,session_key):
        '''
        Article 에 대해 블랙리스트로 설정한 사람의 목록을 돌려줌.

        >>> 사용법 추가해 넣을 것.

        @type  session_key: string
        @param session_key: User Key
        @rtype: list
        @return:
            1. 성공: True, Blacklist Dictionary List
            2. 실패:
                1. 로그인되지 않은 사용자: False, 'NOT_LOGGEDIN'
                2. 데이터베이스 오류: False, 'DATABASE_ERROR'
        '''

        user_id = get_server().login_manager.get_user_id(session_key)
        try:
            session = model.Session()
            raw_blacklist = session.query(model.Blacklist).filter_by(user_id=user_id, block_article=True).all()
            session.close()
            userid_blacklist = [x.blacklisted_user_id for x in raw_blacklist]
        except:
            session.close()
            raise InternalError('database error')
        return userid_blacklist

# vim: set et ts=8 sw=4 sts=4
