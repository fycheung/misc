# -*- coding:utf-8 -*-  
# author:lizr
# date:2013-5-7
# 日志中心类,暂只记录数据库，以后要写文件也添加到这里

import time

from sgLib.core import Gcore
import gevent
import gevent.queue

class DbLogger(object):
    def __init__(self):
        self._queue = gevent.queue.Queue()
        self.con,self.cursor = Gcore.objDB._create()
        #print 'self.con',self.con
        #print 'self.cursor',self.cursor
    
    def refreshCon(self):
        '''刷新连接'''
        self.con,self.cursor = Gcore.objDB._create()
        
    def put(self, sql):
        self._queue.put(sql)
        #print time.time(),'Rabbit.put > _queue.put',msg

    def loop(self):
        print 'DbLogger.loop()'
        while True:
            sql = self._queue.get()
            #print '获得日志sql:',sql
            try:
                self.cursor.execute(sql)
                #self.con.commit()
                gevent.sleep(0.02)
            except:
                try:
                    self.refreshCon()
                    self.cursor.execute(sql) #2次尝试  以防万一 (正常不会运行到)
                    #self.con.commit()
                    gevent.sleep(0.02)
                except:
                    try:
                        import traceback
                        import sys
                        strExcept = traceback.format_exc()
                        print >>sys.stderr, 'Time:' + time.strftime('%Y-%m-%d %H:%M:%S') + '\n' \
                                + 'Location:DbLogger.loop\n' \
                                + 'Sql:' + sql + '\n' \
                                + strExcept
                        sys.stderr.flush()
                    except:
                        pass
                

if '__main__' == __name__:
    '''调试'''
    c = DbLogger()
    c.refreshCon()
    #print c.put('sql abc')
    #print c.loop()
    #import gevent
    gevent.sleep(3)
    print 'end'

