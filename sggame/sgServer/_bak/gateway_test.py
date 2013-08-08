# -*- coding:utf-8 -*-
from gevent import monkey; monkey.patch_all() #必须，且放到最前，去掉就变了单线线 协程堵塞 
import gc
gc.disable()

from os.path import dirname,abspath
system_root = dirname(dirname( abspath( __file__ ) ) ) #定义上层目录为根目录 
import sys;sys.path.insert(0,system_root)  #把项目根目录加入默认库路径 
import sgCfg.config as Cfg

import signal

from optparse import OptionParser
import os

parser = OptionParser()
parser.add_option('-p', '--pid-file', action='store', dest='pid_file',
                                    help='保存该进程的PID的文件')
option, args = parser.parse_args()

pid_file = option.pid_file
if pid_file:
    pid_file = abspath( __file__ )+'.pid'
    with open(pid_file, 'wb') as fd:
        fd.write(str(os.getpid()))

from sgLib.setting import Setting

if args:
    port = args[0]
    Setting.setGatewayPort(port)
    if len(args) >= 2:
        Setting.setDatabase('gamesg%s'%args[1])
else:
    port = Cfg.CFG_GATEWAYSERV_PORT



#python gateway.py 8084 2 开启2服  - 8084端口  数据库 gamesg2 (可省)
#python gateway.py 8086 3 开启3服  - 8086端口  数据库 gamesg3 (未开)


#== START CONTENT START ==
import time
import gevent.pool
import message


import sgLib.common as comm

from sgLib.core import Gcore
from sgLib.proManager import proManager
from CLogin import Login

from sgz import Server, Application

class Service(object):
    
    def __init__(self): 
        #self.validate = Validate()
        self.Clients = {} #所有用户信息库
        Gcore.objCfg.loadAllCfg() #读取所有配置
        Gcore.IsServer = True #定义为服务器核心
        
        Gcore.startNotice() #开启公告自动发布协程
        
    def handle(self, channel, request):

#        print '='*90
#        comm.trace('<font color=green>Echo at Port 8888</font>')
#        print request
        ckey = channel.getpeername()
        
        recData = comm.decodePacket(request) #(协议号，内容)
        if not recData: #参数异常
            channel._send("xxxx Wu ask send xxxx") 
            return 
        
        if not ckey in self.Clients:
            self.Clients[ckey] = {}
            self.Clients[ckey]['uid'] = 0 
            self.Clients[ckey]['Channel'] = channel
        
        if Cfg.TEST: #获取开发人员指定用户ID
            uid_tmp = Setting.developer(ckey[0]) 
            if uid_tmp:
                self.Clients[ckey]['uid'] = uid_tmp
                #print 'get developer uid',uid_tmp
                
        self.checkOpt(ckey, recData[0], recData[1], recData[2])
        
    def checkOpt(self,ckey,optId,optKey,para):

        if optId == 888888:
            result = Gcore.reload()
            print 'Gcore.reload()'
            msg = '<font color=green>Reload Success!</font>' if result is True else "<font color=red>"+str(result)+"</font>"
            response = Gcore.out(optId,{'Result':msg})
            self.Send(ckey,response)
        elif 10001<=optId<=10005: #帐户相关: 10001登录,10002创建帐号,10003随机姓名,10004推荐阵营,10005检查帐户名是否合法
            self.checkLogin(ckey,optId,optKey,para)
        else:
            if optId == 8888: #测试
                #print 'Gcore.getDB(uid)>',Gcore.getDB(uid)
                self.mqPush(ckey,optId,optKey,para)
            else:
                uid = self.Clients[ckey]['uid']
                if uid==0:
                    response = Gcore.error(optId,-88888888) 
                    self.Send(ckey,response) 
                    print 'Please login first'
                    return
                response = proManager.checkOpt(uid, optId, para)
                if type(response) is not dict:
                    #print 'type(response)',type(response),response
                    response = Gcore.error(optId,-33333333) #协议号未定义 或返回出错
                    
                response['opt_key'] = optKey
                self.Send(ckey,response)

    def checkLogin(self,ckey,optId,optKey,para):
        """登录验证"""
        from sgLib.pyMcrypt import TokenDecode
        response = None
        
        #tokenDict: {u'TotalServiceId': u'42', u'LoginMode': 2, u'PlayerId': 0, u'LoginVersion': 101, u'Lan': 1, u'LockTime': 1367994093}
        tokenDict = {}
        if not self.Clients[ckey]['uid']:
            try:
                objToken = TokenDecode()
                tokenDict = objToken.getTokenMsg(para.get("pyKey"))
                print 'tokenDict > ',tokenDict
                para.update(tokenDict)
    
            except Exception,e:
                response = Gcore.error(optId,-10001003,{'Error':str(e)}) #登录验证失败
        
        if tokenDict or self.Clients[ckey]['uid']:
            uid = self.Clients[ckey]['uid']
            if uid:
                para['uid'] = uid
            elif tokenDict.get('PlayerId'):
                para['uid'] = tokenDict.get('PlayerId')
                del para['PlayerId'] 
            
            c = Login()
            if optId == 10001: 
                Result = c.LoginAccount(para)
            elif optId == 10002:
                Result = c.CreateRole(para)
                
            elif optId == 10003:#随机昵称
                resp = c.randomName(para)
                resp['opt_key'] = optKey
                self.Send(ckey,resp)
                return 
            
            elif optId == 10004:#推荐阵营
                resp = c.getRecCamp(optId)
                resp['opt_key'] = optKey
                self.Send(ckey,resp)
                return 
            
            elif optId==10005:#验证昵称合法性
                resp = c.checkNickNameValid(para)
                resp['opt_key'] = optKey
                self.Send(ckey,resp)
                return 
            
            if isinstance(Result,dict): 
                UserData = Result
                uid = UserData.get('UserId')
                if ckey not in self.Clients:
                    response = Gcore.error(optId,0)
                else:
                    self.Clients[ckey]['uid'] = uid
                    Gcore.setUserData(uid, {'Channel':self.Clients[ckey]['Channel']}) #储存用户channel
                    Gcore.onlineUser[uid] = 1
                    print ' ----------  Logined,uid=',uid
                    
                    loginIp = ckey[0]#登录IP
                    loginModel = tokenDict.get('LoginMode',0)#登录方式0:开发者
                    
                    Gcore.getMod('Login', uid).login(loginIp,loginModel)
                    response = Gcore.out(optId,UserData)
            else:
                if Result<0: #错误编号
                    response = Gcore.error(optId,Result)
                        
        if not response:
            response = Gcore.error(optId,0)
        response['opt_key'] = optKey
        #print 'response',response
        self.Send(ckey,response) #验证失败



    def Send(self,ckey,sendData):
        try:
            self.Clients[ckey]['Channel']._send( comm.json_encode(sendData) ) #abu已经有做打包的操作 不用重复操作
        except Exception,e:
            '''用户可能已经下线'''
            pass
            
    def SendAll(self, sendData):
        '''发送给所有人'''

    def new_connection(self, server, channel):
        msg = '%s has a new connection:%s' % (server, channel.peername)
        comm.trace(msg)

    def lost_connection(self, server, channel):
        ckey = channel.peername #自改abu为channel加上此属性,因socket已不可用,不能getpeername
        msg = 'lost a connection:%s' % str(ckey)
        comm.trace(msg)
        if ckey in self.Clients:
            try: #清空些用户的资料 
                uid = self.Clients[ckey]['uid']
                if uid:
                    Gcore.getMod('Login', uid).logout() #更新
                    Gcore.onlineUser.pop(uid,None) #用户落线
                    Gcore.delUserStorage(uid)
            except Exception,e:
                print 'lost_connection >> ',e
            self.Clients.pop(ckey) 
    
    def mqPush(self,ckey,optId,optKey,para):
        '''来自mqReceiver的消息,告诉玩家正在被打'''
        #print ' in mqPush',para
        Users = para.get('UserId')
        Type = para.get('Type')
        Data = para.get('Data',{})
        Gcore.push(105, Users, Data, Type)
    
def main():    
    _pool = gevent.pool.Pool()
    service = Service()
    
    server = Server(('0.0.0.0', int(port)), handle=service.handle, spawn=_pool.spawn)
    def close_server():
        #server.kill()
        server.stop(180)
        print 'server.stop'

    def start_server():
        if server.started:
            print '服务器已经启动'
            return 
        server.start()
        print 'server.start'
        
    def hook_signal(): 
        '''捕获信号'''
        if os.name == 'nt':
            return
        #信号10-开服
        gevent.signal(signal.SIGUSR1, start_server)
        #信号12-关服
        gevent.signal(signal.SIGUSR2, close_server)

    message.sub(Server.NEW_CONNECTION, service.new_connection)
    message.sub(Server.LOST_CONNECTION, service.lost_connection)
    app = Application(server)
    
    hook_signal()
    print '=' * 50
    print '=', ' '*15, 'Server Started', ' '*15, '='
    print '=' * 50

    app.run()

if __name__ == '__main__':
    main()
