# -*- coding:utf-8 -*-
# author:zhoujingjiang
# date:2013-1-3
# 游戏外部接口:祭坛
from __future__ import division
import sys
import math

from sgLib.core import Gcore, inspector
from sgLib.defined import CFG_BUILDING_ALTAR

class Building_altarUI(object):
    '''祭坛功能外部接口'''
    def __init__(self, uid):
        self.mod = Gcore.getMod('Building_altar', uid)
        self.uid = uid
        
    @inspector(15020, ['AltarType'])
    def GetLotteryCnt(self, param = {}):
        '''祭坛：获取天坛或地坛某天的抽奖次数'''
        optId = 15020
        TimeStamp = param['ClientTime']
        AltarType = param['AltarType']
        LotteryCnt = self.mod.getLotteryCnt(AltarType, TimeStamp)
        if not LotteryCnt:
            LotteryCnt = 0
#        if LotteryCnt is False:
#            return Gcore.error(optId, -15020001) #后台数据库出错
        return Gcore.out(optId, {"LotteryCount": LotteryCnt})
    
    @inspector(15021, ['BuildingId', 'AltarType'])
    def Lottery(self, param = {}):
        '''祭坛：抽奖'''
        optId = 15021
        BuildingId = param['BuildingId']
        AltarType = param['AltarType']
        TimeStamp = param['ClientTime']
        #获取建筑
        modBuilding = Gcore.getMod('Building', self.uid)
        BuildingInfo = modBuilding.getBuildingById(BuildingId, TimeStamp = TimeStamp)
        
        if not BuildingInfo:
            return Gcore.error(optId, -15021001) #用户没有该建筑
        if BuildingInfo['BuildingType'] != 16:
            return Gcore.error(optId, -15021002) #建筑不是祭坛
        if BuildingInfo['BuildingState'] == 1:
            return Gcore.error(optId, -15021003) #建筑正在建造
        #读配置
        AltarConfig = Gcore.loadCfg(CFG_BUILDING_ALTAR)  
        #获取抽奖次数
        AlreadyLotteryCnt = self.GetLotteryCnt({'AltarType':AltarType, 'ClientTime':TimeStamp})
        AlreadyLotteryCnt = AlreadyLotteryCnt.get('body', {}).get('LotteryCount', 0)
            
        if AltarType == 2: #地坛
            BuildingLevel = BuildingInfo['BuildingRealLevel']
            #当前等级地坛的抽奖总数
            LandTimes = Gcore.getCfg('tb_cfg_building_up', (16, BuildingLevel), 'LandTimes')
            if LandTimes <= AlreadyLotteryCnt:
                return Gcore.error(optId, -15021004) #地坛的抽奖次数已到      
            #计算货币
            CoinType = AltarConfig['LandCoinType']
            CoinValue = AltarConfig['LandTimesCost']
        elif AltarType == 1: #天坛
            #计算货币
            CoinType = AltarConfig['SkyCoinType']
            CoinValue = min(AltarConfig['SkyTimesCost'] * (AlreadyLotteryCnt + 1),50)
        else:
            return Gcore.error(optId, -15021005) #祭坛类型错误

        #抽奖
        AltarCfg = Gcore.getCfg('tb_cfg_altar')
        #从tb_cfg_altar中筛选出祭坛类型符合的数据
        AltarCfg = filter(lambda dic:dic['AltarType'] == AltarType and dic['AltarType'], AltarCfg.values())
        for dic in AltarCfg:
            dic.setdefault('Id', dic['AwardType'])
        AwardType = self.mod.Choice(AltarCfg).get('AwardType')#根据概率选出AwardType
        #根据AltarType和AwardType筛选出奖励种类
        TableCfg = 'tb_cfg_altar_sky' if AltarType == 1 else 'tb_cfg_altar_land'
        #AwardType = 2   #测试用
        AltarCfg =(Gcore.getCfg(TableCfg,AwardType))
        #根据概率份额筛选出奖励
        for dic in AltarCfg:
            dic['Id'] = AwardType * 100 + dic['AwardId']
        Award = self.mod.Choice(AltarCfg)

        #扣钱
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        pay = modCoin.PayCoin(optId, CoinType, CoinValue, classMethod, param)
        if pay < 0:
            return Gcore.error(optId, -15021006) #支付失败
        #将奖品给玩家
        re=self.mod.distLottery(AltarType,Award,TimeStamp,optId,'Building_altarUI.Lottery')
        #记日志
        self.mod.AddLotteryLog(AltarType, Award, TimeStamp,re['GainId'],re['GainNum'])
        #返回
        if AltarType == 1:
            CoinValue = pay
        body = {}
        body['AwardType'] = Award['SkyAwardType' if AltarType == 1 else 'LandAwardType']
        body['AwardId'] = Award['AwardId']
        body['Cost'] = CoinValue
        body['CostType'] = CoinType
        body['Result'] = re
        NextLoterryPay = self._GetNextPay(AltarType, TimeStamp)
        body['NextLoterryPay']=NextLoterryPay
        
#         print '祭坛抽奖=>> ',Award
        
        recordData = {'uid':self.uid,'ValType':AltarType,'Val':1,'Award':Award}#成就、任务记录
        
        #经验获得
        playerMod = Gcore.getMod('Player',self.uid)
        if AltarType==1:#天坛
            playerMod.addUserExp(105,0,optId)
        elif AltarType==2:#地坛
            playerMod.addUserExp(104,0,optId)
            
        return Gcore.out(optId, body = body, achieve=recordData, mission=recordData)
        
        
    @inspector(15022, ['Flag', 'AltarType','Page'])
    def GetAltarRank(self, param = {}):
        '''获取幸运榜'''
        optId = 15022
        
        Flag = param['Flag'] #1,全服幸运榜;2，我的幸运榜。
        AltarType = param['AltarType'] #祭坛类型
        TimeStamp = param['ClientTime']
        Page=param['Page']
        if not Page:
            Page=1
        PagePerNum=9
        rankCount=self.mod.getAltarRankCnt(AltarType, TimeStamp,Flag)
        stat = self.mod.getAltarRank(AltarType, TimeStamp,Page,PagePerNum, Flag)
        totalPage = math.ceil(rankCount/PagePerNum)
        if stat is False:
            return Gcore.error(optId, -15022001) #查询数据库出错
        return Gcore.out(optId, body = {"Rank":stat,'Page':Page,'TotalPage':totalPage})
    
    @inspector(15023, ['AltarType'])
    def GetLotteryLog(self,param={}):
        optId=15023
        AltarType=param['AltarType']
        TimeStamp=param['ClientTime']
        date=self.mod.getLotteryLog(AltarType,TimeStamp)
        return Gcore.out(optId, {'LotteryList':date})
    
    @inspector(15024, ['AltarType'])                     
    def GetNextLoterryPay(self,param={}):
        optId=15024
        AltarType=param['AltarType']
        TimeStamp = param['ClientTime']
        NextLoterryPay=self._GetNextPay(AltarType, TimeStamp)
        return Gcore.out(optId, {'NextLoterryPay':NextLoterryPay})
    
    def _GetNextPay(self,AltarType,TimeStamp):
        AltarConfig = Gcore.loadCfg(CFG_BUILDING_ALTAR)  
        AlreadyLotteryCnt = self.GetLotteryCnt({'AltarType':AltarType, 'ClientTime':TimeStamp})
        AlreadyLotteryCnt = AlreadyLotteryCnt.get('body', {}).get('LotteryCount', -1)
        if AltarType==2:
            NextCostType = AltarConfig['LandCoinType']
            NextCost = AltarConfig['LandTimesCost']
        else:
            NextCostType = AltarConfig['SkyCoinType']
            NextCost = min(AltarConfig['SkyTimesCost'] * (AlreadyLotteryCnt + 1),50)
            #打折
            vipLevel = Gcore.getUserData(self.uid, 'VipLevel')
            discount = Gcore.getCfg('tb_cfg_vip_up',vipLevel,'Discount')
            discount = discount if discount else 1
            NextCost = math.ceil(NextCost*discount)
        
        NextLoterryPay={'NextCostType':NextCostType,'NextCost':NextCost}
        return NextLoterryPay
#end class Building_altarUI
    

def _test():
    '''测试'''
    uid = 43522
    c = Building_altarUI(uid)
    #Gcore.resetRuntime()
    
#    print c.GetAltarRank({'Flag':1, 'AltarType':2,'Page':1})
    
#    print c.GetLotteryCnt({'AltarType':1})
#     c.Lottery({"BuildingId":13224, "AltarType":1})
#    Gcore.runtime()
#    for i in range(0,50):
#        print c.Lottery({"BuildingId":10557, "AltarType":1})
    #Gcore.runtime()
#    for i in range(1,100):
    print c.Lottery({"BuildingId":12938, "AltarType":2})
#    print c.GetLotteryLog({'AltarType':1})
    Gcore.runtime()
    
if __name__ == '__main__':
    _test()
    