#!/bin/env python

import MySQLdb as db
from threading import Thread
from Queue import Queue 
from multiprocessing import Process
from multiprocessing.connection import Listener

class connection (Thread):
    def __init__(self, qready, **kkw):
        Thread.__init__(self, None, None, "dbconnection" )
        self.iq = Queue(1)
        self.oq = Queue(1)
        self.qready = qready
        self.conn_params = kkw
        
    def run(self):
        conn = db.Connect ( ** self.conn_params )        
        conn.set_character_set ( 'utf8' )
        while True:
            self.qready.put (self)
            query = self.iq.get()
            if query is None: break
            cursor = conn.cursor()            
            assert (isinstance(cursor, db.cursors.Cursor))            
            try:
                cursor.execute (query )
                (desc, rows) = (cursor.description, cursor.fetchall())
                self.oq.put ( (desc, rows) )
            except:
                print "Error"
            del cursor
            
        conn.close()
        print "Done"
        

class connectionpool(object):
    def __init__(self, conn_cnt):
        self.qready = Queue()
        conn_params = { 'host' : '83.243.39.5', 'db': 'techdb',
                        'user' : 'netcon_user', 'passwd' : 'wajig_05850HAX0R' }
        self.connections = [ connection(self.qready, ** conn_params) for i in range(0, conn_cnt) ]
        _ = [ c.start() for c in self.connections ]
    
    def killall(self):
        _ = [ c.iq.put ( None ) for c in self.connections ]
    
    def query ( self, q ):
        conn = self.qready.get()
        conn.iq.put ( q )
        (d, r) = conn.oq.get()        
        return (d,r)
    
