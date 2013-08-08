# -*- coding:utf-8 -*-
from gevent import monkey; monkey.patch_all() #必须要，去掉就变了单线线 协程堵塞 
import gc
gc.disable()

import os
from os.path import dirname,abspath,basename
system_root = dirname(dirname( abspath( __file__ ) ) ) #定义上层目录为根目录 
import sys;sys.path.insert(0,system_root)  #把项目根目录加入默认库路径 

import time

import gevent.pool
import message

import sgCfg.config as Cfg
import sgLib.common as comm

from sgLib.core import Gcore
from sgLib.pyDB import DBPool
from sgLib.proManager import proManager


from CBattle import CBattleManager
from CLogin import Login

from sgz import Server, Application

#python gateway.py 8084 2 开启2服  - 8084端口  数据库 gamesg2 (可省)
#python gateway.py 8086 3 开启3服  - 8086端口  数据库 gamesg3 (未开)

#======================= START CONTENT START ================================
from sgLib.setting import Setting
port = 0
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
    pass

pid_file = ''
if not port: #没有自定义端口才是用脚本运行
    filename = basename(__file__)
    pid_file = dirname( abspath( __file__ ) )+'/pid/'+filename[0:len(filename)-3]+'.pid'
    print 'pid_file',pid_file
    with open(pid_file, 'wb') as fd:
        fd.write(str(os.getpid()))

class Service(object):
    
    def __init__(self): 
        print 'EchoService.__init__'
        self.BM = CBattleManager()

        self.Clients = {} #所有用户信息库
        Gcore.IsServer = True #定义为服务器核心

    def handle(self, channel, request):
        #print 'ps '+ str(Cfg.CFG_BATTLESERV_PORT)+' Echo',request
        recData = comm.decodePacket(request) #(协议号，内容)
        if not recData: #参数异常
            channel._send("xxxx Wu ask send xxxx")
            return
        ckey = channel.getpeername()

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
        #print 'checkOpt',ckey,optId,optKey,para
        response = False
        strExcept = ''
        if optId == 888888:
            Gcore.reload()
            response = Gcore.out(optId,{'Result':'Reload Success!'})
            self.Send(ckey,response) 
            print 'Gcore.reload()'
        elif optId == 10001: #登录
            self.checkLogin(ckey,optId,optKey,para)
        else:
            startTime = time.time()
            
            try:
                uid = self.Clients[ckey]['uid']
                if uid==0:
                    #self.Clients[ckey]['Channel'].close() #关闭socket连接
                    response = Gcore.error(optId,-88888888) #未登录
                    
                elif optId>90000 and optId<=90999: #开始战役
                    if optId == 90001: #开启战斗
                        response = self.BM.createWar(uid,para) 
                    else:
                        response = self.BM.doBattle(uid, optId, para) #暂未使用
                        
                elif optId>91000 and optId<=91999: #战役信息(开始战役战斗前)
                    response = proManager.checkOpt(uid, optId, para)
                    
                elif optId>93000 and optId<=93999: #攻城
                    if optId == 93001: #攻城入口
                        response = self.BM.findSiege(uid,para) #para: {storyBattleId:1} 任务战斗id
                    elif optId == 93002: #开始攻城
                        response = self.BM.startSiege(uid,para) 
                    elif optId == 93003: #离开攻城
                        response = self.BM.leftSiege(uid,para) 
                    elif optId == 93004: #同步  PVE PVC PVG
                        response = self.BM.synBattle(uid,para) 
                    elif optId == 93009: #结束战斗
                        response = self.BM.endBattle(uid,para) 
                    else:
                        response = self.BM.doWBattle(uid, optId, para)
                elif optId>94000 and optId<=94999: #比武
                    if optId == 94001: #开启比武
                        response = self.BM.createRankFight(uid,para) 
                else:
                    response = Gcore.error(optId,-33333333) #协议号未定义 
            except Exception,e: #错误日志
                try:
                    import traceback
                    strExcept = traceback.format_exc()
                    print >>sys.stderr, 'Time:' + time.strftime('%Y-%m-%d %H:%M:%S') + '\n' \
                            + 'UserId:' + str(uid) + '\n' \
                            + 'OptId:' + str(optId) + '\n' \
                            + 'Para:' + str(para) + '\n' \
                            + strExcept
                    sys.stderr.flush()
                except:
                    pass
                
                strExcept = ' >> '+str(e)
                response = False
            finally:
                try: #调试日志
                    optInfo = {
                       93001:'createWar',
                       93001:'findSiege',
                       93002:'startSiege',
                       93003:'leftSiege',
                       93009:'endBattle',
                       }
                    if uid and optId and optId!=93004:
                        runtime = time.time() - startTime
                        db = Gcore.getNewDB()
                        row = {
                                 'UserId':uid,
                                 'OptId':optId,
                                 'CallMethod':optInfo.get(optId,'--'),
                                 'Param':Gcore.common.json_encode(para),
                                 'Response':Gcore.common.json_encode(response),
                                 'Runtime':runtime,
                                 'RecordTime':Gcore.common.datetime(),
                                 }
                        print row
                        db.insert('temp_runtime_log', row, isdelay=True)
                except Exception,e:
                    print 'Exception in battleway',e
                
            if type(response) is not dict and response is False: #None就是不返回
                try:
                    import traceback
                    strExcept = traceback.format_exc()
                    print >>sys.stderr, 'Time:' + time.strftime('%Y-%m-%d %H:%M:%S') + '\n' \
                            + 'UserId:' + str(uid) + '\n' \
                            + 'OptId:' + str(optId) + '\n' \
                            + 'Para:' + str(para) + '\n' \
                            + strExcept
                    sys.stderr.flush()
                except:
                    
                    pass
                
                response = Gcore.error(optId,-22222222,{'Exception':strExcept}) #程序运行错误
            #发送
            if type(response) is dict:
                response['opt_key'] = optKey
                self.Send(ckey,response)
            

    def checkLogin(self,ckey,optId,optKey,para):
        """登录验证，不同于城市场景的登录"""
        from sgLib.pyMcrypt import TokenDecode
        
        #tokenDict: {u'TotalServiceId': u'42', u'LoginMode': 2, u'PlayerId': 0, u'LoginVersion': 101, u'Lan': 1, u'LockTime': 1367994093}
        response = None
        try:
            objToken = TokenDecode()
            tokenDict = objToken.getTokenMsg(para.get("pyKey"))
            print 'tokenDict > ',tokenDict
            if not self.Clients[ckey]['uid']:
                c = Login()
                uid = c.getUserIdByAccount(tokenDict.get('TotalServiceId'))
                self.Clients[ckey]['uid'] = uid
                print 'Player %s logined'%self.Clients[ckey]['uid']
            else:
                print 'Developer %s logined'%self.Clients[ckey]['uid']
            
            uid = self.Clients[ckey]['uid']
            Gcore.onlineUser[uid] = 1
            
            response = Gcore.out(optId,{'ServerTime':time.time()})
            #Gcore.setUserData(uid, {'Channel':self.Clients[ckey]['Channel']}) #储存用户channel 推送需要
        except Exception:
            pass
        
        if not response:
            response = Gcore.error(optId,-10001003) #登录验证失败
        
        response['opt_key'] = optKey
        self.Send(ckey,response) 


    def Send(self,ckey,sendData):
        try:
            self.Clients[ckey]['Channel']._send( comm.json_encode(sendData) ) #abu已经有做打包的操作 不用重复操作
        except Exception,e:
            print 'Send Exception',e
            
    def SendAll(self, sendData):
        '''发送给所有人'''

    def new_connection(self, server, channel):
        print '%s has a new connection:%s' % (server, channel.peername)

    def lost_connection(self, server, channel):
        ckey = channel.peername #自改abu为channel加上此属性,因socket已不可用,不能getpeername
        print 'lost a connection:%s' % str(ckey)
        if ckey in self.Clients:
            try:
                uid = self.Clients[ckey]['uid']
                self.BM.destoryBattle(uid) #删除战斗
                Gcore.onlineUser.pop(uid,None)
                Gcore.delUserStorage(uid)
            except Exception,e:
                print e
            finally:
                self.Clients.pop(ckey)

              
def main():
    port  = Setting.getGatewayPort()
    if not port:
        port = Cfg.CFG_BATTLESERV_PORT

    _pool = gevent.pool.Pool()
    service = Service()
    server = Server(('0.0.0.0', int(port) ), handle=service.handle, spawn=_pool.spawn)
    #===========================================================
    import signal
    logger = Gcore.getLogger('server', 'server')
    def close_server():
        logger.warning('I got a signal.SIGUSR1 going to stop server')
        server.stop(180)

    def reload_server():
        Gcore.reload()
        logger.warning('I got a signal.SIGUSR2, Gcore reload()')
        
    def hook_signal(): 
        '''捕获信号'''
        if os.name == 'nt':
            return
        #信号10-关服
        gevent.signal(signal.SIGUSR1, close_server)
        #信号12-重载
        gevent.signal(signal.SIGUSR2, reload_server)
        
    hook_signal()
    #=====================================================================
    message.sub(Server.NEW_CONNECTION, service.new_connection)
    message.sub(Server.LOST_CONNECTION, service.lost_connection)
    app = Application(server)
    
    print '=' * 50
    print '=', ' '*15, 'Server Started', ' '*15, '='
    print '=' * 50

    app.run()
    
    if pid_file:
        with open(pid_file, 'wb') as fd:
            fd.write('0')
            

if __name__ == '__main__':
    main()

