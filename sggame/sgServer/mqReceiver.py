#coding:utf8
#author:zhoujingjiang
#date:2013-04-13
#分服消息处理程序
from gevent import monkey; monkey.patch_all()
from gevent.pool import Pool

import gevent

import amqp
import os

#--------------------------------------------------------------------
from root_config import system_root
import sys;sys.path.insert(0,'system_root')  #把项目根目录加入默认库路径 
import sgCfg.config as config
serverid = config.CFG_SERVER_ID #本服serverid
serverid = int(sys.argv[1]) if len(sys.argv) > 1 else serverid
print 'ServerId', serverid
from sgLib.setting import Setting
try:
    if serverid == 1:
        database = 'gamesg'
    else:
        database = 'gamesg%s'%serverid
        
    Setting.setDatabase(database)
except Exception, e:
    pass
#--------------------------------------------------------------------

from sgLib.mqManager import MqManager

print >>sys.stdout, 'pid is %s' % os.getpid()

#####      global variables       #####
recv_conn = None
gpool = Pool(100) #coroutine pool

##### end define global variables #####

def ensure_chan(conn):
    '''获取channel'''
    if not isinstance(conn, amqp.connection.Connection):
        conn = amqp.Connection(host=config.MQ_HOST, userid=config.MQ_UID,
                   password=config.MQ_PWD, virtual_host=config.MQ_VHOST, insit=False)
    else:
        for k in conn.channels:
            if isinstance(conn.channels[k], amqp.channel.Channel):
                return conn.channels[k]
    return conn.channel()

def main_loop():
    '''主循环'''
    global gpool
    recv_chan = None
    
    def logic_deal(msg):
        '''逻辑处理'''
        try:
            c = MqManager()
            gpool.spawn(c.checkOpt, msg.body)
        except Exception, e:
            print >>sys.stderr, 'receive a wrong message'
            print >>sys.stderr, str(e)
        finally:
            try:
                recv_chan.basic_ack(msg.delivery_tag)
            except Exception:
                pass
    #end logic_deal()
    
    while True:
        try:
            recv_chan.wait()
        except Exception:
            try:
                recv_chan = ensure_chan(recv_conn)
                recv_chan.basic_consume(queue='sggamequeue%s'%serverid,
                                        callback=logic_deal, consumer_tag="logic_deal")
            except Exception:
                gevent.sleep(5) #hog
                recv_conn = None
    recv_chan.basic_cancel("logic_deal") #永远也不会运行到

gpool.spawn(main_loop)
gpool.join()

print >>sys.stderr, 'application exit with exception'
sys.exit(1)
