# -*- coding:utf-8 -*-
# author:Lizr
# date:2013年2月28日
# 战斗模型
from __future__ import division
import time
import copy
import math
import json
import random
import gevent
from gevent import Timeout
from sgLib.core import Gcore
from sgLib.base import Base
from sgLib.FightOver import FightOver
from sgLib.formula import Formula
from sgLib.pyRedis import redisLock,redisUnlock

Coord = Gcore.Coord
F = Formula

class BattleMod(Base):
    '''战斗模型,数据来源'''
    def __init__(self, uid):
        ''' '''
        print '构造BattleMod'
        Base.__init__(self,uid)
        self.uid = uid
        self.OpUserId = 0 #比武对手的用户ID
        self.battleType = 0 #1PVE战役   2PVC攻城   3PVG比武
        self.TotalNpc = 5 #最多NPC数量 
        self.WarId = 0 #本场战役ID
        self.MapId = 0 #本场战役的地图ID
        self.LandForm = 0 #本场战役 地型: 0无 1水 2陆 3山 4城
        self.armyNum = 0 #军队数量
        self.armyNumMy = 0 #我方军队数量
        self.armyNumEnemy = 0 #敌方军队数量
        
        self.grabCoin = {} #攻城可掠夺资源
        
        #print 'in CBattleMod',self.db
        self.CfgWar = None #战场基本配置
        self.CfgMap = None #战场地图配置
        self.CfgPve = None #PVE配置
        self.CfgPveReward = None #PVE奖励配置
        
        self.homeTotalLife = 0 #我方军队总血量
        self.enemyTotalLife = 0 #敌方军队总血量 (如果是攻城包括防御工事)
        
        self.homeAvgDefense = 0 #我方防御平均数
        self.enemyAvgDefense = 0 #我方防御平均数
        self.ClubTechAdd = {} #获取军团科技
        
        self.DefenseInfo = {} #防御工事
        self.DchangeList = [] #变化过的防御工事
        
        self.MyArmy = {} #我的军队 
        self.EnemyArmy = {} #敌方军队 
        
        self.startTime = time.time() #战斗开始时间
        
        self.MyBastion ={} #我方基地
        self.EnemyBastion = {} #敌方基地
        
        self.RewardGet = {} #获奖信息
        
        self.IsSweep = False #是否扫荡
        self.fromType = 1  #攻城战来源类型   1查找  2复仇 3反抗 4抢夺
        
        self.fightList = [] #攻打对象列表
        self.fightUnit = [] #正选中的对象 - 观察中
        self.fightUser = {} #攻打对象的用户信息
        self.fightProcess = 0 #攻城进度 0~1
        
        self.foundTarget = False #攻城是否已匹配到对象 ，匹配到才能开始，才能继续,防挂 
        self.canWar = True #是否可进行战役
        
        self.UserData = None #我的用户信息
        
        self.BattleReportId = None #反击时的战报ID
        
        self.defeaterSID = None  #抢夺时使用，手下败将的服务器ID
        self.defeaterUID = None  #抢夺时使用，手下败将的用户ID
        
        self.SiegeStarted = False #是否开始了攻城
        self.BattleEnd = False #是否已经结束过战斗
        
        self.lockState = 0 #是否有锁到人
        self.MyTroops = {} #我的出兵 {类型:数量,}
        
    def _checkWar(self,WarId):
        '''检查战役是否可以挑战 和有效战役'''
        
        if self.ProcessWarId==0:
            self.ProcessWarId = 101
        result = self.ProcessWarId>=WarId and WarId in Gcore.getCfg('tb_cfg_pve').keys()
        return result
    
    def _checkGeneralSoldier(self):
        '''检查是否有上阵且带兵的武将'''
        result = bool( self.db.count(self.tb_general(),"UserId=%s AND PosId>0 AND TakeNum>0"%self.uid) )
        print '_checkGeneralSoldier > ',self.db.sql
        print 'result',result
        return result
    
    def initWar(self,WarId,IsSweep=False):
        '''初始化战役  战役ID 0为攻城'''
        self.WarId = WarId
        self.IsSweep = IsSweep 
        self.CfgWar = Gcore.loadCfg( Gcore.defined.CFG_BATTLE ) #获取战场基本配置
        self.battleType = 1 if WarId else 2
        
        if not self._checkGeneralSoldier():
            self.canWar = False
            return -1  #'还没有布阵，不能攻城'
           
        if WarId:
            UserData = self.getUserInfo(['ProcessWarId','DialogWarId','UserLevel'])
            RestPoint,MaxPoint = Gcore.getMod('War',self.uid).getActPoint()
            if not RestPoint:
                self.canWar = False
                return -2   #'没有行动力'
            
            self.ProcessWarId = UserData['ProcessWarId']
            self.DialogWarId = UserData['DialogWarId']
            
            if not self._checkWar(WarId):
                self.canWar = False
                return -3 #战役未达到
                
            self.CfgPve  = Gcore.getCfg('tb_cfg_pve',WarId)
            self.CfgPveReward  = Gcore.getCfg('tb_cfg_pve_reward',WarId)
            self.MapId = self.CfgPve.get('MapId')
            
            self.updateDialogWar() #更新已对话的最大战役ID
            self.ClubTechAdd = {5:1,6:1,7:1,8:1,9:1,10:1} #战役没有加成
        else:
            UserData = self.getUserInfo(['ProtectEndTime','UserLevel'])
            self.MapId = 0
            self.LandForm = 4 #地型攻城
            self.ClubTechAdd = Gcore.getMod('Building_club',self.uid).getClubTechAdd() #攻城才有加成
            if UserData['UserLevel']<Gcore.loadCfg(9301).get('FightLevel'): 
                return -4 #未达可攻城等级
        
        self.UserData = UserData
        self.CfgMap = Gcore.getCfg('tb_cfg_pve_map',self.MapId)
        self.canWar = True
        return 1
    
    def initRankFight(self,OpUserId):
        '''初始化排名'''
        self.canWar = False
        self.battleType = 3
        if not self._checkGeneralSoldier():
            return -1  #还没有布阵，不能攻城
        elif not Gcore.getMod('RankFight',self.uid).checkCanFight(): 
            return -2  #超出可比武上限
        elif OpUserId == self.uid: 
            return -3  #不可与自己比武
        else:
            
            self.LandForm = 5 #不算地型影响
            self.ClubTechAdd = {5:1,6:1,7:1,8:1,9:1,10:1} #战役没有加成
            self.canWar = True
            self.OpUserId = OpUserId
            return 1
    
    def updateDialogWar(self):
        '''更新已对话的最大战役ID'''
        if self.DialogWarId < self.WarId:
            sql = "UPDATE tb_user SET DialogWarId = %s WHERE DialogWarId<%s AND UserId=%s"%(self.WarId,self.WarId,self.uid)
            print 'updateDialogWar',sql
            self.db.execute(sql)
    
    def disMyProtect(self):
        '''取消我的保护'''
        nowtime = Gcore.common.nowtime()
        if nowtime < self.UserData['ProtectEndTime']:
            self.db.update('tb_user',{'ProtectEndTime':nowtime},"UserId=%s"%self.uid)
            key = Gcore.redisKey(self.uid)
            Gcore.redisM.hset('sgProtect',key,nowtime)
    
    def synBattle(self,para={}):
        '''战斗同步'''
        if self.battleType == 2 and not self.foundTarget:
            return -93004001 #
        elif self.battleType == 1 and not self.canWar:
            return -93004002 #
        
        if para.get('SynA'): #同步军队血量
            for k,v in para['SynA'].iteritems():
                k = int(k)
                if k<200: #我军
                    if k in self.MyArmy:
                        self.MyArmy[k]['cur_armyLife'] = v
                elif k<300: #敌军
                    if k in self.EnemyArmy:
                        self.EnemyArmy[k]['cur_armyLife'] = v
                    #print 'set self.EnemyArmy',k,v
        
        if para.get('SynB'): #同步基地血量
            for k,v in para['SynB'].iteritems():
                k = int(k)
                if k == 10001: #我方基地
                    self.MyBastion[k]['cur_bastionLife'] = v
                elif k == 10002: #敌方基地
                    self.EnemyBastion[k]['cur_bastionLife'] = v
        
        if para.get('SynD'): #同步防御工事血量比例
            for k,v in para['SynD'].iteritems():
                if k in self.DefenseInfo:
                    self.DefenseInfo[k]['cur_LifeRatio'] = float(v)
                    if k not in self.DchangeList:
                        self.DchangeList.append(k) #变化过的防御工事 
                    
    #========================================= 攻城 START ==========================================
    def findSiege(self,para={}): #
        '''查找攻城战斗  
        @param fromType': 1, #1查找 2反击 3反抗 4抢夺  (defaut 1)
        @param targetServerId': 0, #1查找时不需要
        @param targetUserId':  0,  #1查找时不需要
        @param BattleReportId : 0,   #反击时才有,
        @param defeaterSID: 0, #抢夺需要 手下败将的服务器ID
        @param defeaterUID: 0, #抢夺需要 手下败将的用户ID
         '''
        print '----------------at findSiege-------------',para
        self.enemyTotalLife = 0 #初始化敌军血量
        
        print self,'self.lockState',self.lockState
        if para.get('fromType'):
            self.fromType = para.get('fromType')
        if self.fromType == 2:
            self.BattleReportId = para.get('BattleReportId')
        elif self.fromType == 4: #抢夺
            self.defeaterSID = para.get('defeaterSID')
            self.defeaterUID = para.get('defeaterUID')
            
        targetUserId = para.get('targetUserId')
        redisM = Gcore.redisM
        rowUser = None
        objRedis = None
        
        
        seconds = Gcore.loadCfg(9301).get('LongestFindTime',15)
        if Gcore.TEST:
            seconds = 8
        try:
            if targetUserId:
                targetServerId =  para.get('targetServerId')
                self.fightList = [ (targetServerId,targetUserId) ]
                print 'fight target > ',self.fightList
                if Gcore.TEST and self.uid==1001 and 0: #自己调试用 
                    key = '%s.%s'%(targetServerId,targetUserId)
                    redisUnlock(key)
                    Gcore.redisM.hset('sgProtect',key,0)
                    gevent.sleep(0.3)
                
            nowtime = int(time.time())
            firstTime = True
            with Timeout(seconds):
                while True:
                    if not self.fightList:
                        if not firstTime: #非第一次就等3秒
                            gevent.sleep(2)
                        else:
                            firstTime = False
                        self.fightList = Gcore.getMod('War',self.uid).findPvcTarget() #如果无了继续查
                        if not self.fightList:
                            continue
                    
                    if Gcore.TEST and self.uid==1001 and False: #测试 指定攻打
                        self.fightList=[[1,43912]]
                    print 'fightList >>',self.fightList
                    unit =  self.fightList.pop()
                    print 'pop a unit',unit
                    if self.fightUnit and self.lockState: #解锁上一次的查找
                        print '查找下一个，解锁上一个'
                        serverId,UserId = self.fightUnit
                        key = '%s.%s'%(serverId,UserId)
                        redisUnlock(key)
                        
                    self.fightUnit = unit
                    serverId,UserId = unit
                    key = '%s.%s'%(serverId,UserId)
                    if key == Gcore.redisKey(self.uid): #不能攻打自己 
                        if targetUserId:
                            return -93001002 #不可攻打自己
                            break
                        else:
                            continue
                    #----------------测试不锁-----------------
#                    if True and Gcore.TEST and self.uid in (1001,43577):  # self.uid in (1001,1011)
#                        objRedis = Gcore.getRedis(serverId)
#                        rowUser = objRedis.hget('sgUser',key,True)
#                        break
                    #-----------------------------------------
                    LoginState = redisM.hget('sgLogin',key)
                    if LoginState:
                        print '%s is online...'%key
                        if targetUserId:
                            return -93001004 #目标当前在线，不能攻打
                            break
                        else:
                            continue 
                    
                    ProtectEndTime = redisM.hget('sgProtect',key)
                    if ProtectEndTime is None:
                        ProtectEndTime =0
                    else:
                        ProtectEndTime = int(ProtectEndTime)
                    if ProtectEndTime>nowtime and self.fromType!=3: #反抗 不管保护
                        print '%s is protecting until %s'%(key,Gcore.common.now(ProtectEndTime))
                        if targetUserId:
                            return -93001005 #目标当前处于保护中，不能攻打
                            break 
                        else:
                            continue
                    else:
                        self.lockState = redisLock(key)
                        if not self.lockState: # and not Gcore.TEST
                            print '%s is locking continue'%key
                            if targetUserId:
                                return -93001006 #锁定目标失败，请稍后再试
                                break
                            else:
                                continue
                        
                        objRedis = Gcore.getRedis(serverId)
                        rowUser = objRedis.hget('sgUser',key,True)
                        if rowUser:
                            break
                        else:
                            print '%s not found sgUser in redis'%key
                            if targetUserId:
                                return -93001007 #获取用户信息失败，请稍后再试
                                break
                            else:
                                continue
        except Timeout:
            print ' >> Could not found target in %s s...'%seconds
            return -93001003 #无匹配对象，请稍后再试
    
        if not rowUser or not objRedis or not key:
            print 'found no target to fight!'
            return -93001007 #获取匹配玩家失败，请稍后再试
        else:
            if self.fromType!=3:
                self.disMyProtect() #非反抗  ,去掉保护,我的保护时间设为现在
            self.fightUnit = unit
            self.foundTarget = True
            
        UserId = rowUser['UserId']
        if self.fromType==3: #反抗不给资源
            rowCoin = {'Jcoin':0,'Gcoin':0}
        else:
            rowCoin = objRedis.hget('sgCoin',key,True)  
            PredictOut = objRedis.hget('sgPredictOut',key,True) #1小时预产量
            print 'get redis sgCoin %s'%key, rowCoin
            print 'get redis PredictOut %s'%key, PredictOut
           
            rowCoin['Jcoin'] = F.calBaseResource( rowCoin.get('Jcoin',0),PredictOut.get('2',0) )
            rowCoin['Gcoin'] = F.calBaseResource( rowCoin.get('Gcoin',0),PredictOut.get('3',0) )
            
        self.grabCoin = rowCoin
        rowUser.update(rowCoin)
        
        levelDif = self.getUserLevel()-rowUser['UserLevel']
        #最大级差
        if levelDif>75:
            levelDif = 75
        elif levelDif<-75:
            levelDif = -75
            
        rowUser['HonourWin'] = Gcore.getCfg('tb_cfg_honour',levelDif,'Honour')
        rowUser['HonourLost'] = Gcore.getCfg('tb_cfg_honour',levelDif*-1,'Honour') * Gcore.loadCfg(9301).get('SiegeFailHounerCut')
        
        if not rowUser['HonourWin']:
            rowUser['HonourWin'] = 0
        if not rowUser['HonourLost']:
            rowUser['HonourLost'] = 0
        
        if self.fromType==3: #反抗不给荣誉
            rowUser['HonourWin'] = 0
            rowUser['HonourLost'] = 0
            
        data = {}  
        data['bRevengeRatio'] = F.bRevengeRatio #基地反伤比例   @todo要区分基地和城墙2个配置
        data['bLifeRatio'] = F.bLifeRatio #基地血量比例   @todo要区分基地和城墙2个配置
        
        DefenseInfo =  objRedis.hget('sgDefense',key,True)  
        self.DefenseInfo = DefenseInfo
       
        for k in self.DefenseInfo:
            row = self.DefenseInfo[k]
            Life = Gcore.getCfg('tb_cfg_soldier_up',(row['SoldierType'],row['SoldierLevel']),'Life')
            self.enemyTotalLife += Life * row.get('LifeRatio')
            
            ttt = Life * row.get('LifeRatio')
            print 'self.enemyTotalLife+=',ttt
        
        #print 'DefenseInfo',DefenseInfo
        data['DefenseInfo'] = DefenseInfo
        data['TrapInfo'] = objRedis.hget('sgTrap',key,True) 
        
        data['UserInfo'] = rowUser
        self.fightUser = rowUser
        data['armyInfo'] = self.getSiegeArmy(serverId,UserId,objRedis,key )
        data['armyNumEnemy'] = self.armyNumEnemy #敌方军队总数量
        data['bastionInfo'] = self.getEnemyBastion()  #基地 城墙
        data['ServerTime'] = int(time.time())
        data['CanFind'] = 1 if self.fromType == 1 else 0 #是否可以继续查找
        
        return data
    
    def startSiege(self):
        '''开始攻城战斗'''
        if not self.foundTarget:
            return -93002001
        else:
            self.SiegeStarted = True
        if self.fromType == 2:
            sql = "UPDATE tb_battle_report SET Revenge=0 WHERE BattleReportId='%s' AND UserId='%s'"%(self.BattleReportId,self.uid)
            print '反击一次',sql
            self.db.execute(sql)
            
        ServerId,UserId = self.fightUnit
        Fighter = self.getUserInfo('NickName')
        if Gcore.IsLocal(ServerId):
            Gcore.getMod('Player', self.uid).beFighting(Fighter,UserId)
        else:
            Gcore.sendmq(4, ServerId, {'UserId':UserId,'Fighter':Fighter}) #发送消息攻打中
        data = {}
        data['armyInfo'] = self.getMyArmy( 0 )
        data['armyNumMy'] = self.armyNumMy #敌方军队总数量
        data['ServerTime'] = int(time.time())
        return data
    
        
    def leftSiege(self):
        '''离开攻城回城  @note 如不解锁 将要等到解死锁'''
        print 'leftSiege',leftSiege
        serverId,UserId = self.fightUnit
        key = '%s.%s'%(serverId,UserId)
        redisUnlock(key) #解锁
        
    #========================================= 攻城 END ==========================================
    def getWarInfo(self):
        '''获取剧情战场信息'''
        if not self.canWar:
            return {}
        WarId = self.WarId
        data = {}

        data['warId'] = WarId #战役ID
        data['mapId'] = self.MapId #地图背景 
        
        CfgPve  = Gcore.getCfg('tb_cfg_pve',WarId)
        MapId = CfgPve.get('MapId')
        
        data['armyInfo'] = copy.deepcopy( self.getEnemyArmy() ) #添加敌方军队
        data['armyInfo'].update( self.getMyArmy( MapId ) ) #我的军队
        data['bastionInfo'] = self.getEnemyBastion() 
        data['bastionInfo'].update(self.getMyBastion() ) #基地
        data['armyNum'] = self.armyNum #军队总数量
        data['dialog'] = 1 if self.WarId > self.DialogWarId else 0
        data['ServerTime'] = time.time()
        data['ShowNpcId'] = self.CfgPve.get('NpcId1')
        
        return data
    
    def getRankInfo(self,):
        '''获取排名战战场信息'''
        if not self.canWar:
            return {}
        
        OpUserId = self.OpUserId
        data = {}
        
        self.OpUserId = OpUserId
        MapId = random.choice(Gcore.loadCfg(Gcore.defined.CFG_RANK_FIGHT).get('RandMapIdList')) #地图背景 
        data['mapId'] = MapId
        
        data['armyInfo'] = copy.deepcopy( self.getOpArmy(MapId,OpUserId) ) 
        data['armyInfo'].update( self.getMyArmy( MapId ) ) 

        data['armyNum'] = self.armyNum #军队总数量
        Gcore.getMod('RankFight',self.uid).updateFightTimes() #更新比武次数
        return data
    
    def getMyBastion(self):
        '''获取我方基地信息'''
        CfgMap = self.CfgMap
        MyBastion={}
        initBasetionLife = F.initBastionLife
        initBasetionDefense = F.initBastionDefense
        bastionLife = initBasetionLife + self.homeTotalLife * F.bLifeRatio #我方基地血量
        bastionDefense = initBasetionDefense+self.homeAvgDefense
        MyBastion[10001] = {
                     'armyId':10001,  #基地ID
                     'armyType':1, #军队类型: 1自己  2敌军
                     'bastionX' :CfgMap['HomePointX'], #我方军队基地坐标X
                     'bastionY' :CfgMap['HomePointY'], #我方军队基地坐标Y 
                     'bastionLife' : bastionLife, #我方基地血量
                     'bastionDefense': bastionDefense, #我方基地防御
                     'cur_bastionLife': bastionLife, #当前我方基地血量
                     }
        self.MyBastion = MyBastion
        return MyBastion
        
    
        
    def getEnemyBastion(self):
        '''获取敌方基地信息'''
        CfgMap = self.CfgMap
        EnemyBastion = {}
        armyType = 3 if self.WarId  else 2 #军队类型:  1友军  2敌军  3NPC
        initBasetionLife = F.initBastionLife
        initBasetionDefense = F.initBastionDefense
        
        bastionDefense = initBasetionDefense+self.enemyAvgDefense
        bastionLife = initBasetionLife + self.enemyTotalLife * F.bLifeRatio #敌方基地血量
        self.enemyTotalLife += bastionLife
        print '获取对方基地的血',bastionLife
        print '敌军总血量 self.enemyTotalLife', self.enemyTotalLife
        EnemyBastion[10002] = {
                     'armyId':10002,  #基地ID
                     'armyType':armyType, #军队类型: 1自己  2敌军
                     'bastionX' :CfgMap['EnemyPointX'], #敌方军队基地坐标X
                     'bastionY' :CfgMap['EnemyPointY'], #敌方军队基地坐标Y 
                     'bastionLife' : bastionLife, #敌方基地血量
                     'bastionDefense': bastionDefense, #我方基地防御
                     'cur_bastionLife': bastionLife, #当前敌方基地血量
                     }
        self.EnemyBastion = EnemyBastion
        return EnemyBastion
    
    def getSiegeArmy(self,serverId,UserId,objRedis,key):
        '''将布防武将信息变更为军队信息'''
        EnemyArmy = {}
        print 'getSiegeArmy(),key:',key
        generalRows = objRedis.hget('sgGeneralOnDefense',key,True)
        SoldiersTech = objRedis.hget('sgTech',key,True)
        if not generalRows:
            return {}
        
        SumDefense = 0
        kLeader  = Gcore.loadCfg(Gcore.defined.CFG_BATTLE)["kLeaderAddNum"]
        armyId = 200 #敌方军队从201开始
        for k,row in generalRows.iteritems():
            armyId += 1
            SoldierType = row['TakeTypeDefense'] if row['TakeTypeDefense'] else 1
            SoldierNum = row['LeaderValue']*kLeader
            SoldierLevel = SoldiersTech.get(SoldierType,0)
            GeneralId = row['GeneralId']
            
            row_soldier = Gcore.getCfg('tb_cfg_soldier',SoldierType)
            row_soldier_up = Gcore.getCfg('tb_cfg_soldier_up',(SoldierType,SoldierLevel))
            
            SoldierLife = row_soldier_up['Life']
            army = {}
            army['armyId'] = armyId
            army['armyUserId'] = '%s.%s'%(serverId,UserId) 
            army['armyType'] = 2  #军队类型: 1友军 2敌军 3NPC
            
            #army['__armySizeL'] = 3 #军队尺寸的长
            #army['__armySizeW'] = 3 #军队尺寸的宽
            #army['armyLife'] = SoldierLife * (SoldierNum** F.HP_mi)  #军队的生命
            army['armyLife'] = F.getArmyLife(SoldierLife, SoldierNum)  #军队的生命
            army['cur_armyLife'] = army['armyLife'] #当前军队生命 战斗中减少
            
            #按校场布阵 地图9宫格而定
            army['initPointX'] = row['x']  #初始位置X
            army['initPointY'] = row['y']  #初始位置Y
                
            army['generalType'] = row['GeneralType']   #武将技能种类 , 军队需要显示武将的名称 来源于武将类型配置
            army['generalLevel'] = row['GeneralLevel'] #武将技能等级
            
            SkillId = Gcore.getCfg('tb_cfg_general',row['GeneralType'],'SkillId') #武将技能ID 暂定每个武将只有一个技能
            if SkillId:
                Chance = F.calSkillChance(SkillId,row['WitValue'])
                army['SkillDict'] = Gcore.common.gen01Dict(Chance,SkillId) 
            else:
                army['SkillDict'] = {}
            army['generalForce'] = row['ForceValue'] 
            army['generalWit'] = row['WitValue']  
            army['generalSpeed'] = row['SpeedValue']  
            army['generalLeader'] = row['LeaderValue']  
            
            army['soldierType'] = SoldierType
            #army['__soldierSort'] = row_soldier['SoldierSort'] #分类 步弓骑
            army['soldierLevel'] = SoldierLevel
            #army['__soldierLife'] = SoldierLife
            army['soldierNum'] = SoldierNum

            #army['__soldierAttackNum'] = row_soldier_up['Attack']
            
            
            #army['__attackDistance'] = row_soldier['AttackDistance'] #攻击距离
            #army['__attackAngle'] = row_soldier['AttackRange'] #攻击角度
            #army['__attackFre'] = row_soldier['AttackFre'] #攻击频率
            army['armyDefense'] = F.defenseAdd(row_soldier_up['Defense'],row['SpeedValue'],row['GeneralType']) #军队防御
            SumDefense += army['armyDefense']
            army['armySpeed'] = F.speedAdd(row_soldier['Speed'],row['SpeedValue'],row['GeneralType']) #军队速度
            #army['__warnRadius'] = row_soldier['WarnRadius'] #警戒距离 (半径 角度360度固定）
                
            army['face'] = 6 #面向            
            EnemyArmy[armyId] = army
            r = army
            ArmyAttack = F.getArmyAttack(
                                               generalType = r['generalType'],
                                               soldierType = r['soldierType'],
                                               landForm = self.LandForm,
                                               soldierAttack = row_soldier_up['Attack'],
                                               soldierNum = r['soldierNum'],
                                               forceValue = r['generalForce'],
    
                                               )
            army['armyInitAttack'] = ArmyAttack #军队初始攻击力 查看公式
            self.enemyTotalLife += army['armyLife']
            self.armyNum += 1
            self.armyNumEnemy += 1
        
        #print 'EnemyArmy',EnemyArmy
        self.EnemyArmy = EnemyArmy
        if self.armyNumEnemy:
            self.enemyAvgDefense = SumDefense / self.armyNumEnemy
        else:
            self.enemyAvgDefense = 0
          
        return EnemyArmy
    
    def getMyArmy(self,MapId):
        '''获取我方军队信息'''
        MyArmy = {}
        row_map = Gcore.getCfg('tb_cfg_pve_map',MapId)
        CoordSet = Coord.Get9Coord(row_map['SelfCenterX'], row_map['SelfCenterY'], row_map['ArmySpace'], False)
        fields = ['GeneralId','PosId','TakeType','TakeNum','GeneralType','GeneralLevel','ForceValue','WitValue','SpeedValue','LeaderValue','ExpValue']
        generalRows = self.db.out_rows(self.tb_general(), fields, "PosId>0 AND UserId=%s"%self.uid) 
        if generalRows:
            generalRows = Gcore.getMod('General',self.uid).getLatestGeneralInfo(generalRows)
        SoldiersTech = Gcore.getMod('Book',self.uid).getTechsLevel(1)
        SumDefense = 0
        armyId = 100
        for row in generalRows:
            i = row['PosId']
            SoldierType = row['TakeType']
            SoldierNum = row['TakeNum']
            if not SoldierType in self.MyTroops: #出兵
                self.MyTroops[SoldierType] = SoldierNum
            else:
                self.MyTroops[SoldierType] += SoldierNum
                
            if SoldierNum == 0: #没有带兵不能上场
                continue
            armyId += 1
            SoldierLevel = SoldiersTech.get(SoldierType,0)
            GeneralId = row['GeneralId']
            
            
            row_soldier = Gcore.getCfg('tb_cfg_soldier',SoldierType)
            row_soldier_up = Gcore.getCfg('tb_cfg_soldier_up',(SoldierType,SoldierLevel))
            
            SoldierLife = row_soldier_up['Life']
            
            army = {}
            army['armyId'] = armyId
            army['armyUserId'] = '%s.%s'%(Gcore.getServerId(),self.uid)
            army['armyType'] = 1  #军队类型:  1友军  2敌军  3NPC
            
            army['armyLife'] = F.getArmyLife(SoldierLife,SoldierNum) * self.ClubTechAdd[5]  #军队的生命 军队科技加成
            
            #按校场布阵 地图9宫格而定
            army['initPointX'] = CoordSet[i][0] #初始位置X
            army['initPointY'] = CoordSet[i][1] #初始位置Y
            army['generalId'] = GeneralId #武将ID 用于损兵
            army['generalType'] = row['GeneralType']   #武将技能种类 , 军队需要显示武将的名称 来源于武将类型配置
            army['generalLevel'] = row['GeneralLevel'] #武将技能等级
            SkillId = Gcore.getCfg('tb_cfg_general',row['GeneralType'],'SkillId') #武将技能ID 暂定每个武将只有一个技能
            if SkillId:
                Chance = F.calSkillChance(SkillId, row['WitValue'])
                army['SkillDict'] = Gcore.common.gen01Dict(Chance,SkillId) 
            else:
                army['SkillDict'] = {}
            army['generalForce'] = row['ForceValue'] 
            army['generalWit'] = row['WitValue']  
            army['generalSpeed'] = row['SpeedValue']  
            army['generalLeader'] = row['LeaderValue']  
            
            army['soldierType'] = SoldierType
            army['soldierLevel'] = SoldierLevel
            army['soldierNum'] = SoldierNum

            army['armyDefense'] = F.defenseAdd(row_soldier_up['Defense'],row['SpeedValue'],row['GeneralType'])
            SumDefense += army['armyDefense']
            army['armySpeed'] = F.speedAdd(row_soldier['Speed'],row['SpeedValue'],row['GeneralType']) #移动速度
            army['face'] = 2 #面向            
            
            army['cur_armyLife'] = army['armyLife'] #当前军队生命 战斗中减少
            r = army
            ArmyAttack = F.getArmyAttack(
                                               generalType = r['generalType'],
                                               soldierType = r['soldierType'],
                                               landForm = self.LandForm,
                                               soldierAttack = row_soldier_up['Attack'],
                                               soldierNum = r['soldierNum'],
                                               forceValue = r['generalForce'],
                                               clubTechAdd = self.getClubTechAdd(row_soldier['SoldierSort'])
                                               )
            army['armyInitAttack'] = ArmyAttack 
            self.homeTotalLife += army['armyLife']
            self.armyNum += 1
            self.armyNumMy += 1
            MyArmy[armyId] = army
        
        self.MyArmy = MyArmy
        if generalRows:
            self.homeAvgDefense = SumDefense / len(generalRows)
        else:
            self.homeAvgDefense = 0
            
        return MyArmy
    
    def getOpArmy(self,MapId,OpUserId):
        '''获取对手方军队信息 参考于getMyArmy()'''
        LeastSoldierTake = Gcore.loadCfg(2401).get('LeastSoldierTake')
        LeastGeneralEnter = Gcore.loadCfg(2401).get('LeastGeneralEnter')
        kLeaderAddNum = Gcore.loadCfg(9001).get('kLeaderAddNum')
            
        EnemyArmy = {}
        row_map = Gcore.getCfg('tb_cfg_pve_map',MapId)
        CoordSet = Coord.Get9Coord(row_map['EnemyCenterX'], row_map['EnemyCenterY'], row_map['ArmySpace'], False)
        fields = ['GeneralId','PosId','TakeType','TakeNum','GeneralType','GeneralLevel','ForceValue','WitValue','SpeedValue','LeaderValue','ExpValue']
        generalRows = self.db.out_rows(self.tb_general(OpUserId), fields, "PosId>0 AND UserId=%s"%OpUserId) 
        if not generalRows:
            where = "UserId=%s ORDER BY GeneralLevel DESC LIMIT %s"%(OpUserId,LeastGeneralEnter)
            generalRows = self.db.out_rows(self.tb_general(OpUserId), fields, where) 
            
        if generalRows:
            generalRows = Gcore.getMod('General',OpUserId).getLatestGeneralInfo(generalRows)
            
        SoldiersTech = Gcore.getMod('Book',OpUserId).getTechsLevel(1)
        SumDefense = 0
        armyId = 200
        for row in generalRows:
            i = row['PosId']
            SoldierType = row['TakeType']
            SoldierNum = row['TakeNum']
            
            if SoldierNum <  LeastSoldierTake * kLeaderAddNum * row['LeaderValue']: #没有带兵不能上场 @todo最少30%的兵
                SoldierNum = int(LeastSoldierTake * kLeaderAddNum * row['LeaderValue'])
                
            armyId += 1
            SoldierLevel = SoldiersTech.get(SoldierType,0)
            GeneralId = row['GeneralId']
            
            row_soldier = Gcore.getCfg('tb_cfg_soldier',SoldierType)
            row_soldier_up = Gcore.getCfg('tb_cfg_soldier_up',(SoldierType,SoldierLevel))
            
            SoldierLife = row_soldier_up['Life']
            
            army = {}
            army['armyId'] = armyId
            army['armyUserId'] = '%s.%s'%(Gcore.getServerId(),OpUserId)
            army['armyType'] = 1  #军队类型:  1友军  2敌军  3NPC
            
            army['armyLife'] = F.getArmyLife(SoldierLife,SoldierNum) * self.ClubTechAdd[5]  #军队的生命 军队科技加成
            
            #按校场布阵 地图9宫格而定
            army['initPointX'] = CoordSet[i][0] #初始位置X
            army['initPointY'] = CoordSet[i][1] #初始位置Y
            army['generalId'] = GeneralId #武将ID 用于损兵
            army['generalType'] = row['GeneralType']   #武将技能种类 , 军队需要显示武将的名称 来源于武将类型配置
            army['generalLevel'] = row['GeneralLevel'] #武将技能等级
            SkillId = Gcore.getCfg('tb_cfg_general',row['GeneralType'],'SkillId') #武将技能ID 暂定每个武将只有一个技能
            if SkillId:
                Chance = F.calSkillChance(SkillId, row['WitValue'])
                army['SkillDict'] = Gcore.common.gen01Dict(Chance,SkillId) 
            else:
                army['SkillDict'] = {}
            army['generalForce'] = row['ForceValue'] 
            army['generalWit'] = row['WitValue']  
            army['generalSpeed'] = row['SpeedValue']  
            army['generalLeader'] = row['LeaderValue']  
            
            army['soldierType'] = SoldierType
            army['soldierLevel'] = SoldierLevel
            army['soldierNum'] = SoldierNum

            army['armyDefense'] = F.defenseAdd(row_soldier_up['Defense'],row['SpeedValue'],row['GeneralType'])
            SumDefense += army['armyDefense']
            army['armySpeed'] = F.speedAdd(row_soldier['Speed'],row['SpeedValue'],row['GeneralType']) #移动速度
            army['face'] = 2 #面向            
            
            army['cur_armyLife'] = army['armyLife'] #当前军队生命 战斗中减少
            r = army
            ArmyAttack = F.getArmyAttack(
                                               generalType = r['generalType'],
                                               soldierType = r['soldierType'],
                                               landForm = self.LandForm,
                                               soldierAttack = row_soldier_up['Attack'],
                                               soldierNum = r['soldierNum'],
                                               forceValue = r['generalForce'],
                                               clubTechAdd = self.getClubTechAdd(row_soldier['SoldierSort'])
                                               )
            army['armyInitAttack'] = ArmyAttack 
            self.homeTotalLife += army['armyLife']
            EnemyArmy[armyId] = army
            self.armyNum += 1
        
        self.EnemyArmy = EnemyArmy
        return EnemyArmy
    
    def getEnemyArmy(self):
        '''获取敌方军队信息'''
        WarId = self.WarId
        EnemyArmy = {}
        CfgPve  = Gcore.getCfg('tb_cfg_pve',WarId)
        MapId = CfgPve.get('MapId')
        row_map = Gcore.getCfg('tb_cfg_pve_map',MapId)
        CoordSet = Coord.Get9Coord(row_map['EnemyCenterX'], row_map['EnemyCenterY'], row_map['ArmySpace'], False)
        
        SumDefense = 0
        NpcNum = 0
        armyId = 200
        print 'CfgPve',CfgPve
        for i in xrange(1,self.TotalNpc+1):
            NpcId = CfgPve.get('NpcId%s'%i)
            if NpcId:
                armyId += 1
                NpcNum += 1
                print 'NpcId',NpcId
                r = Gcore.getCfg('tb_cfg_pve_npc',NpcId)
                rg = Gcore.getCfg('tb_cfg_general',NpcId)
                army = {}
                army['armyId'] = armyId
                army['armyUserId'] = '0'
                army['armyType'] = 3  #1友军 2敌军 3NPC
                #army['__armySizeL'] = 3 #军队尺寸的长(留着)
                #army['__armySizeW'] = 3 #军队尺寸的宽(留着)
                SoldierType = r['TakeSoldierType']
                SoldierNum = r['TakeSoldierNum']
                SoldierLevel = r['SoldierLevel']
                
                row_soldier = Gcore.getCfg('tb_cfg_soldier',SoldierType)
                row_soldier_up = Gcore.getCfg('tb_cfg_soldier_up',(SoldierType,SoldierLevel))
                
                SoldierLife = row_soldier_up['Life']
                
                #army['armyLife'] = (SoldierNum ** F.HP_mi) * SoldierLife #军队的生命
                army['armyLife'] = F.getArmyLife(SoldierLife, SoldierNum)  #军队的生命
                
                army['cur_armyLife'] = army['armyLife'] #当前军队生命 战斗中减少
                
                #按校场布阵 地图9宫格而定
                army['initPointX'] = CoordSet[i][0] #初始位置X
                army['initPointY'] = CoordSet[i][1] #初始位置Y
                
                #武将技能种类 , 军队需要显示武将的名称 来源于武将类型配置, NPC的来源于NPC配置
                army['generalType'] = r['NpcId'] # >1000
                army['generalLevel'] = r['GeneralLevel'] #武将等级
                army['generalForce'] = rg['BaseForce'] + r['GeneralLevel']*rg['GrowForce'] #总武力公式待确认
                army['generalWit'] = rg['BaseWit'] + r['GeneralLevel']*rg['GrowWit'] 
                army['generalSpeed'] = rg['BaseSpeed'] + r['GeneralLevel']*rg['GrowSpeed'] 
                army['generalLeader'] = rg['BaseLeader'] + r['GeneralLevel']*rg['GrowLeader'] 
                #不同于玩家
                SkillId = rg['SkillId'] #武将技能ID 暂定每个武将只有一个技能
              
                if SkillId:
                    Chance = F.calSkillChance(SkillId, army['generalWit'])
                    army['SkillDict'] = Gcore.common.gen01Dict(Chance,SkillId) 
                else:
                    army['SkillDict'] = {}
                    
                army['soldierType'] = SoldierType
                #army['__soldierSort'] = row_soldier['SoldierSort'] #分类  步 弓 骑 特 器
                army['soldierLevel'] = SoldierLevel
                #army['__soldierLife'] = SoldierLife
                army['soldierNum'] = SoldierNum
                #army['__soldierAttackNum'] = row_soldier_up['Attack']
                
                #army['__attackDistance'] = row_soldier['AttackDistance'] #攻击距离
                #army['__attackAngle'] = row_soldier['AttackRange'] #攻击角度
                #army['__attackFre'] = row_soldier['AttackFre'] #攻击频率
                army['armyDefense'] = F.defenseAdd(row_soldier_up['Defense'],army['generalSpeed'],army['generalType'])
                army['armySpeed'] = F.speedAdd(row_soldier['Speed'],army['generalSpeed'],army['generalType']) #移动速度
                #army['__warnRadius'] = row_soldier['WarnRadius'] #警戒距离 (半径 角度360度固定）
                
                army['face'] = 6 #面向  1右 2右上 3上 4左上  5左 6左下 7下 8右下
                SumDefense += army['armyDefense']
                #todo NPC目标定义
                #army['targetPointX'] = 1
                #army['targetPointY'] = 2
                r = army
                ArmyAttack = F.getArmyAttack(
                                               generalType = r['generalType'],
                                               soldierType = r['soldierType'],
                                               landForm = self.LandForm,
                                               soldierAttack = row_soldier_up['Attack'],
                                               soldierNum = r['soldierNum'],
                                               forceValue = r['generalForce'],
                                               )
                
                army['armyInitAttack'] = ArmyAttack #军队初始攻击力 查看公式
                
                self.enemyTotalLife += army['armyLife']
                self.armyNum += 1
                self.armyNumEnemy += 1
               
                EnemyArmy[armyId] = army
        
        self.EnemyArmy = EnemyArmy
        self.enemyAvgDefense = SumDefense / NpcNum
        return EnemyArmy
    
    def _endRankBattle(self,p={}):
        '''比武结束战斗'''
        EnemyArmyRestLife = 0
        for k in self.EnemyArmy:
            EnemyArmyRestLife += self.EnemyArmy[k]['cur_armyLife']
        FightResult = 1 if EnemyArmyRestLife < 1.1 else 0  #怕有误 剩血总和是1也算输
        
        MyRankId = self.db.out_field('tb_rank_fight','RankId','UserId=%s'%self.uid)

        RankFightMod = Gcore.getMod('RankFight',self.uid)
        WinLoseReward = Gcore.loadCfg(2401).get('WinLoseReward')
        
        if FightResult:
            RankFightMod.exchangeRank(self.OpUserId)
            WinMcoin = WinLoseReward['WinMcoin']
            WinHonour = WinLoseReward['WinHonour']
            Gcore.getMod('Player',self.uid).gainHonour(WinHonour) #挑战成功获得荣誉
            Star = self.getStarRank()
        else:
            WinMcoin = WinLoseReward['LoseMcoin']
            WinHonour = Star = 0 

        Gcore.getMod('Coin',self.uid).GainCoin(93009,4,WinMcoin,'BattleMod.endBattle') #成功失败都获得美酒
        RankFightMod.makeRankLog(self.OpUserId,FightResult,MyRankId)
        RankFightMod.updateFightTimes(onlyTime=True)
        
        bresult = {'Result':FightResult, 'Star':Star, 'Coin':{'Mcoin':WinMcoin}, 'Honour':WinHonour}
        if FightResult:
            bresult['Reward'] = self.getWarReward(Star,WinLoseReward['WinDropId'],100)
        
        return self.rewardFormat(bresult)
        
    def endBattle(self,p={}):
        '''立即结束战斗(兼容战役和攻城)'''
#        @"winArmyType": 1 #胜利那方的军队类型  友军1  NPC 2  敌军 3  (弃用)
#        @"resultType": 1  #1:战斗时间 2:一方死 3:一方基地被打掉 4:攻打进程超过 51% 5:立即结束  (弃用)
#        @"process": 0.51  #攻城进度0 ~ 1  string (弃用
#        assert type(p['resultType']) is int

        if self.battleType==3:
            return self._endRankBattle(p) if self.canWar else {}  #比武独立,以下是战役和攻城
            
        if self.BattleEnd or (self.battleType==2 and not self.SiegeStarted): #防止重复结束,或者未开始就断线结束
            if self.battleType==2 and not self.SiegeStarted and self.foundTarget: #攻城 查找了 没开始
                serverId,UserId = self.fightUnit
                key = '%s.%s'%(serverId,UserId)
                redisUnlock(key) #解锁
            return
        else:
            self.BattleEnd = True
        print '--------------------- ps endBattle() -------------------------'
        cutDict = {} #武将损兵数组
        GeneralIds = [] #武将列表 用于增加武将经验
        bresult = {'Result':0,'Expend':{},'GeneralExpend':{},'GeneralExp':0} #战斗结果
        if self.battleType==1: #战役结束 (只有战役才有立即结束继续运算,攻城的改为无效)
            if not self.canWar:
                return -93009002
            if p.get('resultType')==5 : #立即结束  自动战斗
                #-----------------先判断一下按下立即结束的时候出结果了没---------------------
                EnemyArmyRestLife = 0
                for k in self.EnemyArmy:
                    EnemyArmyRestLife += self.EnemyArmy[k]['cur_armyLife']
                
                MyArmyRestLife = 0
                for k in self.MyArmy:
                    MyArmyRestLife += self.MyArmy[k]['cur_armyLife']
                    
                if self.EnemyBastion[10002]['cur_bastionLife']==0 or EnemyArmyRestLife==0:
                    bresult['Result'] = 1
                elif self.EnemyBastion[10001]['cur_bastionLife']==0 or MyArmyRestLife==0:
                    bresult['Result'] = 0
                else:
                    #--------------------------------------------------------------------------
                    param = {} #结束战斗参数
                    param['target_type'] = 1 if self.battleType==2 else 0  #敌方类型  0:NPC(战役) 1:玩家(攻城)
                    param['N1'] = len(self.MyArmy)#己方方阵数量
                    param['N2'] = len(self.EnemyArmy)#对方方阵数量
                    param['TN1'] = self._param_TN(self.MyArmy) #己方方阵种类数
                    param['TN2'] = self._param_TN(self.EnemyArmy) #敌方方阵种类数
                    if self.battleType == 2:
                        param['b_n_2'],param['b_t_n_2'] = self._param_defense( self.DefenseInfo ) #敌方防御工事数量  , 敌方防御工事种类
                    else:
                        param['b_n_2'] = 0
                        param['b_t_n_2'] = 0
                        
                    param['time'] =  time.time() + 5 - self.startTime  #当前消耗时间 5秒后
                    attr = self._param_getArmyAttr(self.MyArmy,1)
                    param.update(attr)
                    attr = self._param_getArmyAttr(self.EnemyArmy,2)
                    param.update(attr)
                    param['P'] = 0 #攻城进度 先设为0
                    param['base_hp_2'] = self.EnemyBastion[10002]['cur_bastionLife']
                    f=FightOver()
                    re=f.judgment(param) #{'FP': 0.005, 'REST_1': 0.93, 'result': 1, 'REST_2': 0}
                    if re is False or not isinstance(re, dict):
                        re = {'FP': 0, 'REST_1': 0, 'result': 0, 'REST_2': 0} #异常处理
                   
                    bresult['Result'] = re['result']
                    self.MyBastion[10001]['cur_bastionLife'] *= re['REST_1'] #战役时我方 基地扣血
                    for k in self.MyArmy:
                        self.MyArmy[k]['cur_armyLife'] = self.MyArmy[k]['cur_armyLife']*re['REST_1'] #扣血
            else:
                TotalArmyRestLife = 0
                for k in self.EnemyArmy:
                    TotalArmyRestLife += self.EnemyArmy[k]['cur_armyLife']
                if self.EnemyBastion[10002]['cur_bastionLife']==0 or TotalArmyRestLife==0:
                    bresult['Result'] = 1
                else:
                    bresult['Result'] = 0
                    
        elif self.battleType==2: #攻城结束
            if not self.foundTarget:
                return -93009001
            else:
                serverId,UserId = self.fightUnit
                key = '%s.%s'%(serverId,UserId)
                redisUnlock(key) #解锁
                
            bresult = {'Result':0,'Expend':{},'Reward':[]}
            self.fightProcess = self.getProcess()
            frontProcess = p.get('process',0)/100 #前台发过来的进度
#            if frontProcess != self.fightProcess:
#                print '前后台进度不一致 前台：%s , 后台：%s'%(frontProcess,self.fightProcess)
            if frontProcess < self.fightProcess+0.05 and 'process' in p:
                #self.fightProcess = frontProcess
                #print '使用前台进度:',frontProcess
                print '前后台进度相差>百分之5,前台:%s,后台:%s'%(frontProcess,self.fightProcess)
            
            self.fightProcess = frontProcess
            print '暂只使用前台进度:',self.fightProcess 
            if self.fightProcess >= 0.51 or self.EnemyBastion[10002]['cur_bastionLife']==0:
                bresult['Result'] = 1 #胜利相关操作在后面加
            else:
                bresult['Result'] = 0
        #--------------------------------- 战斗结束结算开始  -----------------------------------

        cfgReward = self.CfgPveReward
        #计算武将损兵 和 兵种损兵
        for k in self.MyArmy:
            army = self.MyArmy[k]
            soldierType = army['soldierType']
            soldierExpendNum = int( math.ceil( army['soldierNum'] * (1-army['cur_armyLife']/army['armyLife']) ) )
            generalId = self.MyArmy[k]['generalId']
            if soldierExpendNum:
                cutDict[ generalId ] = soldierExpendNum
            GeneralIds.append(generalId)
            
            if soldierType not in bresult['Expend']:
                bresult['Expend'][soldierType] = 0
            bresult['Expend'][soldierType] += soldierExpendNum #损失的兵种和值 (不同军队同兵种)
            
        if self.battleType == 1: #战役
            if bresult['Result'] == 1: #胜利
                self._incrProcessWarId() #开放下一场战役
                star = self.getStar() 
                cutRatio = 1 #减少
                bresult['Reward'] = self.getWarReward(star)
                bresult['GeneralExp'] = self.CfgPveReward['GeneralExp']
                Gcore.getMod('General',self.uid).warIncrGeneralExp(GeneralIds,bresult['GeneralExp'])
                perPoint = self.CfgPve.get(self.WarId,{}).get('ActPointNeed',1)
                Gcore.getMod('War',self.uid).useActPoint(perPoint) #使用行动力
            else:
                star = 1
                cutRatio =F.failRewardRatio #减少
                
            GcoinField = 'Reward%sCointype3'%star
            JcoinField = 'Reward%sCointype2'%star
            bresult['Star'] = star if bresult['Result'] else 0 #失败不显示星级 0级
            bresult['Coin'] = {'Gcoin':int( cfgReward.get(GcoinField)*cutRatio ),
                              'Jcoin':int( cfgReward.get(JcoinField)*cutRatio )}
        elif self.battleType == 2: #攻城

            if bresult['Result'] == 0: #失败 
                bresult['Coin'] = {'Gcoin':0, 'Jcoin':0}
                #基础荣誉=胜利方等级-失败方等级差对应荣誉值
                #d、防守方胜利时，获得荣誉=60%*基础荣誉*(1-攻城进度)
                levelDif = self.fightUser['UserLevel'] - Gcore.getUserData(self.uid,'UserLevel')
                baseHonour = Gcore.getCfg('tb_cfg_honour',levelDif,'Honour')
                Honour = Gcore.loadCfg(9301).get('SiegeFailHounerCut')*baseHonour*(1-self.fightProcess)
                bresult['Honour'] = int(Honour*-1) #攻打方扣将 防守方增加
                print "失败,荣誉",bresult['Honour']
            else: #胜利
                #资源计算
                cutRatio = 1 
                if self.fightProcess <= 0.5:
                    cutRatio = 0.7
                elif self.fightProcess < 1:
                    cutRatio = 0.8
                Gcoin = self.grabCoin['Gcoin'] * self.fightProcess * cutRatio
                Jcoin = self.grabCoin['Jcoin'] * self.fightProcess * cutRatio
                if Gcoin<0:
                    Gcoin = 0
                if Jcoin<0:
                    Jcoin = 0
                print ' >> Gcoin:%s = %s * %s * %s'%(Gcoin, self.grabCoin['Gcoin'], self.fightProcess, cutRatio)
                bresult['Coin'] = {'Gcoin':int(Gcoin), 'Jcoin':int(Jcoin) }
                
                #荣誉计算
                cutRatio2 = 1 
                if self.fightProcess <= 0.5:
                    cutRatio2 = 0.3
                elif self.fightProcess < 1:
                    cutRatio2 = 0.6
                levelDif = Gcore.getUserData(self.uid,'UserLevel') - self.fightUser['UserLevel']
                baseHonour = Gcore.getCfg('tb_cfg_honour',levelDif,'Honour')
                bresult['Honour'] = int(baseHonour * self.fightProcess * cutRatio2)
                print "成功,荣誉",bresult['Honour']
                
                #碎片抢夺
                ServerId,UserId = self.fightUnit
                IsLocalServer = Gcore.IsLocal(ServerId) #是否本服
                if IsLocalServer:
                    kGrapPatch = Gcore.loadCfg(9301).get('kGrapPatch')
                    GrapPatchNum = Gcore.getCfg('tb_cfg_honour',levelDif,'GrapPatchNum')
                    GrapChance = kGrapPatch * self.fightProcess * 100
                    if random.randint(1,100) <= GrapChance:
                        patchs = Gcore.getMod('Building_pub',UserId).randDescPatch(GrapPatchNum)
                        if patchs<0: 
                            GrapPatchIdList = Gcore.loadCfg(9301).get('GrapPatchIdList')
                            patchs = {random.choice(GrapPatchIdList):1} #对方没得抢,系统随机给一个差的
                        
                        Gcore.getMod('Building_pub',self.uid).changePatchNum(patchs)
                        bresult['PatchReward'] = patchs #将成奖励
                else:
                    print '跨服抢碎片未处理'
                
                
            if self.fromType==3: #反抗不给荣誉
                bresult['Honour'] = 0
                try:
                    Gcore.getMod('Building_hold',self.uid).setReventProcess(self.fightProcess, bresult['Result']) #累积反抗进度 
                except:
                    if Gcore.TEST:
                        raise
            
            
        self.gainBattleCoin(bresult['Coin']) #为用户增加货币(包括攻城和战役)

        if cutDict:
            print 'cutDict >>> ',cutDict
            Gcore.getMod('General',self.uid).cutGeneralTakeNum(cutDict) #减少武将带兵
            bresult['GeneralExpend'] = cutDict
            
        if bresult['Expend']:
            #Gcore.getMod('Building_camp',self.uid).changeSoldierNum( bresult['Expend'],0 ) #校场减兵
            Gcore.getMod('General',self.uid).autoAddSoldier() #自动补兵
            pass
        if self.battleType == 2: #攻城
            self.calBattle(bresult)
        else:
            row = {}
            row['UserId'] = self.uid
            row['WarId'] = self.WarId
            row['Result'] = bresult['Result']
            row['ResultDetail'] = json.dumps(bresult)
            row['RecordDate'] = Gcore.common.today()
            row['CreateTime'] = Gcore.common.nowtime()
            self.db.insert('tb_war_log',row)
            
        #------------------------完成相关事件--------------
        if self.battleType==1: #战役
            fromType = 1 if self.IsSweep else 0
        else:
            fromType = self.fromType
        endType = 1 if p.get('resultType')==5 else 0
        Gcore.getMod('Event',self.uid).battleEnd(self.battleType, fromType, endType, self.MyTroops, bresult, self.WarId)
        #-------------------------------------------------
        return self.rewardFormat(bresult)  #组成前台需要的结构
            
    def rewardFormat(self,bresult):
        '''将原来定义的结果转成 统一的奖励结构 方便前台使用 request by Tomorrow'''
        rewardcell = Gcore.getMod('Reward',self.uid).rewardcell
        bReward = []
        if bresult.get('Coin',{}).get('Jcoin'):
            bReward.append( rewardcell(3,2,bresult['Coin']['Jcoin']) )
        if bresult.get('Coin',{}).get('Gcoin'):
            bReward.append( rewardcell(3,3,bresult['Coin']['Gcoin']) )
        if bresult.get('Coin',{}).get('Mcoin'):
            bReward.append( rewardcell(3,4,bresult['Coin']['Mcoin']) )
        if bresult.get('Honour'):
            bReward.append( rewardcell(3,5,bresult['Honour']) )
        if bresult.get('GeneralExp'):
            bReward.append( rewardcell(7,0,bresult.get('GeneralExp')) )
        if bresult.get('PatchReward'):
            for k,v in bresult.pop('PatchReward',{}).iteritems():
                bReward.append( rewardcell(6,k,v) )
        bresult['bReward'] = bReward
        
        #跟前台确认删掉不需的键
        return bresult
    
    def calBattle(self,bresult):
        '''攻城结算'''
        ServerId,UserId = self.fightUnit
        key = '%s.%s'%(ServerId,UserId)
        
        IsLocalServer = Gcore.IsLocal(ServerId) #是否本服
            
        if self.DchangeList:
            Defense = {}
            for k in self.DchangeList:
                Defense[k] = self.DefenseInfo[k]['cur_LifeRatio']
            if IsLocalServer: #本服
                tb_wall_defense = self.tb_wall_defense(UserId)
                for k,v in Defense.iteritems():
                    #if False: #测试暂 不损耗防御工事生命
                    sql = "UPDATE %s SET LifeRatio='%s' WHERE WallDefenseId='%s'"%(tb_wall_defense,v,k)
                    self.db.execute(sql)
                Gcore.getMod('Redis',UserId).offCacheWallDefense() #更新缓存
            else: #跨服
                param = {}
                param['UserId'] = UserId
                param['Defense'] = Defense
                Gcore.sendmq(5, ServerId, param) #工事损坏
            
        #攻打日志 (可用于手下败将)
        rowUser = self.fightUser
        arr = {}
        arr["PeerUID"] = UserId
        arr["PeerSID"] = ServerId
        arr["BattleType"] = self.fromType  #1查找  2复仇 3反抗  4抢夺
        arr["BattleResult"] = bresult['Result'] #0失败，1胜利。
        arr["PeerName"] = rowUser['NickName']
        arr["PeerLevel"] = rowUser['UserLevel']
        arr["PeerVipLevel"] = rowUser['VipLevel']
        arr["PeerCamp"] = rowUser['UserCamp']
        arr["PeerIcon"] = rowUser['UserIcon']
        arr["UserId"] = self.uid
        arr["CreateTime"] = time.time()
        arr["FightProcess"] = self.fightProcess
        arr["FightScore"] = bresult['Honour']
        arr["JcoinGet"] = bresult['Coin']['Jcoin']
        arr["GcoinGet"] = bresult['Coin']['Gcoin']
        self.db.insert('tb_battle_record', arr)
        
        #战报(被攻打者收到) (暂未区分本服和外服)
        arr = {}
        arr['UserId'] = UserId
        arr['Revenge'] = 1 if self.fromType in (1,4) and bresult['Result'] else 0 #是否可以反击
        arr['FighterServerId'] = Gcore.getServerId()
        arr['FighterId'] = self.uid
        arr['FighterIconId'] = Gcore.getUserData(self.uid, 'UserIcon')
        arr['FighterName'] = Gcore.getUserData(self.uid, 'NickName')
        arr['FighterLevel'] = Gcore.getUserData(self.uid, 'UserLevel')
        arr['DefenseResult'] = 0 if bresult['Result'] else 1
        arr['JcoinLost'] = bresult['Coin']['Jcoin']
        arr['GcoinLost'] = bresult['Coin']['Gcoin']
        arr['DefenseScore'] = bresult['Honour']*-1
        arr['FightProcess'] = self.fightProcess
        arr['CreateTime'] = time.time()
        if IsLocalServer: #本服
            self.db.insert('tb_battle_report',arr)
        else:
            Gcore.sendmq(6,ServerId,arr)
            
        #扣取被攻打者资源
        if bresult['Coin']['Jcoin'] or bresult['Coin']['Gcoin']:
            coinDict = {2:bresult['Coin']['Jcoin'],3:bresult['Coin']['Gcoin']} 
            print 'coinDict',coinDict
            if IsLocalServer: #本服
                Gcore.getMod('Building_resource',UserId).lostCoin(coinDict,93009)
            else:
                Gcore.sendmq(7,ServerId,{'UserId':UserId,'coinDict':coinDict} )
        
        #增扣荣誉
        if bresult['Honour']:
            Gcore.getMod('Player',self.uid).gainHonour(bresult['Honour'],93009)
            if IsLocalServer:
                Gcore.getMod('Player',UserId).gainHonour(bresult['Honour']*-1,93009)
            else:
                arr = {}
                arr['UserId'] = UserId
                arr['Honour'] = bresult['Honour']*-1
                Gcore.sendmq(8,ServerId,arr)
        
        #被攻打方获得保护
        if bresult['Result'] and self.fightProcess:
            AddSecond = 4.8*60*self.fightProcess*100  #每1点进度保护4.8分钟
            if AddSecond>8*3600:
                AddSecond = 8*3600 #最长8小时
            if Gcore.TEST or True:
                AddSecond = 120 #测试2分钟
                
            if IsLocalServer: #本服
                Gcore.getMod('Player',UserId).addProtectTime(AddSecond)
            else:
                Gcore.sendmq(9,ServerId,{'UserId':UserId,'AddSecond':AddSecond})
                Gcore.redisM.hset('sgProtect', key, Gcore.common.nowtime()+120 )
                #先预保护1分钟，收到消息的时候再更新,防止马上被人打
        
        #抢夺成功
        if bresult['Result'] and self.fromType==4:
            try:
                if IsLocalServer:
                    para = {'typ':2, 'uid':self.defeaterUID, 'sid':self.defeaterSID}
                    Gcore.getUI('Building_hold',UserId).SlaveOperand(para) #让被抢夺者释放奴隶
                else:
                    Gcore.sendmq(3, ServerId, {'HolderId':UserId,'GiverServerId':self.defeaterSID,'GiverId':self.defeaterUID})
                Gcore.getUI('Building_hold',self.uid).SetHold( {'SlaveUID':self.defeaterUID,'SlaveSID':self.defeaterSID} ) 
            except Exception,e:
                print '抢夺失败:',e
                if Gcore.TEST:
                    raise
        
        #被攻打结束
        if IsLocalServer:
            Gcore.getMod('Player',self.uid).beFightEnd(UserId)
        else:
            #@todo
            pass
        
        redisUnlock(key) #解锁
        
    def getProcess(self):
        '''计算攻城进度'''
        fightProcess = 0
        totalDamage = 0 #造成的总伤害
        for k in self.DchangeList:
            row = self.DefenseInfo[k]
            Life = Gcore.getCfg('tb_cfg_soldier_up',(row['SoldierType'],row['SoldierLevel']),'Life')
            totalDamage += (row['LifeRatio'] - row['cur_LifeRatio'])*Life
            
            ttt = (row['LifeRatio'] - row['cur_LifeRatio'])*Life
            print '工事 totalDamage+=',ttt
        
        for k in self.EnemyArmy:
            row = self.EnemyArmy[k]
            totalDamage += (row['armyLife'] - row['cur_armyLife'])
            
            ttt = (row['armyLife'] - row['cur_armyLife'])
            print '军队 totalDamage+=',ttt
            
        for k in self.EnemyBastion:
            row = self.EnemyBastion[k]
            totalDamage += (row['bastionLife'] - row['cur_bastionLife'])    
            
            ttt = (row['bastionLife'] - row['cur_bastionLife'])    
            print '基地 totalDamage+=',ttt
            
        if self.enemyTotalLife==0:
            fightProcess = 0
        else:
            print 'totalDamage',totalDamage
            print 'self.enemyTotalLife',self.enemyTotalLife
            fightProcess =  totalDamage/self.enemyTotalLife
        
        fightProcess = round(fightProcess,2)
        print '获得攻城进度:',fightProcess
        return fightProcess
    
    def gainBattleCoin(self,coinDict):
        '''获得战斗的货币奖励'''
        assert 'Gcoin' in coinDict
        assert 'Jcoin' in coinDict
        classMethod = 'BattleMod.gainBattleCoin'
        param = {'WarId':self.WarId} #暂只记录这些部分
        if coinDict['Jcoin']:
            Gcore.getMod('Coin',self.uid).GainCoin(93009,2,coinDict['Jcoin'],classMethod,param)
        if coinDict['Gcoin']:
            Gcore.getMod('Coin',self.uid).GainCoin(93009,3,coinDict['Gcoin'],classMethod,param)
    
    def getWarReward(self,Star,DropId=None,DropRatio=None):
        '''获得战斗奖励'''
        from random import randint
        
        if not DropId:
            DropId = self.CfgPve.get('DropId')
        if not DropRatio:
            DropRatio = self.CfgPve.get('DropRatio')
        
        
        if randint(0,100) > DropRatio: #会掉落 
            return []
        else:
            print 'DropId',DropId
            print 'Star',Star
            RewardCfgList = Gcore.getCfg('tb_cfg_pve_drop',(DropId,Star)) 
            RewardList = []
            import copy
            for i in xrange(3):
                #print 'RewardCfgList',RewardCfgList
                RewardUnit = copy.deepcopy( Gcore.common.Choice(RewardCfgList,count=1) )
                if i==0:
                    RewardUnit['WillGet'] = 1
                    #RewardGet = RewardUnit #中奖信息
                    #print 'RewardGet',RewardGet
                    #发放奖励
                    RewardReturn = Gcore.getMod('Reward',self.uid).reward(91002,
                                                          {"WarId":self.WarId},
                                                          RewardUnit['RewardType'],
                                                          RewardUnit['GoodsId'],
                                                          RewardUnit['GoodsNum'],
                                                          )
                    if RewardUnit['RewardType'] == 1: #是装备
                        if not isinstance(RewardReturn, (tuple,list)):
                            RewardReturn = []
                        RewardUnit['EquipIds'] = RewardReturn
                    
                else:
                    RewardUnit['WillGet'] = 0
                    
                del RewardUnit['RewardId']
                del RewardUnit['Ratio']
                
                if self.IsSweep: #如果是扫荡
                    return [RewardUnit] #统一返回列表
       
                RewardList.append(RewardUnit)
        
            return RewardList
            
    def getStar(self):
        '''获得战役结果星级 战役单位 当前HP/总HP:　　　　　　　　
                    　                          0 ≤ X ＜ 30%，一星； 
　　　　　　　　　　30%≤ X ＜60%，两星；
　　　　　　　　　　60% ≤ X＜100%，三星；
        @return 星级 int (1 2 3) 
        '''
        TotalUnitLife = self.homeTotalLife + self.MyBastion[10001]['bastionLife'] #总HP
        CurUnitLife = self.MyBastion[10001]['cur_bastionLife'] #基地剩余HP
        for r in self.MyArmy.values():
            CurUnitLife += r['cur_armyLife'] #我军剩余HP
        try:
            LeftPercent = CurUnitLife/TotalUnitLife
        except:
            LeftPercent = 0
        
        if LeftPercent>=0 and LeftPercent<0.3:
            star = 1
        elif LeftPercent>=0.3 and LeftPercent<0.6:
            star = 2
        else:
            star = 3
        if star:
            row = self.db.out_fields('tb_war_star','*','UserId=%s'%self.uid)
            row.pop('UserId',None)
            totalStar = sum(row.values())+star
            if totalStar:
                Gcore.getMod('Event',self.uid).pveStarGet(totalStar) #完成成就
        self.updateStar(star)
        return star
    
    def getStarRank(self):
        '''排名星级计算 '''
        TotalUnitLife = self.homeTotalLife
        CurUnitLife = 0
        for r in self.MyArmy.values():
            CurUnitLife += r['cur_armyLife'] #我军剩余HP
        try:
            LeftPercent = CurUnitLife/TotalUnitLife
        except:
            LeftPercent = 0
        
        if LeftPercent>=0 and LeftPercent<0.3:
            star = 1
        elif LeftPercent>=0.3 and LeftPercent<0.6:
            star = 2
        else:
            star = 3
        return star
        
    def updateStar(self,star):
        oldstar= self.db.out_field('tb_war_star', 'War%s'%self.WarId, 'UserId=%s'%self.uid )
        if oldstar<star:
            sql = 'UPDATE tb_war_star SET War%s=%s WHERE UserId=%s'%(self.WarId,star,self.uid)
            self.db.execute(sql)
            print 'updateStar',sql

    def _incrProcessWarId(self):
        '''增长玩家可打战役，因为通关了'''
        nextWarId = self.nextWarId(self.WarId)
        if self.WarId < nextWarId and self.ProcessWarId < nextWarId:
            self.db.update('tb_user',{'ProcessWarId':nextWarId},
                           "UserId=%s AND ProcessWarId<%s"%(self.uid,nextWarId))
            print '_incrProcessWarId >> ',self.db.sql
    
    def nextWarId(self,WarId):
        '''获取下一个战役ID'''
        NextWarIdList = [t for t in Gcore.getCfg('tb_cfg_pve').keys() if t>WarId ]
        if not NextWarIdList:
            NextWarId = WarId #已是最大ID
        else:
            NextWarId = min(NextWarIdList)
            
        return NextWarId
            
            
    def _param_TN(self,Army):
        '''公式:获取军队类型'''
        SoldierSortList = []
        assert type(Army) is dict
        for r in Army.values():
            soldierSort = Gcore.getCfg('tb_cfg_soldier',r['soldierType'],'soldierSort')
            if soldierSort not in SoldierSortList:
                SoldierSortList.append( soldierSort )
        
        return len(SoldierSortList)
    
    def _param_defense(self,DefenseInfo):
        '''公式:获取防御工事类型和数量'''
        assert type(DefenseInfo) is dict
        SoldierTypeList = []
        for r in DefenseInfo.values():
            if r['SoldierType'] not in SoldierTypeList:
                SoldierTypeList.append( r['SoldierType'] )
        
        return len(DefenseInfo),len(SoldierTypeList)
    
    def _param_getArmyAttr(self,Army,sign):
        '''公式:获取军队属性'''
        assert sign in (1,2)
        param = {}
        param['hp'] = [] #当前生命值
        param['def'] = [] #当前防御力
        param['rng'] = [] #方阵当前攻击距离
        param['spd'] = [] #移动速度
        param['type'] = [] #方阵兵种
        param['weak_target'] = [] #克制兵种
        #param['map'] = [] #适应地形
        param['atk'] = [] #当前攻击力
        
        param['pro'] = [] #技能释放概率 (3.0以后跟进)
        
        assert type(Army) is dict
        for r in Army.values():
            #{'soldierLife': 15L, 'warnRadius': 40L, 'generalLevel': 1, 'attackFre': 0.8, 'soldierDefenseNum': 15L, 'soldierLevel': 0, 'generalSpeed': 20, 'armyType': 1, 'armySpeed': 1L, 'armySizeW': 3, 'soldierSort': 1L, 'armyLife': 13320L, 'generalWit': 20, 'initPointX': 12L, 'initPointY': 31L, 'generalSkill': 25, 'armySizeL': 3, 'attackAngle': 90L, 'generalType': 132, 'armyId': 104, 'generalForce': 20, 'soldierType': 5, 'attackDistance': 20L, 'soldierAttackNum': 20L, 'armyUserId': 1001, 'face': 2, 'soldierNum': 888L, 'generalLeader': 20}
            if 'cur_armyLife' not in r:
                r['cur_armyLife'] = r['armyLife']
            
            rAttr = Gcore.getCfg('tb_cfg_soldier',r['soldierType'])
            rAttrLv = Gcore.getCfg('tb_cfg_soldier_up', (r['soldierType'],r['soldierLevel']) )
            param['hp'].append( r['cur_armyLife'] )
            param['def'].append( rAttrLv['Defense'] )
            param['rng'].append( rAttr['AttackDistance'])
            param['spd'].append( rAttr['Speed'] )
            param['type'].append( rAttr['SoldierSort'] )
            param['weak_target'].append( Gcore.common.getWeekSort(rAttr['SoldierSort']) )
#            if Gcore.getCfg('tb_cfg_soldier', r['soldierType'], 'LandForm') == self.LandForm:
#                param['map'].append( r['armyId'])

            ArmyCurAttack = F.getArmyCurAttack( r['armyInitAttack'],r['cur_armyLife'],r['armyLife'] )

            param['atk'].append( ArmyCurAttack )
        
        attr = {}
        for k,v in param.iteritems():
            key = '%s_%s'%(k,sign)
            attr[key] = v
        return attr    
    
    
    def getClubTechAdd(self,soldierSort):
        '''获取军团科技加成'''
        if self.battleType == 2 and 0: #攻城
            if soldierSort == 1: #步
                return self.ClubTechAdd[6]
            elif soldierSort == 2: #弓
                return self.ClubTechAdd[7]
            elif soldierSort == 3: #骑
                return self.ClubTechAdd[8]
            elif soldierSort == 4: #特
                return self.ClubTechAdd[9]
            elif soldierSort == 5: #器
                return self.ClubTechAdd[10]
            
        else:
            return 1
                
        
if __name__ == '__main__':
    printd = Gcore.printd
    #43577 忆凡ID    1011 黄国剑      1001 李志荣     43346永乾
    c = BattleMod(1001)
    #------------------------- 比武模拟 ---------------------------
    if 1:
        initRankResult = c.initRankFight(1005)
        print 'initRankResult',initRankResult
        printd ( c.getRankInfo() )
        p = {
                'SynA':{'201':0,'202':0,'203':0,'204':0,'205':0},
                }
        c.synBattle(p)
            
        print c.endBattle()
    #------------------------- 战役模拟 ---------------------------
    elif 0:
        initWarResult = c.initWar(101)
    
        if initWarResult < 0:
            print 'initWarResult',initWarResult
            raise Exception("Error initWar")
        r = c.getWarInfo()
        #printd(r)
        p = {
                    'SynA':{'202':0,'201':0,'101':10000},
                    'SynB':{'10002':0},
                    }
        c.synBattle(p)
        printd( c.endBattle() )
    #------------------------- 攻城模拟 ---------------------------
    else:
        initWarResult = c.initWar(0)
        if initWarResult < 0:
            raise Exception("Error initWar:%s"%initWarResult)
       
        redisUnlock('1.1001') #解锁
        p = {'targetUserId':1001,'targetServerId':1,'fromType': 1} 
        #p = {}
        for i in xrange(1):
            printd ( c.findSiege(p) )
        
        #printd ( c.findSiege(p) )#查找
        if 0: #开始攻城,战斗结果
            d = c.startSiege()
            p = {
                    #'SynA':{'202':0,'201':0,'101':10000},
                    'SynB':{'10002':0},
                    }
            c.synBattle(p)
            p = {u'process': 100, u'resultType': 3, u'winArmyType': 1, 'ClientTime': 0}
            #time.sleep(100)
            printd( c.endBattle(p) )
        
        #import time;time.sleep(2) #等MQ和Redis
    Gcore.runtime()
        