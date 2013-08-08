# -*- coding: utf-8 -*-
#author: Lizr
#date: 2013-07-20

from sgCfg.config import CFG_SERVER_ID
from sgCfg.config import LOGGING_OUT_LEVEL
from sgCfg.config import LOGGING_LOG_LEVEL

import logging
import logging.handlers
from datetime import date
import os
from os.path import dirname,abspath
from os.path import isfile

from time import time,sleep
def logit():
    def logged(f):
        def wrapped(*args, **kargs):
            now =time()
            try:
                result = f(*args, **kargs)
                return result
            finally:
                l = Logger('logit')
                s = "Called:\n function: %s \n args: %r kargs %r \n result:%s \n time use: %s" % (f,args,kargs,result,round(time()-now,3))
                l.debug(s)
        return wrapped
    try:
        return logged
    except KeyError,e:
        raise ValueError(e), ''

def Logger(tag='system',filename='',sizeM=50):
    ''' 日志记录
    @param tag: 日志的name标签
    @param filename: 默认空:服务器+日志  s1.2013-07-20.log , 非空: 服务器+日志 +指定 s1.2013-07-20.myfile.log
    @param sizeM:日志文件最大容量 默认50M
    '''
    assert len(tag)<=8 #下面用了-8s 为整齐起见,e.g. lizr , zhoujj, zhanggh,... temp等
    
    # create logger with "spam_application"
    logger = logging.getLogger(tag)
    logger.setLevel(logging.DEBUG)
    
    # create file handler which logs even debug messages
    #logfile = dirname( abspath( __file__ ) )+'/log/'+str(date.today())+filename+'.log'
    if filename:
        logfile = dirname( abspath( __file__ ) )+'/log/s%s.%s.%s.log'%(CFG_SERVER_ID,date.today(),filename)
    else:
        logfile = dirname( abspath( __file__ ) )+'/log/s%s.%s.log'%(CFG_SERVER_ID,date.today())
    
    try:
        ifexist = isfile(logfile)
    except:
        ifexist = True
    #fh = logging.FileHandler(logfile)
    fh = logging.handlers.RotatingFileHandler(
              logfile, maxBytes=int(sizeM)*1024*1024) #10M

    fh.setLevel(LOGGING_LOG_LEVEL)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(LOGGING_OUT_LEVEL)
    # create formatter and add it to the handlers
    formatter = logging.Formatter("\n%(asctime)s - %(name)-8s - %(levelname)-8s - %(filename)-15s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    if not ifexist and os.name != "nt":
        try:
            os.system("chmod 777 %s"%logfile)
        except:
            pass
    return logger



if("__main__" == __name__):
   
#    @logit()
#    def hello(name,xi,a='you'):
#        sleep(0.16)
#        print "Hello,",name,xi,a
#    hello("bbbb","World!",a="fuck")
    
    import gevent
    class c:
        pass
    logger = Logger('zhoujj','my');
    logger.debug('hello debug!');
    logger.info('hello info!');
    logger.error({'a':1,'b':2});
    logger.critical(c())
    '''
    logger = Logger('bbb','xxx');
    logger.debug('hello debug!');
    logger.info('hello info!');
    logger.error('hello error!');
    logger.critical('hello critical!')'''
