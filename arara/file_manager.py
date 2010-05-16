#!/usr/bin/python
# -*- coding: utf-8 -*-

import md5 as hashlib
import time

from sqlalchemy import and_, or_, not_
from sqlalchemy.exceptions import InvalidRequestError
from arara import model
from arara_thrift.ttypes import *
from arara.util import require_login
from arara.util import log_method_call_with_source, log_method_call_with_source_important
from arara.server import get_server

log_method_call = log_method_call_with_source('file_manager')
log_method_call_important = log_method_call_with_source_important('file_manager')

DANGER_FILE = ('php', 'asp', 'php3', 'php4', 'htaccess', 'js',
               'html', 'htm', '.htaccess', 'jsp')

class FileManager(object):
    '''
    파일 처리 관련 클래스

    TThreadPoolServer, TThreadedServer, TForkingServer 모두 사용가능.
    '''
    
    def __init__(self):
        pass

    def _is_board_exist(self, board_name):
        # XXX 2010.05.15 : Deprecated Check 하고 없애자.
        ret, _ = get_server().board_manager.get_board(board_name)
        if ret:
            return True, 'OK'
        else:
            return False, 'BOARD_NOT_EXIST'

    def _get_article(self, session, article_id):
        try:
            return session.query(model.Article).filter_by(id=article_id).one()
        except InvalidRequestError:
            session.close()
            raise InvalidOperation("article does not exist")

    @require_login
    @log_method_call_important
    def save_file(self, session_key, article_id, filename):
        '''
        article작성시 파일을 저장할 장소와 저장할 파일명를 리턴해주는 함수
        
        @type  session_key: string
        @param session_key: User Key
        @type  article_id: integer
        @param article_id: Article Number
        @type  filename: string
        @param filename: File Name
        @rtype: dictionary
        @return:
            1. 저장 성공: {'file_path': blah1, 'saved_filename': blah2}
            2. 저장 실패:
                1. 로그인되지 않은 유저: NotLoggedIn Exception
                2. 위험한 파일: InvalidOperation Exception
                3. 데이터베이스 오류: InternalError Exception
        '''
        #그 경로의 파일이 있다고 가정하고 저장

        file_ext = filename.split('.')[-1]
        if file_ext in DANGER_FILE:
            return InvalidOperation('danger file detected')
        
        session = model.Session()
        article = self._get_article(session, article_id)
        filepath_to_save = u''+str(article.board.board_name) + '/' +str(article.date.year) + '/' + str(article.date.month) + '/' + str(article.date.day)
        try:
            # Generate unique filename by putting timestamp at the end of the hasing string
            ghost_filename = u''+hashlib.md5(filename.encode('utf-8') + str(article.author.id) + str(article.board.id) + str(article.id) + str(time.time())).hexdigest()
            file = model.File(filename, ghost_filename, filepath_to_save, article.author, article.board, article)
            session.add(file)
            session.commit()
            session.close()
            return FileInfo(filepath_to_save, ghost_filename)
        except Exception: 
            session.close()
            raise InternalError('database error')

    def _get_file(self, session, file_id, article):
        try:
            return session.query(model.File).filter(
                    and_(model.file_table.c.id == file_id,
                    model.file_table.c.user_id == article.author.id,
                    model.file_table.c.board_id == article.board.id,
                    model.file_table.c.article_id == article.id, 
                    model.file_table.c.deleted == False
                    )).one()
        except InvalidRequestError:
            session.close()
            raise InvalidOperation('file not found')

    @log_method_call
    def download_file(self, article_id, file_id):
        '''
        article의 파일을 다운로드 할때 실제로 파일이 저장된 장소와 저장된 파일명을 리턴해주는 함수 
        
        @type  article_id: Integer 
        @param article_id: Article Number 
        @type  filename: string
        @param filename: File Name
        @rtype: dictionary
        @return:
            1. 경로 찾기 성공: {'file_path': blah, 'saved_filename': blah, 'real_filename': blah}
            2. 경로 찾기 실패:
                1. 로그인되지 않은 유저: NotLoggedIn Exception
                2. 데이터베이스 오류: InternalError Exception
        '''
        session = model.Session()
        article = self._get_article(session, article_id)
        file = self._get_file(session, file_id, article)

        download_path = file.filepath
        ghost_filename = file.saved_filename
        real_filename = file.filename
        session.commit()
        session.close()
        return DownloadFileInfo(download_path, ghost_filename, real_filename)

    @require_login
    @log_method_call_important
    def delete_file(self, session_key, article_id, file_id):
        '''
        지울 파일이 저장된 장소와 저장된 파일명을 리턴해주는 함수
        
        @type  session_key: string
        @param session_key: User Key
        @type  article_id: Integer 
        @param article_id: Article Number 
        @type  filename: string
        @param filename: File Name
        @rtype: dictionary
        @return:
            1. 성공: {'file_path': 'blah/blah', 'saved_filename': 'blah'}
            2. 실패:
                1. 로그인되지 않은 유저: False, 'NOT_LOGGEDIN'
                2. 데이터베이스 오류: False, 'DATABASE_ERROR'
        '''
        #ret, filepath_to_delete= self.download_file(session_key, article_id, filename)
        #download_file함수와 유사하다.. 똑같은 코드가 많다.. 먼가 비효율적이다.. 나중에 하나로 좀 해보자.. 일단 지금은 급하니까.. 복사해놓고...
        session = model.Session()
        article = self._get_article(session, article_id)
        file = self._get_file(session, file_id, article)

        file.deleted = True
        download_path = file.filepath
        ghost_filename = file.saved_filename
        session.commit()
        session.close()
        return FileInfo(download_path, ghost_filename)
