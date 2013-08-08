#coding:utf8
#author:zhoujingjiang
#date:2013-5-9
#PVP服务器

from gevent import monkey; monkey.patch_all()
import sys; reload(sys); sys.setdefaultencoding('utf8')

import signal
import os
import time

import gevent
from gevent.pool import Pool
import message
from sgz import Server, Application

from core import Gcore; Gcore.start() #开启核心
import common
import config
import McryptMod

#服务器ip，端口
ADDR = (config.SERVER_IP, config.SERVER_PORT)

print '进程ID：', os.getpid()
print '服务器socket：', ADDR

#绑定信号处理函数
gevent.signal(signal.SIGUSR1, Gcore.arena_start) #开启竞技场
gevent.signal(signal.SIGUSR2, Gcore.arena_end) #关闭竞技场

class Service(object):
    def __init__(self):
        self.channels = {} #缓存channel - uid 对应关系
        self.clients = {} #缓存用户信息
        Gcore.clients = self.clients #把引用传给Gcore
    
    def handle(self, channel, request):
        recData = common.decodePacket(request)
        if not recData: #不合法的消息
            print '收到一个不合法的请求'
            print request
            return False # + 断开连接

        if recData[0] in self.channels[channel]['process']: #进程列表中已有该进程
            res = {'opt_key':recData[1], 'opt_id':recData[0],'flag':2}
            return common.encodePacket(res)
        
        self.channels[channel]['process'].add(recData[0]) #添加进程
        
        print '所有的channel信息', self.channels
        print '收到来自%s的请求' % str(channel.peername)
        print recData
        
        res = self.checkOpt(channel, recData[0], recData[1], recData[2])
        
        print '对该请求的处理结果是'
        print res
        
        self.channels[channel]['process'].remove(recData[0]) #移除进程
        
        if res in [False, None]: #False 断开连接  None 不回复客户端消息
            return res
        else:
            return common.encodePacket(res)

    def checkOpt(self, channel, optId, optKey, para):
        '''协议号处理'''
        if optId == 10001: #登陆
            try:
                tokenStr = para['tokenStr']
                tokenDic = McryptMod.getTokenMsg(tokenStr)
                uid, sid = map(int, [tokenDic['UserId'], tokenDic['ServerId']])
                print '%d服%d玩家已登陆' % (sid, uid)
            except Exception:
                print channel.peername, '登陆失败。断开channel。'
                return False
            self.clients[(uid, sid)] = {}
            self.clients[(uid, sid)]['channel'] = channel
            self.channels[channel]['user'] = (uid, sid)
            
            #登陆成功
            res = {'opt_key':optKey, 'opt_id':optId, 
                   'body':{"UserId":uid, "ServerId":sid}, 'flag':1}
            return res
        else: #非登陆
            uid, sid = self.channels.get(channel, {}).get('user', (None, None))
            if uid is None and sid is None: #没有登陆
                return False #断开channel
            res = Gcore.pro_manager(uid, sid, optId, para)
            if isinstance(res, dict): #是字典
                res['opt_key'] = optKey
            return res
    
    def new_connection(self, server, channel):
        print '来自%s的新连接' % (channel.peername, )
        
        self.channels[channel] = {}
        self.channels[channel]['connect_time'] = time.time() #连接时间
        self.channels[channel]['process'] = set() #该连接的进程

    def lost_connection(self, server, channel):
        print '失去来自%s的连接' % (channel.peername, )
        if channel in self.channels:
            user = self.channels.pop(channel).get('user')
            if user is not None:
                print '%d服%d玩家下线' % user
                del self.clients[user]
            
                Gcore.log_out(user[0], user[1]) #下线处理

def main():
    _pool = Pool()
    service = Service()
    server = Server(listener=ADDR, handle=service.handle, spawn=_pool.spawn)
    app = Application(server)

    message.sub(Server.NEW_CONNECTION, service.new_connection)
    message.sub(Server.LOST_CONNECTION, service.lost_connection)
    
    print '=' * 50
    print '=', ' '*15, 'Server Started', ' '*15, '='
    print '=' * 50

    app.run()

if __name__ == '__main__':
    main()