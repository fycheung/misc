# -*- coding:utf-8 -*-
# author:
# date:2013-3-5
# 游戏内部接口,用户模型

import time
import copy
from  sgLib.defined import CFG_BUILDING,CFG_HOME_SIZE

from sgLib.core import Gcore
import sgLib.common as comm
from sgLib.base import Base

class PlayerMod(Base):
    '''docstring for ClassName模板'''
    def __init__(self, uid):
        '''注释'''
        Base.__init__(self, uid)
        self.uid = uid
        #print 'PlayerMod.db',self.db,self.db.cursor #数据库连接类
    
#    def __del__(self):
#        pass
    #------------------------------START模块内部接口-------------------------------
    def PlayerInfo(self):
        '''返回获取用户相关资料'''
        startTime = time.time()
            
        fields = ['UserHonour','UserCamp','NickName','VipLevel','BuyMapTimes', 'WorkerNumber',
                  'UserIcon','UserExp','UserLevel','Fighter','FightEndTime','ProtectEndTime','BindAccount','LoginTimes',
                  'HolderServerId','HolderId','HoldEndTime', #我是否有藩国,藩国结束时间
                  ]
        
        userProfile = self.getUserProfile()
        
        data = self.getUserBaseInfo(fields)
        data['UserId'] = self.uid
        data['ServerId'] = Gcore.getServerId() #服务器ID
        data['SuserId']= '%s.%s'%(Gcore.getServerId(),self.uid) #服务器ID跟角色ID组成的标志串
        #data['Worker'] =  self.getUserWorker()
        #@todo 添加更多主角信息
        if Gcore.common.nowtime()>=data['FightEndTime']:
            FightRestTime = 0
        else:
            FightRestTime = data['FightEndTime'] - Gcore.common.nowtime()
        
        data['FightRestTime'] = FightRestTime #被攻打剩余时间   Fighter - 正在被谁攻打
        data.pop('FightEndTime')
        
        buildingCfg = Gcore.loadCfg(CFG_BUILDING)
        data['InitJcoin'] = buildingCfg['InitJcoin']
        data['InitGcoin'] =  buildingCfg['InitGcoin']
        
        data['Coin'] = self.getUserCoin()
        data['ServerTime'] = time.time() #round(time.time(),2)
        data['SoldierLevel'] = Gcore.getMod('Book',self.uid).getTechsLevel(1)
        data['SoldierInfo'] = Gcore.getMod('Building_camp', self.uid).TouchAllSoldiers()
        data['Equipments'] = Gcore.getMod('Equip', self.uid).getAllValidEquip()
        data['Factor'] = { #全部系数
                              'kLeader': Gcore.loadCfg(Gcore.defined.CFG_BATTLE)["kLeaderAddNum"] , #统帅系数 @todo 从配置中读取
                              }
        data['Exchange'] = Gcore.loadCfg( Gcore.defined.CFG_ITEM ).get('exchange') #货币兑换比例
        #data['Timezone'] = Gcore.config.CFG_TIMEZONE #时区
        #data['TimezoneDif'] = Gcore.config.CFG_TIMEZONEDIF #格林时间+CFG_TIMEDIF
        
        data['Timezone'] = Gcore.loadCoreCfg('Timezone') #时区
        data['TimezoneDif'] = int( Gcore.loadCoreCfg('TimezoneDif') ) #格林时间+CFG_TIMEDIF
        
        data['PVPstartTime'] = Gcore.loadCfg( Gcore.defined.CFG_PVP ).get('PVPstartTime') #将弃用
        data['PVPendTime'] = Gcore.loadCfg( Gcore.defined.CFG_PVP ).get('PVPendTime')     #将弃用
        data['PvpTime'] = Gcore.loadCfg( Gcore.defined.CFG_PVP ).get('PvpTime')
        
        #军团信息
        clubInfo = Gcore.getMod('Building_club', self.uid).getMemberInfoByUID(self.uid,['ClubId','DevoteCurrent'])#军团ID 
        data['ClubId'] = clubInfo.get('ClubId',0)
        data['ClubDvo'] = clubInfo.get('DevoteCurrent',0)
        data['ClubBox'] = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_CLUB).get('BoxCost')
        
        #装备传承花费 
        data['DivertCost'] = Gcore.loadCfg(Gcore.defined.CFG_EQUIP).get('DivertCost')
        data['DivertCostType'] = Gcore.loadCfg(Gcore.defined.CFG_EQUIP).get('DivertCostType')
        
        data['Inters'] = Gcore.getMod('Building_home', self.uid).getInters() #内政
        
        #获取场景14001 MapUI.getScene()搬过来的
        BuildingInfo = Gcore.getMod('Building',self.uid).getAllBuildingCoord()
        interactGids=Gcore.getMod('Interact',self.uid).getHaveMcoinGeneralIds()#获取有交流记录的武将ID Add by Yew
        data['Scene'] = {'BuildingInfo':BuildingInfo,'BuyMapInfo':[],'InteractGids':interactGids}
        
        #获取武将信息15013 Building_trainUI.GetGenerals()搬过来
        Generals = Gcore.getMod('General', self.uid).getLatestGeneralInfo()
        data['Generals'] = Generals if Generals else []
        
        #VIP折扣
        data['VipDiscount'] = {r['VipLevel']:r['Discount'] for r in Gcore.getCfg('tb_cfg_vip_up').values()}
        data['MaxWorkerNum'] = Gcore.loadCfg(Gcore.defined.CFG_BUILDING).get('MaxWorkerNum',5)
        
        #攻城等级
        data['FightLevel'] = Gcore.loadCfg(9301).get('FightLevel')
        
        #是否首次登录
        data['FirstLogin'] = 0 if data.pop('LoginTimes') else 1
        
        #军师和指引进度
        data['ArmyAdviserId'] = userProfile.get('ArmyAdviserId',0)
        data['GuideProcessId'] = userProfile.get('GuideProcessId',0)
        
        #进贡百分比
        data['GiveRatio'] = Gcore.loadCfg(1506).get('GiveRatio',0.05)
        
        #完成任务数量
        data['MissionFinish'] = Gcore.getMod('Mission',self.uid).getMissionFinishNum()
        
        #官网
        data['Website'] = Gcore.loadCoreCfg('Website')
        
        #心跳时间
        data['HeartBeatInterval'] = Gcore.config.HEARTBEAT_TIME
        
        
        #结束-----------------------------------
        runtime = time.time() - startTime
        if Gcore.IsServer: #调试计时
            row = {
                     'UserId':self.uid,
                     'OptId':10001,
                     'CallMethod':'PlayerMod.PlayerInfo',
                     'Param':'--skip',
                     'Response':'--skip',
                     'Runtime':runtime,
                     'RecordTime':Gcore.common.datetime(),
                     }
            self.db.insert('temp_runtime_log', row, isdelay=True)
        #-------------------------------------
        return data
    
    
    def addUserExp(self,getWay,amount=0,optId=0):
        '''
        :增加主角经验（动作触发）
        @param getWay: 用户获得经验方式0:直接加经验，1-99：消耗加经验 101-199： 事件加经验
        @param amount: if getWay==0:amount='增加的经验值';elif 1<1getWay<99:amount='消耗货币量';
        @return: 返回主角经验等级，当前经验
        '''
        
        expCfg = Gcore.getCfg('tb_cfg_exp_get',getWay)
        fields = ['UserLevel','UserExp']
        userInfo = self.db.out_fields('tb_user',fields,'UserId=%s'%self.uid)
        userLevel = userInfo['UserLevel']
        userExp = userInfo['UserExp']
        getExp = 0
          
        if expCfg:#动作增加经验方式
            segment = getWay/100#判断是消耗还是事件      
            if segment==0:#消耗
                factor1 = expCfg.get('Factor1',0)
                factor2 = expCfg.get('Factor2',0)
                getExp = int(factor1*amount+factor2*userLevel)
                
            elif segment==1 and self._getLimitOfEvent(getWay):#事件
                baseExp = expCfg.get('BaseExp',0)
                getExp = int(baseExp*(userLevel+1)*(1+userLevel/200.0)+1)
                
        elif getWay==0:#直接加经验
            getExp=amount
        
        #增加经验，同时更新等级
        if getExp>0:
            updateExp = self._calUserLevel(userLevel, userExp+getExp)
            self.db.update('tb_user',updateExp,'UserId=%s'%self.uid)
            newLevel = updateExp.get('UserLevel')
            
            #获得经验记录
            logData = {'UserId':self.uid,'GetWay':getWay,'OptId':optId,
                       'UserType':Gcore.getUserData(self.uid,'UserType'),
                       'UserLevel':newLevel,'ExpValue':getExp,'CreateTime':time.time()}
            self.db.insert('tb_log_exp',logData,isdelay=True)
            
            #主角升级
            if newLevel>userLevel:
                #升级推送
                Gcore.push(108,self.uid,{'UserLevel':newLevel})
                mMod = Gcore.getMod('Mission',self.uid)
                mMod.getNewMission(userLevel=newLevel)#用户升级查看有没有新任务
                Gcore.setUserData(self.uid, {'UserLevel':newLevel}) #更新缓存中的用户等级  Lizr
                Gcore.getMod('General',self.uid).touchGeneralLv(newLevel)
                Gcore.getMod('War',self.uid).touchActPoint(userLevel,newLevel) #更新行动力
                modActivity=Gcore.getMod('Activity',self.uid)#报错
                modActivity.growUpAward(newLevel, userLevel)#成长奖励活动Yew
                if newLevel >= Gcore.loadCfg(Gcore.defined.CFG_RANK_FIGHT).get('RankFightOpenLevel',20):
                    Gcore.getMod('RankFight',self.uid).joinRankFight() #每次升级都尝试加入排行榜 防止有漏
                    
            return updateExp
        else:
            return userInfo   
    
    def gainHonour(self,honourValue,optId=0):
        '''获得荣誉  Lizr 
        @param honourValue:荣誉值 +增加，-消耗
        @param optId:功能号 
        @author: zhanggh 6.4
        @return: 增加或消耗的荣誉
        '''
        userInfo = self.db.out_fields('tb_user',['UserHonour','UserLevel'],'UserId=%s'%self.uid)
        curHonour = userInfo['UserHonour']
        actionType = 1
        updateVal = curHonour+honourValue
        
        if honourValue<0:#消耗荣誉
            actionType = 2
            if curHonour <= 0:
                return 0
            if updateVal<0:
                updateVal = 0
                honourValue = -curHonour
        
        #更新荣誉
        self.db.update('tb_user',{'UserHonour':updateVal},'UserId=%s'%self.uid)
        
        #记录荣誉获得
        record = {'UserId':self.uid,'UserLevel':userInfo['UserLevel'],
                  'UserType':Gcore.getUserData(self.uid,'UserType'),
                  'Action':actionType,'HonourNumber':abs(honourValue),'OptId':optId,
                  'NowHonour':updateVal,'CreateTime':time.time()}
        self.db.insert('tb_log_honour',record,isdelay=True)
        
        #记录成就
        if actionType==1:
            recordData = {'ValType':0,'Val':honourValue}
            Gcore.getMod('Building_home',self.uid).achieveTrigger(5,recordData)
            Gcore.getMod('Mission',self.uid).missionTrigger(5,recordData)
            
        return honourValue

    
    def addProtectTime(self,second):
        '''添加保护时间By Yew  此方法是对的 by Lizr'''
        second = int(second)
        now=Gcore.common.nowtime()
        protectEndTime=self.getUserInfo('ProtectEndTime')
        if protectEndTime<now:
            protectEndTime=now+second
        else:
            protectEndTime=protectEndTime+second
        
        sql='UPDATE tb_user SET ProtectEndTime=%s WHERE UserId=%s'%(protectEndTime,self.uid)
        self.db.execute(sql)
        Gcore.redisM.hset('sgProtect', Gcore.redisKey(self.uid), protectEndTime) #更新总服redis 其他人不可以攻打
        #Gcore.sendmq(1, 10000, {'UserId':self.uid,'protectEndTime':protectEndTime}) #发送到总服更新 攻城查找表
        
        return protectEndTime   #返回保护结束时间 by qiudx 2013/06/27
        
    def addProtectHoldTime(self, second):
        '''添加藩国保护时间 by Qiudx'''
        second = int(second)
        now = Gcore.common.nowtime()
        protectHoldEndTime = self.getUserInfo('ProtectHoldEndTime')
        if protectHoldEndTime < now:
            protectHoldEndTime = now + second
        else:
            protectHoldEndTime += second
        sql = 'UPDATE tb_user SET ProtectHoldEndTime=%s WHERE UserId=%s'%(protectHoldEndTime, self.uid)
        self.db.execute(sql)
        Gcore.redisM.hset('sgProtectHold', Gcore.redisKey(self.uid), protectHoldEndTime)
        return protectHoldEndTime
    
    
    def beFighting(self,Fighter,UserId=None):
        '''被人攻打中'''
        t = 180 if Gcore.TEST else 180
        if not UserId:
            UserId = self.uid
        sql = "UPDATE tb_user SET FightEndTime=UNIX_TIMESTAMP()+%s, Fighter='%s' WHERE UserId=%s"%(t,Fighter,UserId)
        self.db.execute(sql)
        Gcore.push(105, UserId, {'FightRestTime':t,'Fighter':Fighter}, Type=1) #推送被攻打
        print 'ps beFighting',sql
    
    def beFightEnd(self,UserId=None):
        '''被人攻打结束'''
        if not UserId:
            UserId = self.uid
        sql = "UPDATE tb_user SET FightEndTime=UNIX_TIMESTAMP()-3 WHERE UserId=%s"%UserId
        self.db.execute(sql)
        #推送被攻打结束
        para = {"UserId":UserId, "Type":0, "Data":{} }
        from sgLib.mqManager import MqManager
        MqManager()._notifyServer(8888, para)
        print 'ps beFightEnd',sql
    
    
#-------------------------------END模块内部接口--------------------------------
    def initUser(self):
        '''初始化用户 '''
        data = {}
        userId = self.uid
        
        init_tables = ['tb_inter','tb_club_tech','tb_soldier'] #初始化用户相关表
        for table in init_tables:
            self.db.execute("INSERT INTO `%s` (UserId) VALUES('%s')"%(table,userId))
            
        buildCfg = Gcore.loadCfg(CFG_BUILDING)
        data = {'UserId':userId, 'Jcoin':buildCfg['InitJcoin'],'Gcoin':buildCfg['InitGcoin']}
        self.db.insert('tb_currency',data)
        #self.db.insert('tb_war_action',{'UserId':self.uid})
        
        initAlls = buildCfg['InitBuild']
        
        for _, data in enumerate(initAlls):
            tmpData = copy.deepcopy(data)
            tmpData['UserId'] = userId
            tmpData['xSize'] = 0
            tmpData['ySize'] = 0
            size = Gcore.getCfg('tb_cfg_building',data['BuildingType'],'Size')
            xy = size.split('*')
            if '*' not in size:
                xy.append(xy[0])
            tmpData['xSize'] = int(xy[0])
            tmpData['ySize'] = int(xy[1])
            tmpData['CompleteTime'] = int(time.time() - 5)
            tmpData['LastChangedTime'] = tmpData['CompleteTime'] - Gcore.getCfg('tb_cfg_building_up', (tmpData['BuildingType'], 1), 'CDValue')
            tmpData['CoinType'] = Gcore.getCfg('tb_cfg_building', tmpData['BuildingType'], 'CoinType')
            tmpData['BuildingPrice'] = Gcore.getCfg('tb_cfg_building_up', (tmpData['BuildingType'], 1), 'CostValue')
            buildingStatus = tmpData.pop('BuildingStatus')
            buildingId = self.db.insert(self.tb_building(),tmpData)
            #初始给予600兵
            if tmpData['BuildingType'] == 7:
                initSoldier = buildCfg['InitSoldier']
                campMod = Gcore.getMod('Building_camp', self.uid)
                campMod.changeSoldierNum({initSoldier['SoldierType']: initSoldier['SoldierNum']})
            #初始系统给予的武将
            if buildingStatus and tmpData['BuildingType'] == 18:
                generalMod = Gcore.getMod('General', self.uid)
                generalId = generalMod.addNewGeneral(buildingStatus, buildingId, time.time(), flag=True, getWay=3)
                #给初始武将添加装备
                myGenerals = generalMod.getMyGenerals()
                for g in myGenerals:
                    if g['GeneralType'] == int(buildingStatus):
                        equipTypes = buildCfg['InitEquips']
                        equipCfg = Gcore.getCfg('tb_cfg_equip').values()
                        initEquips = filter(lambda e: e['EquipType'] in equipTypes, equipCfg)
                        
                        bagMod = Gcore.getMod('Bag', self.uid)
                        for e in initEquips:
                            equipId = bagMod.addGoods(1, e['EquipType'])
                            generalMod.changeEquip(g, e['EquipPart'], equipId[0])
                #布防武将
                generalPosition = buildCfg['InitGeneralDefense']
                generalDefenseData = {'GeneralId': generalId, 'x': generalPosition['x'], 'y': generalPosition['y'], 'UserId': self.uid}
                self.db.insert('tb_wall_general', generalDefenseData)
            #初始给予玩家铜钱和军资
            elif buildingStatus:
                storageNum = Gcore.getCfg('tb_cfg_building_up', (data['BuildingType'],data['BuildingLevel']), 'SaveValue')
                if storageNum:
                    coinType = 2 if data['BuildingType']==2 else 3
                    print '填满',storageNum
                    values = {
                        "UserId": userId,
                        "BuildingId": buildingId,
                        "StorageNum": storageNum,
                        "BuildingType": data['BuildingType'],
                        "CoinType": coinType,
                        "LastChangedTime": time.time(),
                    }
                    self.db.insert('tb_building_storage', values)
        #初始防御工事
        initDefense = buildCfg['InitDefense']
        for defense in initDefense:
            size = Gcore.getCfg('tb_cfg_soldier', defense['SoldierType'], 'Size')
            xSize, ySize = size.split('*')
            ySize, xSize  = int(xSize), int(ySize) #横放
            defenseCfg = Gcore.getCfg('tb_cfg_soldier_up', (defense['SoldierType'], 1))
            cost = defenseCfg.get('MakeCost')
            defenseData = {'SoldierType': defense['SoldierType'],
                    'SoldierLevel': 1,
                    'MakeCost': cost,
                    'UserId': self.uid,
                    'x': defense['x'],
                    'y': defense['y'],
                    'xSize': xSize,
                    'ySize': ySize,
                    }
            defenseTable = self.tb_wall_defense()
            self.db.insert(defenseTable, defenseData)
            
        Gcore.getMod('Redis',self.uid).offCacheWallDefense() #缓存布防工事
        Gcore.getMod('Redis',self.uid).offCacheGeneral()     #缓存布防武将
        
            
        

    def getMapBuyTimes(self):
        '''获取用户已购买'''
        return self.db.out_field('tb_user','BuyMapTimes',"UserId=%s"%self.uid)
        
        
    def getUserCoin(self):
        GoldCoin = self.db.out_field('tb_user','GoldCoin',"UserId=%s"%self.uid)
        dic_con = self.db.out_fields('tb_currency',['Jcoin','Gcoin', 'Mcoin'],"UserId=%s"%self.uid)
        return {'GoldCoin':GoldCoin, 'Jcoin':dic_con['Jcoin'], 'Gcoin':dic_con['Gcoin'], 'Mcoin':dic_con['Mcoin']}
    
    def getUserProfile(self,fields='*'):
        '''获取用户属性'''
        row = self.db.out_fields('tb_user_profile',fields,'UserId=%s'%self.uid)
        return row
    
    def setUserProfile(self,updateDict={}):
        '''更新用户属性'''
        assert isinstance(updateDict, dict) 
        if not self.db.count('tb_user_profile','UserId=%s'%self.uid):
            self.db.insert('tb_user_profile',{'UserId':self.uid})
        return  self.db.update('tb_user_profile',updateDict,'UserId=%s'%self.uid)
        
    def getUserBaseInfo(self,fields=[]):
        '''获取荣誉值,阵营,昵称,vip等级等基础信息'''
        if not fields:
            fields = ['UserHonour','UserCamp','NickName',
                      'VipLevel','BuyMapTimes', 'WorkerNumber',
                      'UserIcon','UserExp','UserLevel']
        res = self.db.out_fields('tb_user',fields,'UserId=%s'%self.uid)
        #print 'getUserBaseInfo', self.db.sql
        return res
    
    def getUserWorker(self):
        '''获取工匠信息'''
        worker = {}
        worker['WorkerFree'] = self.db.out_field('tb_process_record','COUNT(*)', 'StopTime > %s AND UserId=%s'%(time.time(), self.uid))
        worker['WorkerTotal'] = self.db.out_field('tb_user','WorkerNumber',"UserId=%s"%self.uid)
        worker['WorkerFree'] = worker['WorkerTotal']-worker['WorkerFree']
        return worker
    
    def addWorker(self,workerNum):
        '''
        :更新用户表工匠数量并插入一条工匠添加记录
        @param workerNum:当前工匠
        '''
        ctime = comm.datetime()
        self.db.update('tb_user',{'WorkerNumber':workerNum+1},'UserId='+str(self.uid))
        workerRecord = {'UserId':self.uid,'WorkerNumCurrent':workerNum,\
                        'WorkerNumExpand':workerNum+1,'CreateTime':ctime}
        self.db.insert('tb_worker_expand',workerRecord)

    
    def vipAddTotal(self, optId, goldNum):
        '''
        :玩家充值黄金，增加玩家累积黄金，更新Vip等级
        @param goldNum:增加的黄金数量
        '''
        userInfo = self.getUserInfo(['VipLevel','VipTotalPay'])
        curLevel = userInfo.get('VipLevel')
        curVipTotal = userInfo.get('VipTotalPay')
        
        totalPay = goldNum+curVipTotal
        levelCfg = Gcore.getCfg('tb_cfg_vip_up')
        levelUp = max([levelCfg[level]['VipLevel'] for level in levelCfg if totalPay>=levelCfg[level]['TotalPay']])
        data = {'VipTotalPay':totalPay,'VipLevel':levelUp}
        self.db.update('tb_user',data,'UserId=%s'%self.uid)
        if levelUp>curLevel:#VIP升级
            interMod = Gcore.getMod('Inter',self.uid)
            interMod.updateInterVip()#更新VIP内政加成
            Gcore.setUserData(self.uid,{'VipLevel':levelUp}) #更新用户缓存  Lizr
            Gcore.push(107,self.uid,{'VipLevel':levelUp}) #推送给前端升级 Lizr
        if curVipTotal==0:
            #增加首冲奖励
            Gcore.getMod('Activity',self.uid).insertGifts(1,0)
        #发送系统邮件
        mailMod = Gcore.getMod('Mail', self.uid)
        mailMod.sendSystemMail(self.uid, [], optId, other=[goldNum,])
        
        return levelUp
    
    #  UserExp UserLevel

    def _getLimitOfEvent(self,getWay): 
        '''
        :查询当天事件获取经验限制
        @param getWay:
        '''
        import datetime
        today = time.mktime(datetime.date.today().timetuple())
        now = time.time()
        where = 'UserId=%s AND GetWay=%s AND (CreateTime BETWEEN %s AND %s)'%(self.uid,getWay,today,now)
        nums = self.db.out_field('tb_log_exp','Count(1)',where)
        limit = Gcore.getCfg('tb_cfg_exp_get',getWay,'DayLimit')
        if nums<limit:
            return True
        else:
            return False
        
    def _calUserLevel(self,level,exp):
        '''
        :计算主角升级后等级
        @param exp:增加的经验
        '''
        result = {'UserLevel':level,'UserExp':exp}
        expNeed = Gcore.getCfg('tb_cfg_exp_level',level+1,'Exp')
        if expNeed is None:
            return result
        if exp<expNeed:
            return result
        else:
            return self._calUserLevel(level+1, exp-expNeed)
        
    def getUserNum(self):
        return self.db.out_field('tb_user','Count(1)','1')
    
    def getHonRanking(self,offset,pageSize):
        '''查询玩家荣誉值排名'''
        fields = ['UserId','NickName','UserIcon','UserLevel','VipLevel','UserHonour']
        rs = self.db.out_rows('tb_user',fields,'1 ORDER BY UserHonour DESC,VipLevel DESC,UserLevel DESC LIMIT %s,%s'%(offset,pageSize))
        print self.db.sql
        return rs
    
    def getHonRankNum(self,userInfo=None):
        '''查询排名数'''
        if userInfo is None:
            userInfo=self.db.out_fields('tb_user',['UserHonour','VipLevel','UserLevel'],'UserId=%s'%self.uid)
        userHonour = userInfo.get('UserHonour',0)
        userLevel = userInfo.get('UserLevel',0)
        vipLevel = userInfo.get('VipLevel',0)
        where1 = 'UserHonour>%s '%userHonour
        where2 = ' OR (UserHonour=%s AND VipLevel<%s) '%(userHonour,vipLevel)
        where3 = ' OR (UserHonour=%s AND VipLevel=%s AND UserLevel<%s) '%(userHonour,vipLevel,userLevel)
        where4 = ' OR (UserHonour=%s AND VipLevel=%s AND UserLevel=%s AND UserId<%s) '%(userHonour,vipLevel,userLevel,self.uid)
        where = where1+where2+where3+where4
        num=self.db.out_field('tb_user','count(1)',where)
        return num+1
    
    def sendCampGift(self,optId,camp=1):
        '''发放推荐阵营礼包'''
        gCfg = [g for g in Gcore.getCfg('tb_cfg_gift_camp').values() if g['Camp']==camp]
        rewardMod = Gcore.getMod('Reward',self.uid)
        for g in gCfg:
            rewardMod.reward(optId,'',g['GoodsType'],g['GoodsId'],g['GoodsNum'])
    
    def guideCompleteLog(self,GuideProcessId):
        '''新手指引完成日志'''
        if not self.db.count('tb_log_user_guide','UserId=%s AND GuideProcessId=%s'%(self.uid,GuideProcessId)):
            ins = {'UserId':self.uid, 'GuideProcessId':GuideProcessId,'CompleteTime':Gcore.common.nowtime()}
            self.db.insert('tb_log_user_guide',ins)
            

if __name__ == '__main__':
    uid = 1004
    c = PlayerMod(uid)
#    c.guideCompleteLog(2)
#     c.beFightEnd(1005)
#    print c.addUserExp(0, 122222200)
#     d = c.PlayerInfo() #用户登录

#     Gcore.printd(d)
#     for i in xrange(10):
#         c.addProtectTime(100)
#    c.initUser()
#    print c.getUserWorker()
#     print Gcore.getCfg('tb_cfg_nickname','0')
#    print Gcore.loadCfg( Gcore.defined.CFG_ITEM ).get('exchange')

#    print c.getUserNum()
#     print c.gainHonour(-22)
#    Gcore.runtime()
#    print c.initUser()
#    Gcore.printd(d)
#    c.gainHonour(1)
#    print c.getHonRankNum()
#    c.beFighting('你大爷')
#     import time;time.sleep(2)
#     Gcore.runtime()
#     print c._getLimitOfEvent(101)
#     print c.sendCampGift(1,3)
#     print c.getHonRanking(0,999)
    