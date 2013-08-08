#coding:utf8
#author:zhoujingjiang
#date:2013-1-3
#游戏外部接口：建筑通用功能-建造，取消，升级，加速。

import json
import sys

from sgLib.core import Gcore, inspector
import sgLib.common as common

class BuildingUI(object):
    '''建筑通用功能外部接口'''
    def __init__(self, uid):
        self.mod = Gcore.getMod('Building', uid)
        self.uid = uid

    @inspector(15001, ['BuildingType', 'x', 'y'])
    def CreateBuilding(self, param={}):
        '''通用：建造建筑'''
        optId = 15001

        #参数
        BuildingType = param['BuildingType']
        x = param['x']
        y = param['y']
        TimeStamp = param['ClientTime']
        
        BuildingCfg = Gcore.getCfg('tb_cfg_building')
        if BuildingType==1 or BuildingType==19 or \
            BuildingType not in BuildingCfg:
            #非法操作：将军府和城墙不能建造 或 建筑类型不对。
            return Gcore.error(optId, -15001998)

        #建筑大小
        size = Gcore.getCfg('tb_cfg_building', BuildingType, 'Size')
        xSize, ySize = self.mod.sizeExplode(size)

        #用户的所有建筑
        AllBuildings = self.mod.getBuildingById(
            fields=['BuildingType', 'x', 'y', 'xSize', 'ySize'],
            TimeStamp=TimeStamp)

        #已经被建筑占用的坐标
        modMap = Gcore.getMod('Map', self.uid)
        UsedCoords = modMap.cacUsedCoords(AllBuildings)
        #所有可用坐标
        UsefulCoords = modMap.getAllUsefulCoords()
        #要使用的坐标
        NeededCoords = modMap.getCoords(x, y, xSize)
        #检查坐标是否可用
        
        for CoordTpl in NeededCoords:
            if CoordTpl in UsedCoords or CoordTpl not in UsefulCoords:
                print CoordTpl, '不可用'
                print CoordTpl, '在已用坐标中:', CoordTpl in UsedCoords
                print CoordTpl, '不在可用坐标中:', CoordTpl not in UsefulCoords
                return Gcore.error(optId, -15001001) #坐标不可用
        
        #将军府等级
        HomeLevel = 0
        for Building in AllBuildings:
            if Building['BuildingType'] == 1:
                HomeLevel = Building['BuildingRealLevel']

        #读配置
        OpenLevel = Gcore.getCfg('tb_cfg_building', BuildingType, 'OpenLevel')
        MaxNum = Gcore.getCfg('tb_cfg_building', BuildingType, 'MaxNum')
        ExpandLevelJson = Gcore.getCfg('tb_cfg_building', 
                                       BuildingType, 
                                       'ExpandLevelJson')

        if HomeLevel < OpenLevel:
            return Gcore.error(optId, -15001002) #未达到开放等级

        #空闲工匠数量
        AllWorkerNum = self.mod.getWorkerNum()
        BusyWorkerNum = len([Building for Building in AllBuildings 
                             if Building['BuildingState'] != 0])
        FreeWorkerNum = AllWorkerNum - BusyWorkerNum
        if FreeWorkerNum <= 0:
            return Gcore.error(optId,-15001003) #无空闲工匠

        #该类型建筑的数量
        countBuildingType = len([Building for Building in AllBuildings 
                                 if Building['BuildingType'] == BuildingType])
        if countBuildingType >= MaxNum:
            return Gcore.error(optId, -15001004) #已达到最大建筑数量

        #扩建个数
        if ExpandLevelJson:
            ExpandLevelDict = json.loads(ExpandLevelJson)
            MaxCanBuild = [int(num) for num, Level in ExpandLevelDict.iteritems() 
                           if HomeLevel >= Level]
            if MaxCanBuild and countBuildingType >= max(MaxCanBuild):
                return Gcore.error(optId, -15001005) #扩建失败

        CostValue = Gcore.getCfg('tb_cfg_building_up', 
                                 (BuildingType, 1), 'CostValue')
        CDValue = Gcore.getCfg('tb_cfg_building_up', 
                               (BuildingType, 1), 'CDValue')#建筑建造时间
        CoinType = Gcore.getCfg('tb_cfg_building', 
                                BuildingType, 'CoinType')
        
        #建筑CD时间受内政4影响, 花费受内政7影响#Author:Zhanggh 2013-4-23
        interMod = Gcore.getMod('Inter',self.uid)
        CDValue = interMod.getInterEffect(4,CDValue)
        CostValue = interMod.getInterEffect(7,CostValue)

        #开始支付
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        pay = modCoin.PayCoin(optId, CoinType, CostValue, classMethod, param)
        if pay < 0:
            return Gcore.error(optId, -15001995) #支付失败

        param['xSize'], param['ySize']= xSize, ySize
        param['CoinType'] = CoinType
        param['CostValue'] = CostValue
        param['CDValue'] = CDValue
        param['LastChangedTime'] = TimeStamp

        BuildingId = self.mod.createBuilding(param)
        if int(BuildingId) >0:
            #不同类型的建筑向不同的表中插入初始数据
            return Gcore.out(optId,{'Coin%s'%CoinType:modCoin.getCoinNum(CoinType), 
                                    'BuildingId':BuildingId, 
                                    'EndTime':TimeStamp + CDValue,
                                    'x':param['x'], 
                                    'y':param['y'], 
                                    'BuildingType':BuildingType})
        return Gcore.error(optId, -15001997) #系统错误

    @inspector(15002, ['BuildingId'])
    def UpgradeBuilding(self, param={}):
        '''通用：升级建筑'''
        print '建筑开始'
        import time
        starttime = time.time()
        optId = 15002

        BuildingId = param['BuildingId']
        TimeStamp = param['ClientTime']
        body = {}#返回参数
        
        AllBuildings = self.mod.getBuildingById(
                    fields=['BuildingId', 'BuildingType', 'CompleteTime', 'LastOptType'],
                    TimeStamp=TimeStamp)
        IsOwner = False #建筑是不是玩家的
        HomeLevel = 0 #将军府等级
        for Building in AllBuildings:
            if Building['BuildingId'] == BuildingId:
                BuildingLevel = Building["BuildingRealLevel"]
                BuildingType = Building["BuildingType"]
                BuildingState = Building['BuildingState']
                IsOwner = True
                #print '完成时间', Building['CompleteTime']
            if Building['BuildingType'] == 1: #将军府的BuildingType是1
                HomeLevel = Building['BuildingRealLevel']

        if not IsOwner:
            return Gcore.error(optId, -15002001) #用户没有该建筑
        if BuildingState:
            return Gcore.error(optId, -15002002) #不是空闲状态的建筑，无法升级。

        BuildingCfg = Gcore.getCfg('tb_cfg_building', BuildingType)
        BuildingUpCfg = Gcore.getCfg('tb_cfg_building_up', (BuildingType, BuildingLevel + 1))

        MaxLevel = BuildingCfg['MaxLevel']
        MaxLevelHomeDif = BuildingCfg['MaxLevelHomeDif']

        if BuildingLevel >= MaxLevel:
            return Gcore.error(optId, -15002003) #建筑已达最高等级

        if BuildingType != 1 and BuildingLevel - HomeLevel >= MaxLevelHomeDif:
            return Gcore.error(optId, -15002004) #建筑与将军府的差应该小于MaxLevelHomeDif

        AllWorkerNum = self.mod.getWorkerNum()
        BusyWorkerNum = len([Building for Building in AllBuildings if Building['BuildingState'] != 0])
        FreeWorkerNum = AllWorkerNum - BusyWorkerNum
        if FreeWorkerNum <= 0:
            return Gcore.error(optId, -15002904) #建筑工匠数量不足

        CoinType = BuildingCfg['CoinType']
        CoinNum = BuildingUpCfg['CostValue']
        CDValue = BuildingUpCfg['CDValue']
        
        #print '不受内政影响的CD', CDValue
        #print 'min', CDValue/60, 'sec', CDValue%60
        
        #建筑CD时间受内政4影响, 花费受内政7影响 by Lizr 130611
        interMod = Gcore.getMod('Inter',self.uid)
        CDValue = interMod.getInterEffect(4,CDValue)
        CoinNum = interMod.getInterEffect(7,CoinNum)
        
        #print 'cd', CDValue
        #print 'min', CDValue/60, 'sec', CDValue%60
        #print '完成时间', TimeStamp + CDValue
        
        #开始支付
        modCoin = Gcore.getMod('Coin',self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        pay = modCoin.PayCoin(optId, CoinType, CoinNum, classMethod, param)
        if pay < 0:
            return Gcore.error(optId, -15002995, {'CoinNum':CoinNum, 'RestCoin':modCoin.getCoinNum(CoinType)}) #支付失败

        UpInfo = {}
        UpInfo['CoinType'] = CoinType
        UpInfo['BuildingPrice'] = CoinNum
        UpInfo['LastChangedTime'] = TimeStamp
        UpInfo['CompleteTime'] = TimeStamp + CDValue
        UpInfo['BuildingLevel'] = BuildingLevel + 1
        UpInfo['LastOptType'] = 1
        stat = self.mod.updateBuildingById(UpInfo, BuildingId)
        if not stat:
            return Gcore.error(optId, -15002997) #系统错误
        print '建筑升级完成', time.time() - starttime
        #不同类型的建筑进行不同的运算
        # + todo
        if BuildingType==2 or BuildingType==5:#磨坊，铸币厂升级收集军资
            print '建筑升级计算资源'
            starttime = time.time()
            ColInfo = Gcore.getMod('Building_resource',self.uid).collectCoin(optId,BuildingType,BuildingId,TimeStamp,param=param)
            CoinType = 2 if BuildingType == 2 else 3
            body['NowCoin'] = ColInfo.get('NowCoin')
            body['Remain'] = ColInfo.get('Remain')
            body['CoinType'] = CoinType
            print '建筑升级计算资源', time.time() - starttime
             
        if BuildingType in (6, 8): #兵营 工坊：计算士兵
            print '建筑升级计算士兵'
            starttime = time.time()
            
            modCamp = Gcore.getMod('Building_camp', self.uid)
            modCamp.TouchAllSoldiers(TimeStamp=TimeStamp)
            if BuildingType in (6, 8): #兵营 工坊 升级时暂停
                update_dic = {'LastChangedTime':TimeStamp + CDValue,
                              'BuildingLevel':BuildingLevel+1}
                modCamp.updateProcessById(update_dic, BuildingId)
            
            print '建筑升级计算士兵', time.time() - starttime
        if BuildingType == 18: #点将台
            print '建筑升级-点将台'
            starttime = time.time()
            modTrain = Gcore.getMod('Building_train', self.uid)
            Buildings = [building for building in AllBuildings
                         if building['BuildingType'] == BuildingType]
            #print 'Buildings', Buildings
            modTrain.normalAddTrainNum(num=0, TimeStamp=TimeStamp, Buildings=Buildings)
            print '建筑升级-点将台', time.time() - starttime
        #成功
        print '查询金钱'
        starttime = time.time()
        body['Coin%s'%CoinType] = modCoin.getCoinNum(CoinType)
        print '查询金钱', time.time() - starttime
        
        recordData = {'uid':self.uid,'ValType':BuildingType,'Val':1}#成就、任务记录 
        if Gcore.TEST:
            body['test'] = {'payCoin':pay,'Currency':modCoin.getCurrency()}
            
        return Gcore.out(optId, body, mission=recordData)

    @inspector(15003, ['BuildingId'])
    def CancelBuilding(self, param={}):
        '''通用：取消建筑建造或升级'''
        optId = 15003

        BuildingId = param["BuildingId"]
        TimeStamp = param['ClientTime']

        BuildingInfo = self.mod.getBuildingById(BuildingId, 
                                                ['BuildingPrice', 
                                                 'BuildingType', 
                                                 'CoinType',
                                                 'LastOptType'], 
                                                TimeStamp=TimeStamp)
        if not BuildingInfo:
            return Gcore.error(optId, -15003003) #用户没有该建筑
        
        #BuildingType < 100 是建筑；大于100是装饰；
        if BuildingInfo['BuildingType'] < 100 and \
        BuildingInfo['BuildingState'] == 0:
            return Gcore.error(optId, -15003004) #建筑已建造或升级完成,不能取消。
        
        BuildingType = BuildingInfo['BuildingType']
        CostValue = BuildingInfo["BuildingPrice"]
        CostType = BuildingInfo["CoinType"]
        
        #返钱
        CancelReturn = Gcore.loadCfg(
            Gcore.defined.CFG_BUILDING)["CancelReturn"] #返还比例
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, 
                                 sys._getframe().f_code.co_name)
        gain = modCoin.GainCoin(optId, CostType, 
                                int(CostValue * CancelReturn), 
                                classMethod, param)
        if gain < 0:
            return Gcore.error(optId, -15003005) #增加货币失败

        #建筑正在建造 ：如果是装饰，删掉。
        if BuildingInfo['BuildingType'] > 100 or \
        BuildingInfo['BuildingState'] == 1:
            self.mod.deleteBuildingById(BuildingId)
        else:
            #更新建筑表
            UpInfo = {}
            UpInfo['CompleteTime'] = TimeStamp
            UpInfo['BuildingLevel'] = BuildingInfo['BuildingRealLevel']
            UpInfo['LastOptType'] = 2
            self.mod.updateBuildingById(UpInfo, BuildingId)
        #不同类型的建筑进行不同的操作
        # + todo
        if BuildingType in (6, 7, 8): #校场 兵营 工坊：计算士兵
            modCamp = Gcore.getMod('Building_camp', self.uid)
            modCamp.TouchAllSoldiers(TimeStamp=TimeStamp)
            if BuildingType in (6, 8): #兵营 工坊 回复生产
                update_dic = {'LastChangedTime':TimeStamp, 
                              'BuildingLevel':BuildingInfo['BuildingRealLevel']}
                modCamp.updateProcessById(update_dic, BuildingId)
        return Gcore.out(optId, 
                         {'Coin%s'%CostType:modCoin.getCoinNum(CostType), 
                          "RetValue":int(CostValue * CancelReturn)})

    @inspector(15004, ['BuildingId'])
    def SpeedupProcess(self, param={}):
        '''通用：加速建造或升级'''
        optId = 15004

        BuildingId = param["BuildingId"]
        if not BuildingId:
            x = param["x"]
            y = param["y"]
            BuildingId = self.mod.getBuildingByCoord(x,y)
        if not BuildingId:
            return Gcore.error(optId, -15004002) #没有这个建筑
        TimeStamp = param['ClientTime']
        
        BuildingInfo = self.mod.getBuildingById(BuildingId, 
                fields=['CompleteTime', 'BuildingType','BuildingLevel'], 
                TimeStamp=TimeStamp)
        if not BuildingInfo:
            return Gcore.error(optId, -15004003) #用户没有该建筑
        if BuildingInfo['BuildingState'] == 0:
            return Gcore.error(optId, -15004004) #建筑已建造或升级完成
        BuildingType = BuildingInfo['BuildingType']
        BuildingLevel = BuildingInfo['BuildingLevel']
        
        StopTime = BuildingInfo['CompleteTime']
        TimeRemained = StopTime - TimeStamp
        GoldenCoinNum = common.calSpeedCost(1, TimeRemained)
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, 
                                 sys._getframe().f_code.co_name)
        pay = modCoin.PayCoin(optId, 1, GoldenCoinNum, classMethod, param)
        if pay < 0:
            return Gcore.error(optId, -15004995) #支付失败

        #更新建筑表
        UpInfo = {"CompleteTime":TimeStamp, "LastOptType":3}
        self.mod.updateBuildingById(UpInfo, BuildingId)

        #不同类型的建筑进行不同的操作
        # + todo
        if BuildingType in (6, 7, 8): #校场 兵营 工坊：计算士兵
            modCamp = Gcore.getMod('Building_camp', self.uid)
            modCamp.TouchAllSoldiers(TimeStamp=TimeStamp)
            if BuildingType in (6, 8): #兵营 工坊 回复生产
                update_dic = {'LastChangedTime':TimeStamp}
                modCamp.updateProcessById(update_dic, BuildingId)
        if BuildingType == 18: #点将台
            print '点将台加速完成'
            modTrain = Gcore.getMod('Building_train', self.uid)
            if BuildingLevel == 1:
                num = Gcore.getCfg('tb_cfg_building_up',
                                   (18, 1), 'MakeValue')
            else:
                num = Gcore.getCfg('tb_cfg_building_up',
                                   (18, BuildingLevel),
                                   'MakeValue') - \
                      Gcore.getCfg('tb_cfg_building_up',
                                   (18, BuildingLevel-1),
                                   'MakeValue')
            print '增加的数量', num
            modTrain.normalAddTrainNum(num=num, TimeStamp=TimeStamp)
        
        recordData = {'uid':self.uid,'ValType':BuildingType,'Val':1,
                      'BuildingLevel':BuildingLevel}#成就、任务记录 
        return Gcore.out(optId, {'Coin%s'%1:modCoin.getCoinNum(1),
                                 "Cost":pay, 
                                 "TimeRemained":TimeRemained},
                         mission=recordData)
    
    @inspector(15901, ['BuildingId', 'x', 'y'])
    def MoveBuilding(self, param={}):
        '''通用：移动建筑位置'''
        optId = 15901

        BuildingId = param['BuildingId']
        x = param['x']
        y = param['y']
        TimeStamp = param['ClientTime']
        
        #用户的所有建筑
        AllBuildings = self.mod.getBuildingById(fields=['BuildingId', 'BuildingType', 'x', 'y', 'xSize', 'ySize'], TimeStamp=TimeStamp)
        
        AllBuildings2 = [] #除建筑本身外的所有建筑
        tag = False #玩家是否有该建筑
        for building in AllBuildings:
            if BuildingId == building['BuildingId']:
                tag = True
                xSize = building['xSize']
                if building['BuildingType'] == 1:
                    return Gcore.error(optId, -15901001) #将军府不能移动
            else:
                AllBuildings2.append(building)
        if not tag:
            return Gcore.error(optId, -15901002) #不是该玩家的建筑，无法移动
        
        del AllBuildings
        #已经被建筑占用的坐标
        modMap = Gcore.getMod('Map', self.uid)
        UsedCoords = modMap.cacUsedCoords(AllBuildings2)

        #所有可用坐标
        UsefulCoords = modMap.getAllUsefulCoords()

        #要使用的坐标
        NeededCoords = modMap.getCoords(x, y, xSize)

        #检查坐标是否可用
        for CoordTpl in NeededCoords:
            if CoordTpl in UsedCoords or CoordTpl not in UsefulCoords:
                #print 'CoordTpl',CoordTpl
                #print 'UsedCoords',UsedCoords
                return Gcore.error(optId, -15901003) #坐标已被占用
        
        self.mod.updateBuildingById({"x":x, "y":y}, BuildingId)
        recordData = {'uid':self.uid,'ValType':0,'Val':1}#成就、任务记录 
        return Gcore.out(optId, body = {"x":x, "y":y, "BuildingId":BuildingId},mission=recordData)
#end class BuildingUI

def _test():
    '''测试'''
    uid = 1001
    c = BuildingUI(uid)
    #可建BuildingType:
    #2磨坊 3谷仓 4钱庄 5铸币厂 6兵营 7校场 8工坊 9 佣兵兵 10理藩院 11铁匠铺
    #12书院 13招贤馆 14演武场 15外史院 16祭坛  18点将台 
    #可用x y (28,39),()....
    p  = {
                "x":34,
                "y":35,
                "BuildingType": 18,
                "CreateTimeStamp":  1365672841
        }
    print c.CreateBuilding(p)
    ##print c.MoveBuilding({"BuildingId":374, 'x':22, 'y':38})
    
    ##print Gcore.loadCfg(Gcore.defined.CFG_BUILDING)["SpeedUpTime"]
    #print c.UpgradeBuilding({"BuildingId": 2865})
    ##print c.CancelBuilding({"BuildingId":658})
    #print c.SpeedupProcess({"BuildingId":2865})
    ##print Gcore.getMod('Building_home',uid).achieveTrigger(1,1)

if __name__ == '__main__':
    _test()
    Gcore.runtime()
