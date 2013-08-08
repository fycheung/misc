# -*- coding:utf-8 -*-
from gevent import monkey; monkey.patch_all() #必须，且放到最前，去掉就变了单线线 协程堵塞 
import gc
gc.disable()
import os
from os.path import dirname,abspath,basename
system_root = dirname(dirname( abspath( __file__ ) ) ) #定义上层目录为根目录 
import sys;sys.path.insert(0,system_root)  #把项目根目录加入默认库路径 
from optparse import OptionParser

import time
import gevent.pool
import message

import sgCfg.config as Cfg
import sgLib.common as comm

from sgLib.core import Gcore
from sgLib.proManager import proManager
from CLogin import Login

from sgz import Server, Application


#== START CONTENT START ==
#parser = OptionParser()
#parser.add_option('-p', '--pid-file', action='store', dest='pid_file',
#                                    help='保存该进程的PID的文件')
#option, args = parser.parse_args()
#pid_file = option.pid_file #pid文件名

filename = basename(__file__)

pid_file = dirname( abspath( __file__ ) )+'/pid/'+filename[0:len(filename)-3]+'.pid'
print 'pid_file',pid_file
with open(pid_file, 'wb') as fd:
    fd.write(str(os.getpid()))
        
#python gateway.py 8084 2 开启2服  - 8084端口  数据库 gamesg2 (可省)
#python gateway.py 8086 3 开启3服  - 8086端口  数据库 gamesg3 (未开)

from sgLib.setting import Setting
try:
    if len(sys.argv)>1:
        port = int(sys.argv[1])
        Setting.setGatewayPort(port)
        if len(sys.argv)>2:
            database = 'gamesg%s'%sys.argv[2]
            Setting.setDatabase(database)
except Exception, e:
    if Gcore.TEST:
        raise
    print e
    pass
class Service(object):
    
    def __init__(self): 
        #self.validate = Validate()
        self.Clients = {} #所有用户信息库
        Gcore.objCfg.loadAllCfg() #读取所有配置
        Gcore.IsServer = True #定义为服务器核心
        
        Gcore.startNotice() #开启公告自动发布协程
        
    def handle(self, channel, request):

        ckey = channel.getpeername()
        
        recData = comm.decodePacket(request) #(协议号，内容)
        if not recData: #参数异常
            channel._send("xxxx Wu ask send xxxx") 
            return 
        
        if not ckey in self.Clients:
            self.Clients[ckey] = {}
            self.Clients[ckey]['uid'] = 0 
            self.Clients[ckey]['Channel'] = channel

        optId = recData[0]
        optKey = recData[1]
        para = recData[2]
        
        if 1001<=optId<=9999: #系统内部预留
            if optId == 1001: #聊天监控
                from sgLib.pyMcrypt import checkListenKey
                if checkListenKey(para.get('keyWord')):
                    print '聊天接入成功'
                    Gcore.setListenerData(ckey, channel, para.get('chatChannel'))
                    response = Gcore.out(1001)
                    channel._send( comm.json_encode(response) )
                else:
                    print '聊天接入失败'
                    
                
        else:
            if Cfg.TEST: #获取开发人员指定用户ID
                uid_tmp = Setting.developer(ckey[0]) 
                if uid_tmp:
                    self.Clients[ckey]['uid'] = uid_tmp
                  
            self.checkOpt(ckey, optId, optKey, para)
        
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
                if uid > 0:
                    Gcore.getMod('Login', uid).logout() #更新
                    Gcore.onlineUser.pop(uid,None) #用户落线
                Gcore.delUserStorage(uid)
            except Exception,e:
                print 'lost_connection >> ',e
            self.Clients.pop(ckey,None) 
            
        Gcore.delListenerStorage(ckey) #如果是监听者就清除
    
    def mqPush(self,ckey,optId,optKey,para):
        '''来自mqReceiver的消息,告诉玩家正在被打'''
        #print ' in mqPush',para
        Users = para.get('UserId')
        Type = para.get('Type')
        Data = para.get('Data',{})
        Gcore.push(105, Users, Data, Type)
        


        
def main():
    
    port  = Setting.getGatewayPort()
    if not port:
        port = Cfg.CFG_GATEWAYSERV_PORT

    _pool = gevent.pool.Pool()
    service = Service()
    server = Server(('0.0.0.0', int(8088)), handle=service.handle, spawn=_pool.spawn)
    #===========================================================
    import signal
    #对linux一些信号进行捕获
    def hook_signal():
        if os.name != "nt":
            signal.signal(signal.SIGBUS,signal_handle)
            signal.signal(signal.SIGTERM, signal_handle)
            signal.signal(signal.SIGUSR1, signal_handle)
            signal.signal(signal.SIGUSR2, signal_handle)
            signal.signal(signal.SIGABRT, signal_handle)
            #屏蔽与终端控制有关的信号
            signal.signal(signal.SIGTTOU,signal.SIG_IGN)
            signal.signal(signal.SIGTTIN,signal.SIG_IGN)
            signal.signal(signal.SIGTSTP,signal.SIG_IGN)
            signal.signal(signal.SIGHUP ,signal.SIG_IGN)
            
    #linux信号处理函数
    def signal_handle(sign_num, frame):
        import signal
        logger = Gcore.getLogger('system', 'server')
        if sign_num == signal.SIGBUS:
            server.stop(180)
            logger.warning('I got a signal.SIGBUS server stop')
            sys.exit(-1)
        elif sign_num == signal.SIGTERM:
            server.stop(180)
            logger.warning('I got a signal.SIGTERM server stop')
        elif sign_num == signal.SIGHUP:
            logger.warning('I got a signal.SIGHUP pass')
            pass
        elif sign_num == signal.SIGUSR1:  #用户发送停止服务的指令  10
            logger.warning('I got a signal.SIGUSR1 going to  stop server')
            server.stop(180)
        elif sign_num == signal.SIGUSR2: # 12
            Gcore.reload()
            logger.warning('I got a signal.SIGUSR2, Gcore reload()')
        
    hook_signal()
    #=====================================================================
    message.sub(Server.NEW_CONNECTION, service.new_connection)
    message.sub(Server.LOST_CONNECTION, service.lost_connection)
    app = Application(server)
    
    print '=' * 50
    print '=', ' '*15, 'Server Started', ' '*15, '='
    print '=' * 50
    app.run()
    
    Gcore.log.warning('I got a signal.SIGUSR1 have stoped server')
    if pid_file:
        with open(pid_file, 'wb') as fd:
            fd.write('0')
    

if __name__ == '__main__':
    main()
