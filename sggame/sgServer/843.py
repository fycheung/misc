# -*- coding: utf-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf-8')
if(sys.platform=="win32"):
    from twisted.internet import selectreactor
    selectreactor.install()
elif "freebsd" in sys.platform:
    from twisted.internet import kqreactor
    kqreactor.install()
elif "linux" in sys.platform:
    from twisted.internet import epollreactor
    epollreactor.install()


import time
#import json;
#import struct;
#import traceback;
#import hashlib;
#import base64;

#from Storage import CStorage
#from QueueStorage import CMStorage
#from Security import CSecurity
#from Config import Config
#from NotifyHttp import NotifyHttp


from twisted.internet.protocol import Factory,Protocol
from twisted.internet import reactor,address
#from twisted.internet import defer,task
#import random;

#输出文字
def OutMsg(messagebox,msg_type=1):
    pass;
    messagebox=messagebox.decode("utf-8")
    print "["+time.strftime("%Y-%m-%d %H:%M:%S")+"] >>> "+messagebox+""
    
class RichProtocol(Protocol):
    def connectionMade(self):
        OutMsg('Client [%s] link!'% self.transport.getPeer())

    def connectionLost(self,reason):
        OutMsg('Client[%s] stop!' % self.transport.getPeer())
    
    def dataReceived(self,recv_data):
        if(recv_data.find('<policy-file-request/>')!=-1):
            OutMsg('Client[%s] send!' % self.transport.getPeer())
            self.transport.write('<cross-domain-policy><allow-access-from domain="*" to-ports="*"/></cross-domain-policy>\0');#发送授权
            #self.transport.loseConnection();

    
class RichFactory(Factory):
    protocol=RichProtocol
    def __init__(self):
        print 'Start GameServer'
        
port = 843
argv = sys.argv
if len(argv) >=2 and argv[1] :
    port = int(argv[1])

reactor.listenTCP(port,RichFactory())
reactor.run()
