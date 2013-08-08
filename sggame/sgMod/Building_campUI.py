#coding:utf8
#author:zhoujingjiang
#date:2013-7-22
#comment:兵营外部接口

import sys
import time
import math

from sgLib.core import Gcore, inspector
from sgLib.common import calSpeedCost

class Building_campUI(object):
    def __init__(self, uid):
        self.uid = uid

    @inspector(15030, ['BuildingId'])
    def GetSpawnNum(self, param={}):
        '''获取当前时刻，兵营或工坊的新兵数量'''
        optId = 15030

        BuildingId = param['BuildingId']
        TimeStamp = param['ClientTime']
        
        modBuilding = Gcore.getMod('Building', self.uid)
        BuildingInfo = modBuilding.getBuildingById(BuildingId, TimeStamp=TimeStamp)
        if not BuildingInfo:
            return Gcore.error(optId, -15030001) #玩家没有该建筑
        if BuildingInfo['BuildingState'] == 1:
            return Gcore.error(optId, -15030002) #建筑正在建造
        if BuildingInfo['BuildingType'] not in (6, 8):
            return Gcore.error(optId, -15030003) #建筑不是兵营或工坊
        
        print '建筑ID', BuildingId
        print '建筑类型', BuildingInfo['BuildingType']
        print '建筑等级', BuildingInfo['BuildingLevel']

        modCamp = Gcore.getMod('Building_camp', self.uid) 
        spawn_detail= modCamp.getSoldierStorage(BuildingInfo, TimeStamp)
        body = {}
        body['StorageNum'] = spawn_detail['StorageNum']
        body['LastChangedTime'] = spawn_detail['LastChangedTime']

        return Gcore.out(optId, body=body)

    @inspector(15031, ['BuildingId'])
    def FullAddSoldier(self, param={}):
        '''填满兵营或工坊的剩余训练空间'''
        optId = 15031
        
        BuildingId = param['BuildingId']
        TimeStamp = param['ClientTime']
        
        modBuilding = Gcore.getMod('Building', self.uid)
        BuildingInfo = modBuilding.getBuildingById(BuildingId, TimeStamp=TimeStamp)
        if not BuildingInfo:
            return Gcore.error(optId, -15031001) #玩家没有该建筑
        if BuildingInfo['BuildingState'] == 1:
            return Gcore.error(optId, -15031002) #建筑正在建造
        if BuildingInfo['BuildingType'] not in (6, 8):
            return Gcore.error(optId, -15031003) #建筑不是兵营或工坊

        modCamp = Gcore.getMod('Building_camp', self.uid) 
        spawn_detail= modCamp.getSoldierStorage(BuildingInfo, TimeStamp)

        MaxNum = Gcore.getCfg('tb_cfg_building_up',
                              (BuildingInfo['BuildingType'], BuildingInfo['BuildingRealLevel']),
                              'MakeValue')
        buy_cnt = MaxNum - spawn_detail['StorageNum']
        print '兵营或工坊的最大数量', MaxNum
        print '当前时刻的数量', spawn_detail['StorageNum']
        print '购买数量', buy_cnt
        
        if buy_cnt < 0:
            return Gcore.error(optId, -15031004) #兵营或工坊已满
        elif buy_cnt > 0:
            coin_need = calSpeedCost(3, buy_cnt)
            class_method = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
            modCoin = Gcore.getMod('Coin', self.uid)
            pay = modCoin.PayCoin(optId, 1, coin_need, class_method, param)
            if pay < 0:
                return Gcore.error(optId, -15031005) #支付失败
            
            #将兵营置满
            modCamp.fullAddSoldier(BuildingId, BuildingInfo['BuildingType'], 
                                   BuildingInfo['BuildingRealLevel'],
                                   max(spawn_detail['LastChangedTime'], TimeStamp),
                                   TimeStamp)
        else:
            pay = 0

        body = {}
        body['StorageNum'] = MaxNum
        body['BuyCnt'] = buy_cnt
        body['GoldenCoinCost'] = pay
        body['TimeStamp'] = TimeStamp
        
        return Gcore.out(optId, body=body)

    @inspector(15032, ['BuildingId', 'SoldierType', 'SoldierNum'])
    def ExchangeSoldier(self, param={}):
        '''训练新兵'''
        optId = 15032
        
        BuildingId = param['BuildingId']
        SoldierType = param['SoldierType']
        SoldierNum = param['SoldierNum']
        TimeStamp = param['ClientTime']
        
        SoldierNum = int(SoldierNum)
        if SoldierNum <= 0:
            return Gcore.error(optId, -15032001) #训练数量不得小于0

        modCamp = Gcore.getMod('Building_camp', self.uid) 
        SoldierClass = modCamp.isSameCamp(SoldierType)
        if not SoldierClass:
            return Gcore.error(optId, -15032002) #不是同一阵营的士兵

        modBuilding = Gcore.getMod('Building', self.uid)
        BuildingInfo = modBuilding.getBuildingById(BuildingId, TimeStamp=TimeStamp)
        if not BuildingInfo:
            return Gcore.error(optId, -15032003) #玩家没有该建筑
        if BuildingInfo['BuildingState'] == 1:
            return Gcore.error(optId, -15032004) #建筑正在建造
        if BuildingInfo['BuildingType'] not in (6, 8):
            return Gcore.error(optId, -15032005) #建筑不是兵营或工坊

        building_type = BuildingInfo['BuildingType']
        building_level = BuildingInfo['BuildingRealLevel']
        spawn_detail= modCamp.getSoldierStorage(BuildingInfo, TimeStamp)        

        if building_type == 6 and SoldierClass != 1:
            return Gcore.error(optId, -15032006) #兵种不是士兵
        elif building_type == 8 and SoldierClass != 2:
            return Gcore.error(optId, -15032007) #兵种不是器械
        
        #是否达到开放等级
        OpenLevel = Gcore.getCfg('tb_cfg_soldier', SoldierType, 'OpenLevel')
        if building_level < OpenLevel:
            return Gcore.error(optId, -15032008) #没达到开放等级

        if SoldierNum > spawn_detail['StorageNum']:
            return Gcore.error(optId, -15032009) #训练数量大于新兵数量
        
        SoldierSpace = modCamp.getMaxSoldierNum() - sum(modCamp.getSoldiers().values())
        if SoldierSpace <= 0:
            return Gcore.error(optId, -15032010) #校场已满
        if SoldierNum > SoldierSpace:
            return Gcore.error(optId, -15032011) #校场剩余空间不足
        
        #扣钱
        modCoin = Gcore.getMod('Coin', self.uid)
        modInter = Gcore.getMod('Inter', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)

        modBook = Gcore.getMod('Book', self.uid)
        SoldiersScience = modBook.getTechsLevel(1, TimeStamp)
        SoldierLevel = SoldiersScience[SoldierType]
        SoldierUpCfg = Gcore.getCfg('tb_cfg_soldier_up',
                                    (SoldierType, SoldierLevel))
        
        MakeCost = SoldierUpCfg['MakeCost']
        coinType = SoldierUpCfg['MakeCostType']
        coinValue = MakeCost * SoldierNum
        coinValue = modInter.getInterEffect(6, coinValue)
        pay = modCoin.PayCoin(optId,coinType,coinValue,classMethod,param) 
        print 'pay', pay
        if pay < 1:
            return Gcore.error(optId, -15032012) #支付失败
        
        #更新士兵
        modCamp.changeSoldierNum({SoldierType:int(SoldierNum)})
        #更新兵营或工坊
        modCamp.updateStorage(BuildingId, 
                        spawn_detail['StorageNum'] - SoldierNum, 
                        spawn_detail['LastChangedTime'],
                        spawn_detail['LastCalTime'])
        body = {}
        body['CostValue'] = pay
        body['CostType'] = coinType
        body['CurStorageNum'] = spawn_detail['StorageNum'] - SoldierNum
        body['LastChangedTime'] = spawn_detail['LastChangedTime']
        
        recordData = {'uid':self.uid,'ValType':SoldierType,'Val':SoldierNum}
        return Gcore.out(optId, body=body , achieve=recordData,mission=recordData)

    @inspector(15033, ['BuildingId', 'SoldierType', 'SoldierNum'])
    def HireSoldier(self, param={}):
        '''佣兵处雇佣'''
        optId = 15033

        BuildingId = param['BuildingId'] #佣兵处ID
        SoldierType = param['SoldierType'] #佣兵类型
        SoldierNum = param['SoldierNum'] #佣兵数量
        TimeStamp = param['ClientTime']
        
        #佣兵数量大于0
        SoldierNum = int(SoldierNum)
        if SoldierNum <= 0: 
            return Gcore.error(optId, -15033001) #佣兵数量应该大于0
        
        #佣兵处信息
        modBuilding = Gcore.getMod('Building', self.uid)
        BuildingInfo = modBuilding.getBuildingById(BuildingId, TimeStamp=TimeStamp)
        if not BuildingInfo:
            return Gcore.error(optId, -15033002) #玩家没有这个佣兵处
        if BuildingInfo['BuildingState'] == 1: 
            return Gcore.error(optId, -15033003) #佣兵处正在建造
        BuildingLevel = BuildingInfo['BuildingRealLevel'] #佣兵处等级

        #兵种信息
        SoldierCfg = Gcore.getCfg('tb_cfg_soldier')
        HireSoldierType = [k for (k, v) in SoldierCfg.iteritems() if v["SoldierSide"] == 4]
        SoldierType = int(SoldierType)
        if SoldierType not in HireSoldierType:
            return Gcore.error(optId, -15033004) #兵种不是雇佣兵
        
        #校场信息
        modCamp = Gcore.getMod('Building_camp', self.uid)
        Schools = modBuilding.getBuildingByType(7, TimeStamp=TimeStamp)
        SoldierSpace = modCamp.getMaxSoldierNum(Schools) - sum(modCamp.getSoldiers().values())
        if SoldierSpace <= 0:
            return Gcore.error(optId, -15033005) #校场已满
        if SoldierNum > SoldierSpace:
            return Gcore.error(optId, -15033006) #校场剩余空间不足

        #获取当天的雇佣数量
        TodayDate = time.strftime('%Y-%m-%d', time.localtime(TimeStamp))
        HireInfo = modCamp.getHireByDate(BuildingId, TodayDate)
        if not HireInfo:
            print '今天还没雇佣'
            HireInfo = dict.fromkeys(map(lambda s:'Soldier%s'%s, HireSoldierType), 0)
            HireNum = 0
        else:HireNum = sum(HireInfo.values())
        print '已经雇佣的数量', HireNum

        #是否已达到最大雇佣上限
        MakeValue = Gcore.getCfg('tb_cfg_building_up', 
                                 (9, BuildingLevel), 
                                 'MakeValue')
        if SoldierNum + HireNum > MakeValue:
            return Gcore.error(optId, -15033007) #超过了雇佣上限

        #计算花费
        MakeCost = Gcore.getCfg('tb_cfg_soldier_up', 
                                (SoldierType, 0), 
                                'MakeCost')
        MakeCostType = Gcore.getCfg('tb_cfg_soldier_up', 
                                    (SoldierType, 0), 
                                    'MakeCostType')
        Cost = MakeCost * int(math.ceil(SoldierNum / 200.0))
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        pay = modCoin.PayCoin(optId, MakeCostType, Cost, classMethod, param)        
        if pay <= 0:
            return Gcore.error(optId, -15033008) #支付失败

        #更新士兵表
        modCamp.changeSoldierNum({SoldierType:SoldierNum}, Buildings=Schools)
        #更新雇佣表
        HireInfo['Soldier%s'%SoldierType] += SoldierNum
        modCamp.updateSoldierHire(HireInfo, BuildingId, TodayDate)

        body = {}
        body['GoldenCost'] = pay
        body['AlreadyHireNum'] = HireNum + SoldierNum
        body['TimeStamp'] = TimeStamp
        body['MaxHireNum'] = MakeValue
        recordData = {'uid':self.uid,'ValType':SoldierType,'Val':SoldierNum}
        return Gcore.out(optId, body=body,achieve=recordData,mission=recordData)

    @inspector(15034, ['BuildingId'])
    def GetHireNum(self, param={}):
        '''获取当天佣兵处的雇佣数量'''
        optId = 15034

        BuildingId = param['BuildingId']
        TimeStamp = param['ClientTime']
        
        modCamp = Gcore.getMod('Building_camp', self.uid) 
        TodayDate = time.strftime('%Y-%m-%d', time.localtime(TimeStamp))
        HireInfo = modCamp.getHireByDate(BuildingId, TodayDate)
        if not HireInfo:HireNum=0
        else:HireNum = sum(HireInfo.values())
        
        body = {'BuildingId':BuildingId, 'HireNum':HireNum}
        return Gcore.out(optId, body=body)
#end class Building_campUI

