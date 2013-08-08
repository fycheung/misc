# -*- coding:utf-8 -*-
# author:zhoujingjiang
# date:2013-2-19
# 游戏内部接口:祭坛

import random
import datetime
import time

from sgLib.core import Gcore
from sgLib.base import Base

class Building_altarMod(Base):
    '''祭坛模型'''
    def __init__(self, uid):
        Base.__init__(self,uid)
        self.uid = uid
        
    def getLotteryCnt(self, AltarType, TimeStamp):
        '''获取某一天的抽奖次数'''
        table = 'tb_altar_lottery'
        field = 'COUNT(*)'
        where = 'UserId=%s AND AltarType=%s AND AwardDate="%s"' % (self.uid, AltarType, datetime.date.fromtimestamp(TimeStamp))
        return self.db.out_field(table, field, where)

    def Choice(self, nodes, count = 1):
        '''根据概率份额选择节点
        nodes -由node组成的序列，node -dict：Ratio份额，Id节点标识。
        count -int：要选出的节点数目。
        '''
        assert len(nodes) != 0 and len(nodes) >= count
        RetLst = []
        totalRatio = sum([node['Ratio'] for node in nodes])
        while len(RetLst) < count:
            RandomInt = random.randrange(1, totalRatio + 1, 1)
            for node in nodes:
                RandomInt -= node['Ratio']
                if RandomInt <= 0 and node not in RetLst:
                    RetLst.append(node)
                    break
        if count == 1:
            return RetLst.pop(0)
        return RetLst
    
    def AddLotteryLog(self, AltarType, Award, TimeStamp,GainId,GainNum):
        '''记抽奖日志'''
        table = 'tb_altar_lottery'
        ValueClause = {}
        ValueClause['AltarType'] = AltarType
        ValueClause['UserId'] = self.uid
        ValueClause['AwardId'] = Award['AwardId']
        ValueClause['AwardQuality'] = Award['AwardQuality']
        ValueClause['AwardType'] = Award['SkyAwardType' if AltarType == 1 else 'LandAwardType'] 
        ValueClause['AwardTime'] = TimeStamp
        ValueClause['AwardDate'] = datetime.date.fromtimestamp(TimeStamp)
        ValueClause['GainId']=GainId
        ValueClause['GainNum']=GainNum
        AutoId = self.db.insert(table, ValueClause)
        if AutoId > 0 and Award['AwardQuality'] >= 4:
            table = 'tb_altar_rank'
            return self.db.insert(table, ValueClause)
        return False
    
    def getLotteryLog(self,AltarType,TimeStamp):
        '''获取抽奖记录'''
        table='tb_altar_lottery'
        field=['AwardType','AwardId','GainId','GainNum']
        where='UserId=%s AND AltarType=%s AND AwardDate="%s" ORDER By AwardTime desc Limit 10'%(self.uid,AltarType,datetime.date.fromtimestamp(TimeStamp))
        return self.db.out_rows(table,field,where)
    
    def getAltarRank(self, AltarType, TimeStamp, Page, PagePerNum,Flag = 1):
        '''获取幸运榜'''
        table = 'tb_altar_rank,tb_user'
        fields = ['tb_user.NickName', 'tb_user.UserId', 'tb_user.UserIcon', 'AwardType', 'AwardId', 'AwardQuality', 'AwardTime','GainId','GainNum']
        where = 'AltarType=%s AND AwardDate="%s" AND tb_user.UserId=tb_altar_rank.UserId' % (AltarType, datetime.date.fromtimestamp(TimeStamp))
        if Flag != 1:
            where += ' AND tb_altar_rank.UserId=%s' % self.uid
        where+=' ORDER BY AwardTime DESC LIMIT %s,%s'%((Page-1)*PagePerNum,PagePerNum)
        return self.db.out_rows(table, fields ,where)
    
    def getAltarRankCnt(self,AltarType,TimeStamp,Flag = 1):
        where='AltarType=%s AND AwardDate="%s"'% (AltarType, datetime.date.fromtimestamp(TimeStamp))
        if Flag != 1:
            where += ' AND UserId=%s' % self.uid
        return self.db.count('tb_altar_rank',where)
    
    def distLottery(self, AltarType, Award, TimeStamp, optId, classMethod):
        '''将抽奖的奖品根据类型分发给玩家'''
        AwardType = 'SkyAwardType' if AltarType == 1 else 'LandAwardType'
        print 'Award',Award
        if Award[AwardType] in (1, 2, 3, 4, 6):
            rewardMod = Gcore.getMod('Reward', self.uid)
            #道具卡，装备，武器
            #bagMod=Gcore.getMod('Bag',self.uid)
            if Award[AwardType] in (3, 4, 6):   #相应的资源卡或者道具
                rewardMod.reward(optId, "", 2, Award['ItemId'], Award['AwardNum'])
                return {'GainId': Award['ItemId'], 'GainNum': Award['AwardNum']}
                #bagMod.addGoods(2,Award['ItemId'],addLog=1)
            if Award[AwardType] in (1, 2):
                equalId = rewardMod.reward(optId, "", 1, Award['ItemId'], Award['AwardNum'])
                if type(equalId) in (list, tuple) and equalId:
                    equalId = equalId[0]
                if not equalId:
                    equalId = 0
                return {'GainId': equalId, 'GainNum': 1}
                #bagMod.addGoods(1,Award['ItemId'],addLog=1)
        if AltarType == 2 and Award[AwardType] == 5: 
            #黄金
            CoinType = 1
            CoinValue = Award["AwardNum"]
            modCoin = Gcore.getMod('Coin', self.uid)
            addCoin = modCoin.GainCoin(optId, CoinType, CoinValue, classMethod)
            return {'GainId': CoinType, 'GainNum': addCoin}
        if (AltarType==2 and Award[AwardType] == 9)or (AltarType==1 and Award[AwardType]in(5,7)):
            #给随机一名武将加经验或属性
            modGeneral = Gcore.getMod('General', self.uid)
            Generals = modGeneral.getMyGenerals()
            if not Generals: #玩家没有武将
                return {'GainId':0,'GainNum':0}
            LuckGeneral = random.choice(Generals)
            if Award[AwardType] == 7: #给武将增加经验
                ExpValue = Award["AwardNum"]
                modGeneral.incGeneralExp(LuckGeneral,ExpValue,LuckGeneral['GeneralLevel'])
            if Award[AwardType] in(9,5): #给武将增加属性
                force = speed = wit = leader = 0
                if Award['ItemId']==1:
                    #PropertyName = 'WitValue'
                    wit = Award['AwardNum']
                elif Award['ItemId']==2:
                    #PropertyName = 'ForceValue'
                    force = Award['AwardNum']
                elif Award['ItemId']==3:
                    #PropertyName = 'LeaderValue'
                    leader = Award['AwardNum']
                elif Award['ItemId']==4:
                    #PropertyName = 'SpeedValue'
                    speed = Award['AwardNum']
                #ProPertyValue = Award['AwardNum']
                #LuckGeneral[PropertyName] += ProPertyValue
                modTrain = Gcore.getMod('Building_train', self.uid)
                #应策划要求，改成和武将培养一样
                modTrain.saveTrainGeneral(LuckGeneral['GeneralId'], force, wit, speed, leader)
                #modGeneral.changeAttr(LuckGeneral['GeneralId'], force, speed, wit, leader)
                #modGeneral.updateGeneralById(LuckGeneral, LuckGeneral['GeneralId'])
            return {'GainId':LuckGeneral['GeneralType'],'GainNum':Award['AwardNum']}
        
#         if AltarType==1 and Award[AwardType] == 8: 
#             SoldierCfg = Gcore.getCfg('tb_cfg_soldier')
#             #随机增加士兵
#             #随机选出一种兵种
#             modBuilding=Gcore.getMod('Building',self.uid)
#             camps=modBuilding.getBuildingByType(6, TimeStamp = TimeStamp)
#             maxcampLevel=max(camps,key=lambda x:x['BuildingRealLevel'])['BuildingRealLevel']
#             UserCamp = self.getUserCamp()  
#             
#             buildingTypes=self.getMyBuildingType()
#             SoldierTypeLst = [SoldierType for SoldierType in SoldierCfg if SoldierType < 100 
#                               and SoldierCfg[SoldierType]['SoldierSide'] in [0, UserCamp, 4] 
#                               and SoldierCfg[SoldierType]['OpenLevel']<=maxcampLevel
#                               and SoldierCfg[SoldierType]['SpawnBuildingType'] in buildingTypes]
#             if not SoldierTypeLst:
#                 return {'GainId':0,'GainNum':0}
#             else:
#                 SoldierType = random.choice(SoldierTypeLst)
#         
#             modCamp = Gcore.getMod('Building_camp', self.uid)
#             Schools=modBuilding.getBuildingByType(7, TimeStamp = TimeStamp)
#             
#             Soldiers = modCamp.wrapGetSoldierNum(Schools, TimeStamp)
#             if Soldiers == -1:
#                 return {'GainId':0,'GainNum':0}
#             SoldierNum = sum(Soldiers.values())
#             MaxNum = modCamp.getMaxSoldierNum(Schools)
#             NewAddNum = min([MaxNum - SoldierNum, Award['AwardNum']])
#             modCamp.changeSoldierNum({SoldierType:NewAddNum})
#             
#             return {'GainId':SoldierType,'GainNum':NewAddNum}
        
        if Award[AwardType] == 8: #增加武将碎片
            pubMod = Gcore.getMod('Building_pub', self.uid)
            params = {Award['ItemId']: Award['AwardNum']}
            res = pubMod.changePatchNum(params)
            if res:
                return {'GainId': Award['ItemId'], 'GainNum': Award['AwardNum']}
            return {'GainId': Award['ItemId'], 'GainNum': Award['AwardNum']}
            
        if AltarType==2 and Award[AwardType]==10:
            #主角经验
            playMod=Gcore.getMod('Player',self.uid)
            playMod.addUserExp(0,Award['AwardNum'],optId)
            return {'GainId':0,'GainNum':0}

            
        if AltarType==2 and Award[AwardType]==7:
            #可强化
            equipMod= Gcore.getMod('Equip',self.uid)
            equipMod.changeStrengthNum(Award['AwardNum'])
            return{'GainId':0,'GainNum':0}
            
    def getMyBuildingType(self):
        table = self.tb_building()
        blist = self.db.out_list(table, 'BuildingType', 'UserId=%s'%self.uid)
        #types=self.db.query('SELECT BuildingType FROM `tb_building0` WHERE UserId=1012 group by BuildingType')
        #t=[type['BuildingType'] for type in types]
        return blist
        
#end class Building_altarMod

def _test():
    '''测试方法'''
    uid = 1012
    c = Building_altarMod(uid)
    now=time.time()
    c.getMyBuildingType()
    #天坛测试
    skyAltar=Gcore.getCfg('tb_cfg_altar_sky')
    for e in skyAltar.values():
        for s in e:
            print c.distLottery(1, s, now, 10554, 'distLottery')
    #地坛测试
    lankAltar=Gcore.getCfg('tb_cfg_altar_land')
    for e in lankAltar.values():
        for s in e:
            print c.distLottery(2, s, now, 10554, 'distLottery')
    

    
if __name__ == '__main__':
    _test()

