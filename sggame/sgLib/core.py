#-*-coding:utf-8-*-  
#author:Lizr
#date:2012-12-21
#modi:2012-5-22
#游戏核心类
'''服务器核心方法说明:
常用属性：
Gcore.config  #模块 sgCfg.config
Gcore.defined #模块 sgLib.defined
Gcore.common  #模块 sgLib.common
Gcore.Coord   #静态类 sgLib.coord.Coord

常用方法：
Gcore.out()     #正确返回数据时使用
Gcore.error()   #错误返回数据时使用 
Gcore.getServerId() #获取本服ID
Gcore.getNewDB()    #返回用户0的一个数据库操作对象 = getDB(0) note:多人共用没有问题 DB()线程安全
Gcore.getDB()  #已改为单例
Gcore.getUI()  #获取UI
Gcore.getMod() #获取模型

#配置相关
Gcore.loadCfg(9001) #获取tb_config配置的缓存数据
Gcore.loadCoreCfg('CrossServer') #获取tb_config_core配置的缓存数据
Gcore.getCfg(table,key=None,field=None)  #获取tb_cfg_*配置表的缓存数据

#消息相关
Gcore.redisL  #本地redis对象 继承于redis.Redis 详细见sgLib/pyRedis.py
Gcore.redisM  #总服redis对象 同上
Gcore.redisKey(UserId)   #返回本服用户redis的键 e.g. 1.1008
Gcore.getRedis(ServerId) #根据传入的服务器ID 判断该返回 Gcore.redisL还是Gcore.redisM
Gcore.IsLocal(ServerId) #根据传入的服务器ID 判断是否本服
Gcore.push()   #推送时使用  sgLib/pyPusher.py
Gcore.sendmq() #推送消息 具体查看 sgLib/pyRabbit.py 
(MQ的接收见：sgServer/mqReceiver.py | sgLib/mqManager.py | )

#日志相关
Gcore.sqldelay() #延迟运行sql, 将所有日志，交给一个协程和一个数据库连接处理 
Gcore.log  #系统默认logger
Gcore.getLoger(tag,filename) #获取独立的logger

#用户资料缓存
Gcore.setUserData() #设置或更新缓存
Gcore.getUserData() #获取缓存


#调试相关
Gcore.TEST      #开发1 测试2  真网0
Gcore.IsServer  #是否为服务器模式
Gcore.echo()    #打印调试输出
Gcore.printd()  #打印好看的json格式，调试使用
Gcore.resetRuntime() #重置开始时间
Gcore.runtime() #显示运行时间，调试使用
'''

from gevent import monkey; monkey.patch_all() #必须要，去掉就变了单线线 协程堵塞 
import sys; reload(sys); sys.setdefaultencoding('utf8') #确认服务器所有编码

import gevent
import time

import sgCfg.config
import sgLib.defined 
import sgLib.common
import sgLib.coord

class Gcore(object):
    TEST = False #读 sgCfg.config.TEST
    started = None
    startedRedis = None
    startedRabbit = None
    startedNotice = None
    
    pool = None
    con = None
    log = None #系统默认的loger

    redisL = None #本地redis
    redisM = None #总服redis
    #chan = None #RabbitMQ channel对象保存
    
    config = None #将配置模块也放到核心
    defined = None #将定义模块也放到核心
    common = None #将common模块也放到核心
    Coord = None #将coord.Coord静态类也放到核心
    
    objCfg = None #表里面的配置
    objPush = None #推送对象
    objLogger = None #日志中心对象
    
    dictMod = {} #所有模型类列表
    dictUI = {} #所有UI类列表
    
    StorageListener = {} #聊天监听管理员
     
    StorageUser = {} #记录在线用户资料，包括channel等信息
    StorageCfg = {} #tb_config里面的配置
    StorageCoreCfg = {} #tb_config_core里面的配置
    
    StorageDB  = {} #用户的连接对象,一用户一个
    StorageUI = {} #用户调用过的所有UI
    StorageMod = {} #用户调用过的所有模型
        
    IsServer = False #是否socket服务器中调用
    objDB = None #所有人共用一个DB()
    onlineUser = {} #在线用户，在线用户才缓存对象
    
    @staticmethod
    def start():
        '''游戏核心开始启动'''
        if not Gcore.started:
            print '-----Gcore.start-----'
            from pyDB import DB
            Gcore.objDB = DB()
            
            Gcore.started = True
            Gcore.starttime = time.time()
            
            Gcore.TEST = sgCfg.config.TEST
            #from pyDB import DBPool
            #Gcore.pool = DBPool()
            
            Gcore.objCfg = Gconfig() #表里面的配置
            Gcore.objCfg.load_tb_config() #将tb_config的所有数据读到 StorageCfg
            Gcore.Coord = sgLib.coord.Coord #将静态类也放到核心
            #Gcore.objCfg.loadAllCfg() #将所有配置表内容读入内存
            
            from sgLib.pyPusher import Pusher
            Gcore.objPush = Pusher()
            
            from sgLib.pyLogger import DbLogger
            Gcore.objLogger = DbLogger()
            gevent.spawn(Gcore.objLogger.loop)
            
            from sgDebug.logger import Logger
            Gcore.log = Logger('system')
    
            gevent.spawn(Gcore.gcClearLoop)
            
            Gcore.importMod() #引入常用模块 config defined common
            
            if Gcore.IsServer: #引入模块太多需要1s,调试时太慢
                Gcore.makeUIDict() #组成所有UI字典
                Gcore.makeModDict() #组成所有模型字典
    
            Gcore.startRedis()  #开始Redis
            Gcore.startRabbit() #开始Rabbit
            
            
            #Gcore.runtime()
            print '-----end Gcore.start -----'
    
    @staticmethod
    def resetRuntime():
        '''重置开始时间'''
        Gcore.starttime = time.time()
        
    @staticmethod
    def startRabbit():
        return  #暂不开始rabbit
        if not Gcore.startedRabbit:
            from sgLib.pyRabbit import Rabbit
            Gcore.rabbit = Rabbit()
            Gcore.rabbit.start()
            gevent.spawn(Gcore.rabbit.loop)
            Gcore.startedRabbit = True
    
    @staticmethod
    def startNotice():
        '''开始公告发布'''
        if not Gcore.startedNotice:
            from sgLib.pySystem import SystemNotice
            gevent.spawn( SystemNotice().loop )
            Gcore.startedNotice = True
        
    @staticmethod
    def sendmq(optId, toServerId, para={}):
        '''本服发送给各服的消息
        toServerId:10000是总服  
        optId: 总服 ( 1更新攻城用户信息  2插入创建用户信息资料 )  分服请查看sgLib/mqManager.py
        '''
        return  #暂不开始rabbit
        #print type(toServerId),toServerId
        msg = {}
        msg['optId'] = int(optId)
        msg['toServerId'] = int(toServerId)
        msg['fromServerId'] = int(Gcore.getServerId())
        msg['para'] = para
        print ' --> Gcore.sendmq',msg
        Gcore.rabbit.put(msg)
    
    @staticmethod
    def sqldelay(sql):
        '''sql延迟插入 用于日志,在pyDB.DB()调用,也可独立调用'''
        Gcore.objLogger.put(sql)
        
    @staticmethod
    def startRedis():
        '''连接Redis服务器'''
        if not Gcore.startedRedis:
            from sgLib.pyRedis import MyRedis
            #连到本服
            #print 'connect redisL',Gcore.config.REDISL_HOST,Gcore.config.REDISL_PORT
            Gcore.redisL = MyRedis(host=Gcore.config.REDISL_HOST, 
                                   port=Gcore.config.REDISL_PORT,
                                   password=Gcore.config.REDISL_PWD)
            Gcore.redisL.start('redisL')
            gevent.spawn(Gcore.redisL.loop)
            
            if Gcore.config.REDISL_HOST != Gcore.config.REDISM_HOST and Gcore.loadCoreCfg('CrossServer')!='0':
                #连到总服
                print '连到总服redis...'
                #print 'connect redisM',Gcore.config.REDISM_HOST,Gcore.config.REDISM_PORT
                Gcore.redisM = MyRedis(host=Gcore.config.REDISM_HOST, 
                                       port=Gcore.config.REDISM_PORT, 
                                       password=Gcore.config.REDISM_PWD)
                Gcore.redisM.start('redisM')
                gevent.spawn(Gcore.redisM.loop)
            else:
                Gcore.redisM = Gcore.redisL
            
            if 0:
                print 'redisL',Gcore.redisL.get('foo')
                print 'redisM',Gcore.redisM.get('foo')
            Gcore.startedRedis = True
        
        
    @staticmethod
    def reload():
        '''热更新： 重新加载游戏配置和模型'''
        try:
            import ModLib
            reload(ModLib)
            ModLib.modReload()
            Gcore.importMod() #重新引入模块
            Gcore.makeUIDict() #重组UI
            Gcore.makeModDict() #重组模型
            return True
        except Exception,e:
            print 'Reload Fail',e
            return False
        finally:
            Gcore.objCfg.load_tb_config() #重载tb_config配置
            Gcore.objCfg.loadAllCfg()     #重载tb_cfg_* 配置
    
    
    @staticmethod
    def makeUIDict():
        '''组成UI字典'''
        from ModLib import getDictUI
        Gcore.dictUI = getDictUI()
        
    @staticmethod        
    def makeModDict():
        '''组成模型字典'''
        from ModLib import getDictMod
        Gcore.dictMod = getDictMod()

    @staticmethod
    def importMod():
        '''引入模块'''
        Gcore.config = sgCfg.config
        Gcore.defined = sgLib.defined
        Gcore.common = sgLib.common
    
    @staticmethod
    def runtime():
        '''计算运行时间'''
        runtime = round(time.time() - Gcore.starttime,3)
        print '------------ Gcore runtime > ',runtime,'------------ '
    
    @staticmethod
    def push(pushId, Users, Data={}, Type=0):
        '''推送给客户端  
        @param pushId: 协议号 101~999
        @param Users: 要推送的用户 int or list or 空(例 发送给全服人，某军团内部等)
        @param Data: 推送的内容  或者 逻辑需要的数据 (例 发送给某军团内部时 需要军团ID)
        @param Type: 类型  一个协议号或者有多种类型  (例 通知全军团人 事件1或事件2)
        '''
        pushId = int(pushId)
        Gcore.objPush.push( pushId, Users, Data, Type)

    @staticmethod
    def out(optId, body={}, mission={},achieve={}, broadcast={}):
        '''正确时返回,参考output'''
        data={}
        data['flag']= 1
        data['retime']=int(time.time())
        data['opt_id']=int(optId)
        if body:
            data['body']=body
        
        #触发任务记录   
        if mission:
            uid = mission.get('uid')
            if uid:
                missionMod = Gcore.getMod('Mission', uid)
                missionMod.missionTrigger(optId,mission)
                
                activityMod=Gcore.getMod('Activity',uid)
                activityMod.actionTrigger(optId,mission)
                
                Gcore.getMod('Event',uid).OptId2MyEvent(optId,mission)
        
        #触发成就记录   
        if achieve:
            uid = achieve.get('uid')
            if uid:
                achieveMod = Gcore.getMod('Building_home', uid)
                achieveMod.achieveTrigger(optId,achieve)
           
        if Gcore.TEST and not Gcore.IsServer:
            print "Gcore.out %s >> "%optId
            Gcore.printd(data)
            Gcore.runtime()
        return data
       
    @staticmethod
    def error(optId,message,body={}):
        '''错误时返回,参考output'''
        from lang_message import lang
        data={}
        data['flag']=2
        data['opt_id']=int(optId)
        data['retime']=int(time.time())
        if type(message) is list or type(message) is tuple:
            message = message[0]
        if type(message) is str:
            message = int(message)
        if message>0:
            message*=-1
        endNum = (message*-1)%1000
        if endNum>=900:
            messagekey = endNum
        else:
            messagekey = message
        msg = lang.get(messagekey,None)
        #if Gcore.TEST and msg:
        #    print 'Gcore.error.message > ',message,msg
        data['message']={message:msg}
        if body:
            data['body']=body
        
        if Gcore.TEST and not Gcore.IsServer:
            print "Gcore.out %s >> "%optId
            Gcore.printd(data)
        return data
        
    @staticmethod
    def loadCfg(CfgKey):
        '''读取tb_config的配置'''
        assert type(CfgKey) is int
        if CfgKey in Gcore.StorageCfg:
            return  Gcore.StorageCfg[CfgKey]
        else:
            return None 
    
    @staticmethod
    def loadCoreCfg(CoreKey):
        '''读取tb_config_core的配置'''
        if CoreKey in Gcore.StorageCoreCfg:
            return  Gcore.StorageCoreCfg[CoreKey]
        else:
            return None 
    
    @staticmethod
    def getCfg(*a,**kw):
        '''读取配置表tb_cfg_*中的数据'''
        return Gcore.objCfg.getCfg(*a,**kw)
    
    @staticmethod
    def getRedis(serverId):
        '''获取Redis对象本服还是总服'''
        if int(serverId) == Gcore.getServerId():
            return Gcore.redisL
        else:
            return Gcore.redisM
    
    @staticmethod
    def redisKey(UserId):
        '''获取用户Redis的键值 e.g. return 1.1008'''
        return '%s.%s'%(Gcore.getServerId(),UserId)
    
    @staticmethod
    def IsLocal(ServerId):
        '''判断是否本服'''
        return Gcore.getServerId() == int(ServerId)
    
    @staticmethod
    def getServerId():
        '''获取当前服务器ID'''
        #return int( Gcore.loadCoreCfg('ServerId') )  #弃用
        return int(sgCfg.config.CFG_SERVER_ID)
        
    @staticmethod
    def getUI(UIname,uid):
        '''获取UI类'''
        if UIname in Gcore.dictUI:   
            classUI = Gcore.dictUI.get(UIname)
        else: #add by Lizr 0424
            #print 'pass  Gcore.getUI.exec'
            exec("from sgMod.%sUI import %sUI"%(UIname,UIname))
            exec("classUI = %sUI"%UIname)
        
        if uid not in Gcore.onlineUser: #非在线用户就不缓存对象
            return classUI(uid)
        
        if uid not in Gcore.StorageUI:
            Gcore.StorageUI[uid] = {}
            
        #Gcore.StorageUI[uid] = classUI(uid)
        #return Gcore.StorageUI[uid]
    
        if not isinstance(Gcore.StorageUI[uid].get(UIname),classUI): #如果重载 将不是它的实例 所以会清缓存
            Gcore.StorageUI[uid][UIname] = classUI(uid)
        UI = Gcore.StorageUI[uid][UIname]
        return UI
    
    @staticmethod
    def getMod(classMod,uid,noCache=False):
        '''将用户创建过的Mod，缓存
        @param classMod 模块名称去Mod 
        @example  getMod('Map',uid)  调用MapMod
        @note 调用其他用户的模型时不能缓存，避免其他用户模型长驻在内存 (需全局检查) (战斗例外，战斗完的时候清除对方缓存)
        @todo 应该做成在线用户的模型才缓存!!!
        '''
        assert uid!=0
        assert type(classMod) is str
        classModName = classMod
        if classMod in Gcore.dictMod:
            classMod = Gcore.dictMod.get(classMod)
        else:
            try:
                if classMod.startswith('Building_'):
                    command = "from sgMod.subMod.building.%sMod import %sMod"%(classMod,classMod)
                else:
                    command = "from sgMod.subMod.%sMod import %sMod"%(classMod,classMod)
                #print 'command >> ',command
                exec(command)
            except ImportError:
                print 'error command >> ',command
                raise 
    
            exec("classMod = %sMod"%classMod)
            
            Gcore.dictMod[classModName] = classMod
        
        if uid not in Gcore.onlineUser or noCache: #非在线用户就不缓存对象
            return classMod(uid)
            
        try:
            ModName = classMod.__name__
        except AttributeError:
            raise AttributeError, 'in Gcore.getMod %s not exist' % classModName
        if uid not in Gcore.StorageMod:
            Gcore.StorageMod[uid] = {}
        
        if not isinstance(Gcore.StorageMod[uid].get(ModName),classMod): #如果重载 将不是它的实例 所以会清缓存

            Gcore.StorageMod[uid][ModName] = classMod(uid)
        Mod = Gcore.StorageMod[uid][ModName]
        return Mod

    @staticmethod
    def getNewDB():
        '''拿连接对象'''
        return Gcore.getDB(0) #暂时的先用同一个
    
    @staticmethod
    def getDB(uid=0): 
        '''按用户ID缓存数据库操作对象   -> 已改做成单例'''
        return Gcore.objDB
    
#        if uid not in Gcore.StorageDB:
#            from pyDB import DB
#            Gcore.StorageDB[uid] = DB()
#        
#        return Gcore.StorageDB[uid]
            
    @staticmethod
    def printd(demoDictList):
        '''调试 方法:将字典打印出漂亮的缩进格式 @note:整形的键值会变成字符型'''
        import json
        #demoDictList is the value we want format to output
        jsonDumpsIndentStr = json.dumps(demoDictList, indent=1, ensure_ascii=False)
        print jsonDumpsIndentStr
    
    @staticmethod
    def echo(*a,**kw):
        '''调试打印方法:真网不会输出
        @例子: 
        echo = Gcore.echo  
        uid = 1001
        d = {'t':1,'c':2}
        echo(uid)
        echo(uid,d)
        echo(uid=uid,d=d)
        '''
        if Gcore.TEST:
            if a:
                for b in a:
                    print 'echo >>',b
            if kw:
                for k,v in kw.iteritems():
                    print 'echo >> %s = %s'%(k,v)
        
    @staticmethod
    def setListenerData(ckey,Channel,listenChannel):
        '''储存监听者信息
         Channel:socket客户端的渠道,
         listenChannel:监听频道 0全部, 1世界, 2势力, 3军团, 4私聊, 5系统, 6喇叭
        '''
        if ckey not in Gcore.StorageListener:
            Gcore.StorageListener[ckey] = {}
        
        Gcore.StorageListener[ckey]['Channel'] = Channel
        Gcore.StorageListener[ckey]['ListenChannel'] = listenChannel
    
    @staticmethod
    def delListenerStorage(ckey):
        '''清除监听者信息'''
        if ckey in Gcore.StorageListener:
            del Gcore.StorageListener[ckey]
        
    @staticmethod
    def setUserData(uid,DataDict):
        '''储存用户数据,包括channel，成就，任务等完成状态等'''
        #print >>sys.stderr, 'setUserData', uid,DataDict
        if uid not in Gcore.StorageUser:
            Gcore.StorageUser[uid] = {}
        
        for k,v in DataDict.iteritems():
            Gcore.StorageUser[uid][k] = v
            
    @staticmethod
    def getUserData(uid,key):
        '''获取用户数据,包括channel，成就，任务等完成状态等'''
        if uid not in Gcore.StorageUser:
            Gcore.getMod('Login', uid).cacheUserData()
        try:
            return Gcore.StorageUser[uid].get(key)
        except:
            print 'error accurs'
            return None
            
    @staticmethod
    def delUserStorage(uid):
        '''将用户创建的对象删除，断socket的时候调用'''
        
        if uid in Gcore.StorageUI:
            del Gcore.StorageUI[uid]
            
        if uid in Gcore.StorageMod:
            del Gcore.StorageMod[uid]
        
#        if uid in Gcore.StorageDB:
#            del Gcore.StorageDB[uid]
            
        if uid in Gcore.StorageUser:
            del Gcore.StorageUser[uid]
    
    @staticmethod
    def gcClearLoop():
        '''内存回收 每天4:00~4:59之间运行一次'''
        import gc
        while True:
            if time.strftime('%H',time.localtime()) == '4': 
                print '>> gc cleared!'
                gc.enable()
                gc.collect()
                gc.disable()
            gevent.sleep(3600) #每小时计一次时
    
    
    @staticmethod
    def getLogger(tag,filename=''):
        '''获取新的独立的Logger,系统公用的用Gcore.log
        @param tag: 日志标签
        @param filename: 日志文件名 {$filename}.log
        @e.g. 
        :系统公用:  Gcore.log.debug|info|warning|error|critical('hi')  
        :独立使用:  log = Gcore.getLogger('mytag','myfile'); log.debug|info|warning|error|critical('hi')  
        @note 日志文件将统一存放于sgDebug/log 格式 s1.2013-07-20.log 或 s1.2013-07-20.xx.log
        @remark 真网warning以上会输出
        '''
        assert tag!='system'
        from sgDebug.logger import Logger
        return Logger(tag, filename, 50)
        
        
class Gconfig(object):
    """游戏配置储存类"""
    dictCfg = {}
    def __init__(self):
        ''' '''
    
    def load_tb_config(self):
        '''读取tb_config'''
        import json
        db = Gcore.getNewDB()
        #读取游戏配置
        sql = "SELECT CfgKey,CfgValue FROM tb_config WHERE 1"
        rows = db.query(sql)
        for row in rows:
            CfgKey = row.get('CfgKey')
            CfgValue = row.get('CfgValue')
            
            try:
                CfgDict = json.loads(CfgValue)
            except:
                CfgDict = {}
            Gcore.StorageCfg[CfgKey] = CfgDict
        
        #读取核心配置
        sql = "SELECT CoreKey,CoreValue FROM tb_config_core WHERE 1"
        rows = db.query(sql)
        for row in rows:
            CoreKey = row.get('CoreKey')
            CoreValue = row.get('CoreValue')
            
            Gcore.StorageCoreCfg[CoreKey] = CoreValue

        
    def _combineRows(self,table,rows):
        '''
        :特殊定制配置
        @param table:表名
        @param rows:表内数据
        @return: 没有特需定制的返回False
        '''
        rowsCombine = {}
        if table == 'tb_cfg_building_up':
            for row in rows:
                #if Gcore.TEST and row['CDValue']>0: #调试暂用 将CD时间统一改为1秒
                #    row['CDValue'] = 1
                key = (row['BuildingType'],row['Level'])
                rowsCombine[key] = row
                             
        elif table == 'tb_cfg_altar_land':  #地坛抽奖配置
            for row in rows:
                key = row['LandAwardType']
                if key not in rowsCombine: #配置有点特别，把相同LandAwardType存在一个列表
                    rowsCombine[key] = []
                rowsCombine[key].append(row)   
        
        elif table == 'tb_cfg_altar_sky':   #天坛抽奖配置
            for row in rows:
                key = row['SkyAwardType']
                if key not in rowsCombine: #配置有点特别，把相同SkyAwardType存在一个列表
                    rowsCombine[key] = []
                rowsCombine[key].append(row)   
                
        elif table == 'tb_cfg_club_box':   #军团宝箱奖励配置
            for row in rows:
                key = row['BoxType']
                if key not in rowsCombine: #配置有点特别，把相同SkyAwardType存在一个列表
                    rowsCombine[key] = []
                rowsCombine[key].append(row)
                
        elif table == 'tb_cfg_achieve':#成就配置
            for row in rows:
                key = row['AchieveType']
                scdKey = row['AchieveStepId']
                if key not in rowsCombine:
                    rowsCombine[key] = {}
                rowsCombine[key][scdKey] = row 
                
        elif table == 'tb_cfg_pve_drop':#战役奖励配置表
            for row in rows:
                key = (row['DropId'],row['Star'])
                #del row['DropId']
                #del row['Star']
                if key not in rowsCombine: #配置有点特别，把相同掉落ID和星级 存在一个列表
                    rowsCombine[key] = []
                rowsCombine[key].append(row)     
        
        elif table == 'tb_cfg_act_online_award':  #在线奖励
            for row in rows:
                key = (row['TypeId'],row['Level'])
                if key not in rowsCombine: #配置有点特别，把相同类型ID和奖励 存在一个列表
                    rowsCombine[key] = []
                rowsCombine[key].append(row)   
        
        elif table == 'tb_cfg_nickname': #随机姓名表        
            for row in rows:
                if not row['Active']:
                    continue
                key = row['Type']
                if key not in rowsCombine: #配置有点特别，把相同掉落ID和星级 存在一个列表
                    rowsCombine[key] = []
                rowsCombine[key].append(row['Content'])
                
        elif table == 'tb_cfg_item_box':
            for row in rows:
                key = row['ItemBoxType']
                if key not in rowsCombine: #配置有点特别，把相同SkyAwardType存在一个列表
                    rowsCombine[key] = []
                rowsCombine[key].append(row)
                    
        else:
            return False                 
        return rowsCombine
        
    def loadAllCfg(self,tables=None):
        '''读取所有配置'''
        db = Gcore.getNewDB()
        if tables is None:#查询所有配置表
            cfgs = db.fetchall("SHOW tables LIKE %s",('tb_cfg_%',))
            tables = []
            for t in cfgs:
                tables = tables+t.values()
        if type(tables) is not list and type(tables) is not tuple:
            tables = [tables]         
        for table in tables:
            rows = db.query("SELECT * FROM `"+table+"` WHERE 1")
            ks = db.query('DESCRIBE %s'%table)
            keys = [k['Field'] for k in ks if k['Key']=='PRI']#查询主键
            rowsCombine = self._combineRows(table, rows)#生成特殊定制的配置       
            if rowsCombine:
                self.dictCfg[table] = rowsCombine
            else:#没有特殊定制默认生成
                newRows = {}
                for row in rows:
                    size = len(keys)
                    if size == 1:
                        key = row[keys[0]]
                    elif size == 2:
                        key = (row[keys[0]],row[keys[1]])
                    newRows[key] = row
                self.dictCfg[table] = newRows
        db.close()
        
    def getCfg(self,table,key=None,field=None):
        if table not in self.dictCfg:
            self.loadAllCfg(table) #如没有数据重新读取
        try:
            row = self.dictCfg[table]
            if key is not None:
                row = row.get(key,None)
                if field:
                    row = row.get(field,None)
            return row
        except:
            return None
    
def inspector(optId, keys=[]):
    '''检查参数的装饰器
    @param：
        optId：功能号
        keys：验证传入字典键
    '''
    if not isinstance(optId, int):
        optId = int(optId)
    def _inspector(fun):
        def _inspector(point,p={}):
            if isinstance(p,dict):
                for k in keys:
                    if k not in p:
                        return Gcore.error(optId,optId*-1000-999)
                if 'ClientTime' not in p:
                    p['ClientTime'] = int(time.time())
            else:
                return Gcore.error(optId,optId*-1000-999)
            return fun(point,p)
        return _inspector
    return _inspector

if __name__ == '__main__':
    print '注意:本页面不支持调试,因会交叉引用,可到sgMod/ExampleUI.py里试'
    import sys
    sys.exit()
else:
    if not Gcore.started:
        print '>>> Gcore go start' 
        Gcore.start()
    else:
        print '>>> Gcore already started' 


    
