#!/bin/env python

import curses, curses.panel, curses.textpad, curses.wrapper
import contextlib

@contextlib.contextmanager
def terminal():
    try:
        screen = curses.initscr()        
        curses.noecho()        
        curses.start_color()
        yield screen
    finally:
        curses.echo()        
        curses.endwin()
        print "DONE"

class Application(object):
    
    def __init__(self):
        with terminal() as screen:
            self.screen = screen
            self.tabs = [ Tab(self) ]
            self.refresh = self.screen.refresh
            self.nap = curses.napms
            self.cls = self.screen.clear
            
            self.tabs[0].display()
            self.activetab = self.tabs[0]
            self.refresh()
            
            while 1:
                self.activetab.handleinput ( self.screen.getch() )
            
    def decorate(self):
        self.cls()
        self.screen.box()
        for t in self.tabs:
            self.screen.addstr (1, 2, " | ".join( map(lambda x: x.tabtitle(), self.tabs)))
        pass

class Tab(object):
    def __init__(self, application):
        assert isinstance(application, Application)
        self.application = application
        self.screen = application.screen
        
    def display(self):
        self.application.cls()
        self.application.decorate()

    def tabtitle(self):
        return "Tab"

    def handleinput(self, i):
        self.screen.addstr (2, 2, `i` + "      ")
    
a = Application()
