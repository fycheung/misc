#coding:utf8
#author:zhoujingjiang
#date:2013-3-6
#comment:武馆外部接口

import sys
import math
import copy
import time

from sgLib.core import Gcore, inspector
from sgLib.common import calSpeedCost

class Building_groundUI(object):
    '''武馆功能外部接口'''
    def __init__(self, uid):
        self.mod = Gcore.getMod('Building_ground', uid)
        self.uid = uid

    @inspector(15090, ['BuildingId', 'GeneralId', 'PractiseTime'])
    def PractiseGeneral(self, param = {}):
        '''武馆：训练武将'''
        optId = 15090

        #参数
        BuildingId = param['BuildingId']
        GeneralId = param['GeneralId']
        PractiseTime = param['PractiseTime']
        TimeStamp = param['ClientTime'] #使用客户端时间 
        Flag = param.get('Flag') #Flag-True定长训练，False变长训练

        #建筑信息
        modBuilding = Gcore.getMod('Building', self.uid)
        BuildingInfo = modBuilding.getBuildingById(BuildingId, TimeStamp=TimeStamp)
        if not BuildingInfo:
            return Gcore.error(optId, -15090001) #玩家没有该建筑
        if BuildingInfo["BuildingState"] == 1:
            return Gcore.error(optId, -15090002) #武馆正在建造
        if BuildingInfo["BuildingType"] != 14:
            return Gcore.error(optId, -15090003) #不是武馆
        BuildingLevel = BuildingInfo["BuildingRealLevel"]

        #武将信息
        modGeneral = Gcore.getMod('General', self.uid)
        Generals = modGeneral.getMyGenerals()
        if GeneralId not in [General['GeneralId'] for General in Generals]:
            return Gcore.error(optId, -15090004) #玩家没有此武将

        #训练信息
        PractiseQueues, Generals = self.mod.touchPractise(Generals, TimeStamp)
        if GeneralId in [PractiseQueue["GeneralId"] for PractiseQueue in PractiseQueues]:
            return Gcore.error(optId, -15090005) #武将正在训练

        #正在训练的武将的数量
        PractisingNum = len(PractiseQueues)
        #武馆的可训练数量
        GroundCfg = Gcore.getCfg('tb_cfg_ground', BuildingLevel)
        MaxPractiseNum = GroundCfg["TrainNum"]

        if PractisingNum >= MaxPractiseNum:
            return Gcore.error(optId, -15090006) #训练位已满

        if (not Flag) and (not 0 < int(PractiseTime)/60. <= 720): #训练时间在0-720分钟
            return Gcore.error(optId, -15090007) #训练时间不正确
        elif Flag:
            PractiseTime = 12 * 60 * 60 #训练12小时

        modCoin = Gcore.getMod('Coin', self.uid)
        CoinType = 3 #训练花费铜币
        CoinValue = GroundCfg["TrainCost"] * math.ceil(PractiseTime/60)#训练花费
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        #武将训练花费受内政9影响
        CoinValue = Gcore.getMod('Inter',self.uid).getInterEffect(9, CoinValue)

        pay = modCoin.PayCoin(optId, CoinType, CoinValue, classMethod, param)
        if pay < 0:
            return Gcore.error(optId, -15090008) #支付失败

        #插入训练记录
        TrainExp = GroundCfg["TrainExp"]
        self.mod.createPractise(GeneralId, TrainExp, TimeStamp, PractiseTime, pay)
        
        body={"Cost":CoinValue}
        body['Coin%s'%CoinType] = modCoin.getCoinNum(CoinType)
        recordData = {'uid':self.uid,'ValType':0,'Val':1}#成就、任务记录
        return Gcore.out(optId, body=body, mission=recordData)

    @inspector(15091, ["GeneralId"])
    def SpeedUpPractise(self, param={}):
        '''武馆：取消或加速训练'''
        optId = 15091

        GeneralId = param["GeneralId"]
        TimeStamp = param["ClientTime"]
        Flag = param.get('Flag') #Flag-False加速训练 ；1取消训练

        modGeneral = Gcore.getMod('General', self.uid)
        Generals = modGeneral.getMyGenerals()
        GeneralsCopy = copy.deepcopy(Generals)

        PractiseQueues, Generals = self.mod.touchPractise(Generals, TimeStamp)

        if GeneralId not in [PractiseQueue["GeneralId"] for PractiseQueue in PractiseQueues]:
            return Gcore.error(optId, -15091001) #该武将没训练

        #计算花费，经验值
        TotalTime = 0
        SpeedTime = 0
        ExpValue = 0
        PractiseId = None
        for PractiseQueue in PractiseQueues:
            if PractiseQueue["GeneralId"] == GeneralId:
                TotalTime = PractiseQueue["CompleteTime"] - PractiseQueue["StartTime"]
                ExpValue = int(math.ceil((TotalTime//60) * PractiseQueue["TrainExp"]))
                SpeedTime = PractiseQueue["CompleteTime"] - PractiseQueue["StartTime"]
                PractiseId = PractiseQueue['PractiseId']
                TrainPay = PractiseQueue['TrainPay']
                
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        
        body = {} #返回信息

        #将当前的武将的信息删除
        body['Generals'] = [General for General in Generals 
                            if General['GeneralId'] != GeneralId]
        #将当前武将的训练队列删除
        body['PractiseQueues'] = [PractiseQueue for PractiseQueue in PractiseQueues
                                  if PractiseQueue['GeneralId'] != GeneralId]
        if not Flag: #加速
            CoinType = 1
            CoinValue = calSpeedCost(4, SpeedTime)
            pay = modCoin.PayCoin(optId, CoinType, CoinValue, classMethod, param)
            if pay < 0:
                return Gcore.error(optId, -15091002) #支付失败
        
            #更新武将表
            General = self.mod.getGeneralById(GeneralsCopy, GeneralId)
            General = modGeneral.incGeneralExp(General, ExpValue)
            body['Generals'].append(General)
            
            #从训练表中删除记录
            self.mod.deletePractise(PractiseId)
            
            recordData = {'uid':self.uid,'ValType':0,'Val':1}#成就、任务记录
            body['Cost'] = pay
            body['SpeedTime'] = SpeedTime
            return Gcore.out(optId, body=body,
                             mission=recordData)
        elif Flag == 1: #取消
            #返钱
            coinValue = (SpeedTime / TotalTime) * TrainPay
            gain = modCoin.GainCoin(optId, 3, coinValue, classMethod, param)
            if gain is False:
                return Gcore.error(optId, -15091003) #增加货币失败
            
            #删除训练记录
            self.mod.deletePractise(PractiseId)
            
            #更新武将信息
            modGeneral = Gcore.getMod('General', self.uid)
            General = self.mod.getGeneralById(Generals, GeneralId)
            modGeneral.updateGeneralById(General, GeneralId)
            body['Generals'].append(General)

            
            body['GainValue'] = gain
            body['TheoryGainValue'] = coinValue
            body['CoinType'] = 3
            return Gcore.out(optId, body=body)
        else:
            return Gcore.error(optId, -15091004) #Flag不正确

    @inspector(15092)
    def GetPractiseInfo(self, param={}):
        '''获取训练信息'''
        optId = 15092

        TimeStamp = param['ClientTime']
        print 'TimeStamp', TimeStamp
        print 'server time', time.time()

        modGeneral = Gcore.getMod('General', self.uid)
        Generals = modGeneral.getMyGenerals()

        PractiseQueues, Generals = self.mod.touchPractise(Generals, TimeStamp)
        return Gcore.out(optId, body = {"TimeStamp":TimeStamp, 
                                        "PractiseQueues":PractiseQueues,
                                        "Generals":Generals})

    @inspector(15093, ['BuildingId', 'GeneralId'])
    def RapidPractise(self, param={}):
        '''突飞训练'''
        optId = 15093

        #参数
        BuildingId = param['BuildingId']
        GeneralId = param['GeneralId']
        TimeStamp = param['ClientTime']

        #武馆信息
        modBuilding = Gcore.getMod('Building', self.uid)
        BuildingInfo = modBuilding.getBuildingById(BuildingId, TimeStamp=TimeStamp)
        if not BuildingInfo:
            return Gcore.error(optId, -15093001) #玩家没有该武馆
        if BuildingInfo['BuildingState'] == 1:
            return Gcore.error(optId, -15093002) #武馆正在建造
        if BuildingInfo["BuildingType"] != 14:
            return Gcore.error(optId, -15090003) #不是武馆
        BuildingLevel = BuildingInfo['BuildingRealLevel']

        #武将信息
        modGeneral = Gcore.getMod('General', self.uid)
        MyGenerals = modGeneral.getMyGenerals()
        General = None
        for MyGeneral in MyGenerals:
            if str(MyGeneral['GeneralId']) == str(GeneralId):
                General = MyGeneral
        if not General:
            return Gcore.error(optId, -15093004) #玩家没有该武将

        #突飞训练参数
        MaxRapidPractiseCount = 100 #读配置
        RapidPractiseTime = 30 * 60 #突飞训练的时间长度
        MaxRapidPractiseCD = 8 * 60 * 60
        
        #突飞训练记录
        TodayDate = time.strftime('%Y-%m-%d', time.localtime(TimeStamp))
        modGround = Gcore.getMod('Building_ground', self.uid)
        RapidRecord = modGround.getRapidRecord(TodayDate)
        
        # + 突飞次数，冷却时间
        if not RapidRecord:
            RapidCount = 0
            IsOverFlow = 0
            
            CDValue = 0
        else:
            RapidCount = RapidRecord['PractiseCount']
            IsOverFlow = RapidRecord['IsOverFlow']

            TotalCD = RapidRecord['CDValue']
            SecondsPast = TimeStamp - RapidRecord['LastRapidTime']
            CDValue = max(TotalCD - SecondsPast, 0)
            if CDValue <= 0:
                IsOverFlow = 0

        if IsOverFlow:
            return Gcore.error(optId, -15093005) #等待冷却结束
        if RapidCount >= MaxRapidPractiseCount:
            return Gcore.error(optId, -15093006) #已达最大突飞次数
        if CDValue + RapidPractiseTime > MaxRapidPractiseCD:
            IsOverFlow = 1 #超上限
        
        #计算经验和花费
        GroundCfg = Gcore.getCfg('tb_cfg_ground', BuildingLevel)
        TrainExp = GroundCfg['TrainExp']
        TrainCost = GroundCfg['TrainCost']
        TrainCostType = 3

        TrainExp = TrainExp * (RapidPractiseTime // 60) #突飞的经验
        TrainCost = TrainCost * (RapidPractiseTime // 60) #突飞的花费
        
        # + 武将训练受内政影响
        modInter = Gcore.getMod('Inter', self.uid)
        TrainCost = modInter.getInterEffect(9, TrainCost)
        
        #扣钱
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        pay = modCoin.PayCoin(optId, TrainCostType, TrainCost, classMethod, param)
        if pay < 0:
            return Gcore.error(optId, -15093007) #扣钱失败
        
        #给武将加经验
        modGeneral.incGeneralExp(General, TrainExp)
        
        #加上训练信息
        PractiseQueues, Generals = self.mod.touchPractise(MyGenerals, TimeStamp)
        
        #更新突飞训练表
        CDValue = CDValue + RapidPractiseTime if not IsOverFlow else MaxRapidPractiseCD
        LastRapidTime = TimeStamp
        PractiseCount = RapidCount + 1
        LastChangedDate = TodayDate
        modGround.changeRapidRecord(CDValue, LastRapidTime, PractiseCount, LastChangedDate, IsOverFlow)
        
        body = {}
        body['PractiseQueues'] = PractiseQueues
        body['Generals'] = Generals
        body['IsOverFlow'] = IsOverFlow
        body['CDValue'] = CDValue
        body['CostValue'] = pay
        body['CostType'] = TrainCostType
        return Gcore.out(optId, body=body)

    @inspector(15094, )
    def SpeedRapidPractise(self, param={}):
        '''加速突飞训练的冷却时间'''
        optId = 15094
        
        IsSpeed = param.get('IsSpeed')
        TimeStamp = param['ClientTime']
        
        TodayDate = time.strftime('%Y-%m-%d', time.localtime(TimeStamp))
        modGround = Gcore.getMod('Building_ground', self.uid)
        RapidRecord = modGround.getRapidRecord(TodayDate)
        
        if not RapidRecord:
            RapidCount = 0
            IsOverFlow = 0
            
            CDValue = 0
        else:
            RapidCount = RapidRecord['PractiseCount']
            IsOverFlow = RapidRecord['IsOverFlow']
            
            TotalCD = RapidRecord['CDValue']
            SecondsPast = TimeStamp - RapidRecord['LastRapidTime']
            CDValue = max(TotalCD - SecondsPast, 0)
            if CDValue <= 0:
                IsOverFlow = 0
        
        if not IsSpeed: #不是加速
            body = {}
            body['TimeStamp'] = TimeStamp
            body['IsOverFlow'] = IsOverFlow
            body['CDValue'] = CDValue
            body['RapidCout'] = RapidCount
            return Gcore.out(optId, body=body)
        
        #加速冷却时间
        if CDValue <= 0:
            return Gcore.error(optId, -15094001) #冷却时间为0
        
        CoinType = 1
        CoinValue = calSpeedCost(4, CDValue)
        
        #扣钱
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        pay = modCoin.PayCoin(optId, CoinType, CoinValue, classMethod, param)
        if pay < 0:
            return Gcore.error(optId, -15094002) #扣钱失败
        
        #更新突飞记录表
        modGround.speedCD()
        
        body = {}
        body['GoldenCost'] = pay
        body['CDValue'] = 0
        body['SpeedTime'] = CDValue
        body['IsOverFlow'] = 0
        body['TimeStamp'] = TimeStamp
        return Gcore.out(optId, body=body)
