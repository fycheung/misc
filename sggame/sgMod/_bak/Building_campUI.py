#coding:utf8
#author:zhoujingjiang
#date:2013-1-30
#游戏外部接口:兵营，佣兵处，工坊。

import time
import sys
import math

from sgLib.core import Gcore, inspector
from sgLib.common import calSpeedCost

class Building_campUI(object):
    '''兵营，佣兵处，工坊功能外部接口'''
    def __init__(self, uid):
        self.uid = uid

    @inspector(15030, ['BuildingId'])
    def GetSpawnInfo(self, param={}):
        '''兵营：获取征兵信息 或 工坊：获取制造信息'''
        optId = 15030
        BuildingId = param["BuildingId"]
        TimeStamp = param['ClientTime']

        modCamp = Gcore.getMod('Building_camp', self.uid) 
        modCamp.getSoldierNum(TimeStamp)
        TrainQueues = modCamp.getSoldierProcess(BuildingId)
        TrainQueues = sorted(TrainQueues, key=lambda dic:dic["ProcessId"])        
        TrainLst = {}
        for ind, queue in enumerate(TrainQueues, start=1):
            TrainLst[ind] = {'SoldierType':queue['SoldierType'],
                             'SpawnNumRest':queue['SpawnNumRest']}
        TrainDict = {"SoldierTraining":TrainLst, "TimeStamp":TimeStamp}
        return Gcore.out(optId, TrainDict)

    @inspector(15031, ['BuildingId', 'SoldierType', 'CurNum', 'Flag'])
    def SetCurNum(self, param = {}):
        '''兵营：设置士兵的数量 或 工坊：设置器械的数量'''
        optId = 15031

        #参数
        BuildingId = param["BuildingId"] #兵营或工坊ID
        SoldierType = param["SoldierType"] #兵种类型
        CurNum = param["CurNum"] #设置的数量
        TimeStamp = param['ClientTime'] #客户端时间戳
        Flag = param['Flag'] #1，兵营；非1，工坊。

        if CurNum < 0:
            return Gcore.error(optId, -15031001) #训练数量不能小于0 

        modCamp = Gcore.getMod('Building_camp', self.uid)
        SoldierClass = modCamp.isSameCamp(SoldierType)
        if Flag==1 and (SoldierClass!=1):
            return Gcore.error(optId, -15031002) #不是士兵
        elif Flag!=1 and (SoldierClass!=2):
            return Gcore.error(optId, -15031003) #不是器械

        modBuilding = Gcore.getMod('Building', self.uid)
        BuildingInfo = modBuilding.getBuildingById(BuildingId, TimeStamp=TimeStamp)
        if not BuildingInfo:
            return Gcore.error(optId, -15031004) #该玩家没有这个建筑
        if BuildingInfo['BuildingState'] != 0:
            return Gcore.error(optId, -15031005) #建筑不在空闲状态
        BuildingLevel = BuildingInfo['BuildingRealLevel']

        if (Flag==1) and BuildingInfo['BuildingType'] != 6:
            return Gcore.error(optId, -15031006) #该建筑不是兵营
        elif (Flag!=1) and BuildingInfo['BuildingType'] != 8:
            return Gcore.error(optId, -15031007) #该建筑不是工坊

        OpenLevel = Gcore.getCfg('tb_cfg_soldier', SoldierType, 'OpenLevel')
        if OpenLevel > BuildingLevel:
            return Gcore.error(optId, -15031008) #没有达到开放等级

        Buildings = modBuilding.getBuildingByType(7, TimeStamp=TimeStamp)
        MaxSoldierNum = modCamp.getMaxSoldierNum(Buildings)
        Soldiers = modCamp.getSoldierNum(TimeStamp)
        TotalSoldierNum = sum(Soldiers.values()) if Soldiers else 0

        SoldierProcess = modCamp.getSoldierProcess()
        TotalTrainingNum = 0 #所有兵营的征兵数量之和
        AllTrainingNum = 0 #该兵营训练的士兵的所有数量
        NumInTraining = 0 #该类型的征兵数量
        for queue in SoldierProcess:
            if queue["SoldierType"] == SoldierType \
                and queue['BuildingId'] == int(BuildingId):
                NumInTraining = queue["SpawnNumRest"]
            if queue['BuildingId'] == int(BuildingId):
                AllTrainingNum += queue["SpawnNumRest"]
            TotalTrainingNum += queue["SpawnNumRest"]

        #读配置
        MakeValue = Gcore.getCfg('tb_cfg_building_up', 
                                 (6, BuildingInfo["BuildingRealLevel"]), 
                                 "MakeValue")
        diff = CurNum - NumInTraining #新增的数量
        if AllTrainingNum + diff > MakeValue:
            return Gcore.error(optId, -15031009) #超过了兵营训练上限
        if TotalSoldierNum + TotalTrainingNum + diff > MaxSoldierNum:
            return Gcore.error(optId, -15031010) #超过了校场上限

        if Flag == 1:
            modBook = Gcore.getMod('Book', self.uid)
            SoldiersScience = modBook.getTechsLevel(1, TimeStamp)
            SoldierLevel = SoldiersScience[SoldierType]
        else:
            SoldierLevel = 0
        SoldierUpCfg = Gcore.getCfg('tb_cfg_soldier_up',
                                    (SoldierType, SoldierLevel))
        MakeCost = SoldierUpCfg['MakeCost']
        coinType = SoldierUpCfg['MakeCostType']

        modCoin = Gcore.getMod('Coin', self.uid)
        modInter = Gcore.getMod('Inter', self.uid)
        coinValue = MakeCost * diff
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        
        print '正在训练的数量', NumInTraining
        print 'CurNum', CurNum
        print '没受内政：增加,货币%s:%s' % (coinType, abs(coinValue)) if diff < 0 else '减少,货币%s:%s' % (coinType, abs(coinValue))
        if diff > 0:
            coinValue = modInter.getInterEffect(6, coinValue)
            pay = modCoin.PayCoin(optId,coinType,coinValue,classMethod,param) 
            print 'pay', pay
            if pay < 1:
                return Gcore.error(optId, -15031010) #支付失败
        elif diff < 0:
            coinValue *= -1
            coinValue = modInter.getInterEffect(6, coinValue)
            gain = modCoin.GainCoin(optId,coinType,coinValue,classMethod,param)
            print 'gain', gain
            if gain < 0:
                return Gcore.error(optId, -15031011) #增加货币失败
        else:
            return Gcore.error(optId, -15031012) #未改变数量

        if NumInTraining == 0:
            modCamp.createSoldierProcess(CurNum, SoldierType, BuildingId, BuildingLevel, TimeStamp)
        else:
            modCamp.updateSoldierProcess(CurNum, SoldierType, BuildingId)
        
        recordData = {'uid':self.uid,'ValType':SoldierType,'Val':diff}#成就、任务记录 
        return Gcore.out(optId, 
                         body = {"Cost":coinValue, "TimeStamp":TimeStamp},
                         mission=recordData,
                         achieve=recordData)

    @inspector(15032, ['BuildingId', "SoldierType", "Flag"])
    def SpeedUpTraining(self, param = {}):
        '''兵营：加速征兵  或  工坊：加速制造 或  佣兵处：雇佣''' 
        optId = 15032

        BuildingId = param['BuildingId']
        SoldierType = param['SoldierType']
        TimeStamp = param['ClientTime']
        Flag = param['Flag'] #Flag：1，兵营；2，工坊；3，佣兵处。

        SoldierCfg = Gcore.getCfg('tb_cfg_soldier')
        if Flag == 3:
            HireNum = param['HireNum']
            if HireNum <= 0:
                return Gcore.error(optId, -15032001) #雇佣数量必须大于0
            HireSoldierType = [k for (k, v) in SoldierCfg.iteritems() if v["SoldierSide"] == 4]
            if SoldierType not in HireSoldierType:
                return Gcore.error(optId, -15032002) #兵种不是雇佣兵

        modCamp = Gcore.getMod('Building_camp', self.uid)
        modBuilding = Gcore.getMod('Building', self.uid)
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)

        Buildings = modBuilding.getBuildingByType(7, TimeStamp=TimeStamp)
        Soldiers = modCamp.getSoldierNum(TimeStamp)
        SoldierNum = sum(Soldiers.values()) if Soldiers else 0
        MaxNum = modCamp.getMaxSoldierNum(Buildings)

        if Flag == 3: #佣兵处
            #当天已雇佣的数量
            TodayDate = time.strftime('%Y-%m-%d', time.localtime(TimeStamp))
            HireInfo = modCamp.getHireByDate(BuildingId, TodayDate)
            print '今天已佣兵', HireInfo
            
            if not HireInfo: #当天未雇佣 或 雇佣表中没有该佣兵处的雇佣记录。
                print '今天尚未佣兵'
                HireInfo = {}
                for st in HireSoldierType:
                    HireInfo['Soldier%s'%st] = 0
                AlreadyHireNum = 0
            else:
                AlreadyHireNum = sum(HireInfo.values())

            #雇佣上限
            BuildingInfo = modBuilding.getBuildingById(BuildingId, TimeStamp=TimeStamp)
            if not BuildingInfo:
                return Gcore.error(optId, -15032003) #玩家没有该建筑 
            if BuildingInfo['BuildingState'] == 1:
                return Gcore.error(optId, -15032004) #建筑正在建造
            if BuildingInfo["BuildingType"] != 9:
                return Gcore.error(optId, -15032005) #建筑不是佣兵处

            BuildingLevel = BuildingInfo["BuildingRealLevel"]
            MakeValue = Gcore.getCfg('tb_cfg_building_up', (9, BuildingLevel), 'MakeValue')

            HireSpace = MaxNum - SoldierNum
            if HireNum > HireSpace:
                return Gcore.error(optId, -15032006) #大于校场屯兵数
            if AlreadyHireNum + HireNum > MakeValue:
                return Gcore.error(optId, -15032007) #超过了雇佣上限

            #计算花费
            MakeCost = Gcore.getCfg('tb_cfg_soldier_up', (SoldierType, 0), 'MakeCost')
            MakeCostType = Gcore.getCfg('tb_cfg_soldier_up', (SoldierType, 0), 'MakeCostType')
            Cost = MakeCost * int(math.ceil(HireNum / 200.0))
            pay = modCoin.PayCoin(optId,MakeCostType,Cost,classMethod,param)        
            if pay <= 0 :
                return Gcore.error(optId, -15032008) #支付失败

            #增加士兵
            Num = Soldiers['Soldier%s'%SoldierType] + HireNum
            modCamp.updateSoldierNum(SoldierType, Num)

            HireInfo['Soldier%s'%SoldierType] += HireNum
            #更新tb_soldier_hire
            modCamp.updateSoldierHire(HireInfo, BuildingId, TodayDate)
            
            print '现在的佣兵数量是', HireInfo
            
            recordData = {'uid':self.uid,'ValType':SoldierType,'Val':HireNum}#成就、任务记录 
            return Gcore.out(optId, {"Cost":Cost, "TimeStamp":TimeStamp,"HireNum":HireNum}
                             ,mission=recordData,achieve=recordData)

        SoldierProcess = modCamp.getSoldierProcess(BuildingId)
        if not SoldierProcess:
            return Gcore.error(optId, -15032009) #用户当前没有征兵记录

        NumInTraining = 0
        ProcessId = None
        BuildingLevel = None
        for Process in SoldierProcess:
            if Process["SoldierType"] == SoldierType:
                NumInTraining = Process['SpawnNumRest']
                ProcessId = Process['ProcessId']
                BuildingLevel = Process['BuildingLevel']
        if NumInTraining == 0:
            return Gcore.error(optId, -15032010) #没有训练该兵种 
        if SoldierNum + NumInTraining > MaxNum:
            return Gcore.error(optId, -15032011) #训练数量大于校场的剩余容量

        #加速时间
        #注意：配置中是小时产量。
        #speed = Gcore.getCfg('tb_cfg_building_up', (6, BuildingLevel), 'HourValue')
        #TotalTimeNeed = int(math.ceil(NumInTraining/(speed/3600+0.0)))
        GoldCost = calSpeedCost(3, NumInTraining)
        pay = modCoin.PayCoin(optId,1,GoldCost,classMethod,param)
        if pay < 0:
            return Gcore.error(optId, -15032012) #黄金不足

        #加速征兵记录
        modCamp.speedupSoldierProcess(ProcessId)
        #更新士兵表 或更新器械表
        Num = NumInTraining + Soldiers['Soldier%s'%SoldierType]
        modCamp.updateSoldierNum(SoldierType, Num)
        
        recordData = {'uid':self.uid,'ValType':SoldierType,'Val':1}#成就、任务记录 
        return Gcore.out(optId, {"SpeedNum":NumInTraining, "GoldCost":pay, "TimeStamp":TimeStamp}
                         ,mission=recordData,achieve=recordData)

    @inspector(15035, ['BuildingId'])
    def GetHireNum(self, param={}):
        '''获取当天雇佣数量  '''
        optId = 15035
        
        BuildingId = param['BuildingId']
        TimeStamp = param['ClientTime']
        
        modCamp = Gcore.getMod('Building_camp', self.uid)
        TodayDate = time.strftime('%Y-%m-%d', time.localtime(TimeStamp))
        HireInfo = modCamp.getHireByDate(BuildingId, TodayDate)

        if not HireInfo:
            return Gcore.out(optId, {'TodayHireNum':0})
        return Gcore.out(optId,{'TodayHireNum':sum(HireInfo.values())})
#end class BuildingUI

def _test():
    '''测试'''
    uid = 1001
    c = Building_campUI(uid)

    #GetSpawnInfo
    #SetCurNum
    para ={
                "BuildingId":   1964,
                "SoldierType":  1,
                "HireNum":      12,
                "CurNum":3000,
                "Flag": 1
        }
    #print c.SetCurNum(para)
    #print c.SpeedUpTraining(para)
    print c.GetSpawnInfo(para)

if __name__ == '__main__':
    _test()
