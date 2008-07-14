#!/usr/bin/python
# coding: utf-8

import os
import urwid.curses_display
import urwid
from common import *

class ara_login(ara_forms):
    def get_login_message(self):
        basedir = os.path.dirname(__file__)
        banner = os.path.join(basedir, 'login.txt')
        f = open(banner, 'r')
        return f.read().decode('utf-8')
    
    def login(self, id, password, ip):
        retvalue = self.server.login_manager.login(id, password, ip)
        if retvalue[0] == True:
            return
        else:
            if retvalue[1] == 'WRONG_ID':
                self.errormessage.body.set_text(u"ID가 ㅇ벗습니다.")
            elif retvalue[1] == 'WRONG_PASSWORD':
                self.errormessage.body.set_text(u"비밀번호가 틀렸습니다.")
            elif retvalue[1] == 'DATABASE_ERROR':
                self.errormessage.body.set_text(u"데이터베이스 오류가 발생했습니다.")
            else:
                assert(False)
            self.idedit.body.set_edit_text("")
            self.pwedit.body.set_edit_text("")
            self.idpwpile.set_focus(0)

    def __keypress__(self, size, key):
        curfocus = self.bottomcolumn.get_focus_column()
        if key.strip() == 'tab':
            self.bottomcolumn.set_focus_column((curfocus + 1) % 3)
        elif key.strip() == 'enter':
            if curfocus == 0:
                if self.idpwpile.get_focus() == self.idedit:
                    self.idpwpile.set_focus(1)
                elif self.idpwpile.get_focus() == self.pwedit:
                    self.login(self.idedit.body.get_edit_text(), self.pwedit.body.get_edit_text(), "127.0.0.1")
                else:
                    assert(False)
            elif curfocus == 1:
                pass
            elif curfocus == 2:
                pass
        else:
            if curfocus == 1:
                self.langlist.keypress(size, key)
            elif curfocus == 2:
                self.joinlist.keypress(size, key)
            else:
                self.bottomcolumn.keypress(size, key)

    def __initwidgets__(self):
        self.message = urwid.Filler(urwid.Text(self.get_login_message(), align="center"))
        self.errormessage = urwid.Filler(urwid.Text("", align="center"))
        self.message_ko = urwid.Filler(urwid.Text(u"[Tab] 키를 누르면 항목간을 전환할 수 있습니다", align='center'))
        self.message_en = urwid.Filler(urwid.Text(u"Press [Tab] key to jump between each items", align='center'))

        self.idedit = urwid.Filler(urwid.Edit(caption="ID:", wrap='clip'))
        self.pwedit = urwid.Filler(urwid.Edit(caption="Password:", wrap='clip'))
        self.idpwpile = urwid.Pile([self.idedit, self.pwedit])


        langitems = ['Korean','English','Chinese']
        langitems = [Item(w, None, 'selected') for w in langitems]
        self.langlist = urwid.LineBox(urwid.ListBox(urwid.SimpleListWalker(langitems)))

        joinitems = ['Join','Guest']
        joinitems = [Item(w, None, 'selected') for w in joinitems]
        self.joinlist = urwid.LineBox(urwid.ListBox(urwid.SimpleListWalker(joinitems)))

        self.bottomcolumn = urwid.Columns([('weight',40,self.idpwpile),('weight',30,self.langlist),('weight',30,self.joinlist)])

        content = [self.message,('fixed',1,self.errormessage),('fixed',1, self.dash), ("fixed", 1, self.message_ko), ('fixed',1,self.message_en), ('fixed',1,self.blank), ('fixed',5,self.bottomcolumn)]
        self.mainpile = urwid.Pile(content)

        self.keymap = {'left':'', 'right':''}
	return self.mainpile

ara_login().main()

# vim: set et ts=8 sw=4 sts=4:
