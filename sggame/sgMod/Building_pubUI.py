# -*- coding:utf-8 -*-
# author:zhoujingjiang
# date:2013-1-3
# 游戏外部接口:招贤馆

import sys
import copy
import random

from sgLib.core import Gcore, inspector

class Building_pubUI(object):
    '''招贤馆功能外部接口'''
    def __init__(self, uid):
        self.mod = Gcore.getMod('Building_pub', uid)
        self.uid = uid
        
    @inspector(15006, ['BuildingId'])
    def GetInviteUI(self, param = {}):
        '''招贤馆：招募界面'''
        optId = 15006
        
        BuildingId = param['BuildingId']
        RequestTimeStamp = param['ClientTime']
        
        InviteInfo = self.mod.getInvite()
        modBuilding = Gcore.getMod('Building', self.uid)
        BuildingInfo = modBuilding.getBuildingById(BuildingId, TimeStamp = RequestTimeStamp)
        if not BuildingInfo:
            return Gcore.error(optId, -15006901) #用户没有该建筑
        if BuildingInfo['BuildingState'] == 1:
            return Gcore.error(optId, -15006902) #建筑正在建造
        if BuildingInfo['BuildingType'] != 13:
            return Gcore.error(optId, -15006903) #该建筑不是招贤馆
        BuildingLevel = BuildingInfo['BuildingRealLevel']  
        
        if not InviteInfo:
            print '第一次招募'
            ChosenGenerals = self.mod.chooseGenerals(GeneralNum=3, IsFirst=True)
            self.mod.insertInvite(ChosenGenerals, BuildingLevel, RequestTimeStamp)
            RemainedTime = Gcore.getCfg('tb_cfg_building_up', key = (13, BuildingLevel), field = 'RefreshValue')
            return Gcore.out(optId, body = {"RemainedTime":RemainedTime, 
                                            "Generals":ChosenGenerals, 
                                            'CostValue':5}) #系统错误 (招募表中此玩家初始记录)
        
        print 'InviteInfo', InviteInfo
        
        #SpeedCount = self.mod.cacSpeedCount(InviteInfo['SpeedCount'], InviteInfo['LastSpeedDate'], RequestTimeStamp)
        #SpeedCount += 1
        #CostValue = SpeedCount * 2
                
        CostValue = 5 #读配置 - 招贤馆每次刷新所用的黄金数量
        RetDic = {}
        RetDic['CostValue'] = CostValue   
        if RequestTimeStamp < InviteInfo['EndTime']:
            RefreshTimeRemained = InviteInfo['EndTime'] - RequestTimeStamp
            
            RetDic['RemainedTime'] = RefreshTimeRemained
            RetDic['Generals'] = [InviteInfo['GeneralId1'],
                                  InviteInfo['GeneralId2'],
                                  InviteInfo['GeneralId3']]
            
            return Gcore.out(optId, RetDic)
        else:
            RefreshValue = Gcore.getCfg('tb_cfg_building_up', key = (13, BuildingLevel), field = 'RefreshValue')
            RefreshTimeRemained = RefreshValue - (RequestTimeStamp - InviteInfo['EndTime']) % RefreshValue   
            RefreshTimeStamp = RequestTimeStamp - (RequestTimeStamp - InviteInfo['EndTime']) % RefreshValue
            ChosenGenerals = self.mod.chooseGenerals()
            self.mod.updateInvite(ChosenGenerals, BuildingLevel, RefreshTimeStamp)
            
            RetDic['RemainedTime'] = RefreshTimeRemained            
            RetDic['Generals'] = ChosenGenerals
            return Gcore.out(optId, RetDic)
    
    @inspector(15007, ['GeneralType'])
    def InviteGenerals(self, param = {}):
        '''招贤馆：招募武将'''
        optId = 15007

        GeneralType = param["GeneralType"]
        InviteTimeStamp = param['ClientTime']

        InviteInfo = self.mod.getInvite()
        if not InviteInfo or InviteTimeStamp > InviteInfo['EndTime']:
            return Gcore.error(optId, -15007004)
        
        Invites = [InviteInfo["GeneralId1"], InviteInfo["GeneralId2"], InviteInfo["GeneralId3"]]
        if GeneralType not in Invites:
            return Gcore.error(optId, -15007001) #此武将不可招募
        
        modGeneral = Gcore.getMod('General', self.uid)
        if GeneralType in modGeneral.getGeneralTypeList():
            return Gcore.error(optId, -15007002) #已有该类型武将

        FreeGeneralHomes = self.mod.getFreeGeneralHomes(InviteTimeStamp)
        if not FreeGeneralHomes:
            return Gcore.error(optId, -15007003) #没有剩余的点将台
        
        GeneralInfo = Gcore.getCfg('tb_cfg_general', key = GeneralType)
        InviteCostType = GeneralInfo["InviteCostType"]
        InviteCost = GeneralInfo["InviteCost"]
        
        #开始支付流程 
        print 'InviteCostType', InviteCostType
        print 'InviteCost', InviteCost
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        pay = modCoin.PayCoin(optId, InviteCostType, InviteCost, classMethod, param)
        if pay < 0:
            return Gcore.error(optId, -15007995) #支付失败
            
        GeneralId = modGeneral.addNewGeneral(GeneralType, min(FreeGeneralHomes), InviteTimeStamp)
        
        recordData = {'uid':self.uid,'ValType':GeneralType,'Val':1}#成就记录
        return Gcore.out(optId
                         , body = {"Location":min(FreeGeneralHomes), "GeneralId":GeneralId, "GeneralType":GeneralType}
                         , achieve=recordData,mission=recordData)
    
    @inspector(15008, ['BuildingId'])
    def SpeedupInvite(self, param = {}):
        '''招贤馆：黄金加速刷新'''
        optId = 15008
        
        BuildingId = param['BuildingId']
        SpeedUpTimeStamp = param['ClientTime']
    
        modBuilding = Gcore.getMod('Building', self.uid)
        BuildingInfo = modBuilding.getBuildingById(BuildingId, TimeStamp = SpeedUpTimeStamp)
        if not BuildingInfo:
            return Gcore.error(optId, -15008901) #用户没有该建筑
        if BuildingInfo['BuildingState'] == 1:
            return Gcore.error(optId, -15008902) #建筑正在建造
        if BuildingInfo['BuildingType'] != 13:
            return Gcore.error(optId, -15008903) #该建筑不是招贤馆       
        
        InviteInfo = self.mod.getInvite()
        if not InviteInfo or InviteInfo['EndTime'] < SpeedUpTimeStamp:
            return Gcore.error(optId, -15008001) #没有招募记录
        
        #获取加速次数
        SpeedCount = self.mod.cacSpeedCount(InviteInfo['SpeedCount'], InviteInfo['LastSpeedDate'], SpeedUpTimeStamp)
        SpeedCount += 1
        
        coinValue = 5 #读配置
             
        #开始支付流程 
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        pay = modCoin.PayCoin(optId, 1, coinValue, classMethod, param)
        if pay < 0:
            return Gcore.error(optId, -15008995) #支付失败
        
        BuildingLevel = BuildingInfo['BuildingRealLevel']    
        ChosenGenerals = self.mod.chooseGenerals()
        self.mod.updateInvite(ChosenGenerals, BuildingLevel, SpeedUpTimeStamp, SpeedCount)
        
        RemainedTime = Gcore.getCfg('tb_cfg_building_up', (13, BuildingLevel), 'RefreshValue')   
        RetDic = {}
        RetDic["CostValue"] = coinValue
        RetDic["NextCostValue"] = coinValue
        RetDic["RemainedTime"] = RemainedTime
        RetDic["Generals"] = ChosenGenerals
        return Gcore.out(optId, RetDic)
    
    @inspector(15131, ['ItemId'])
    def ExchangeGeneralCard(self, para={}):
        '''兑换武将卡'''
        optId = 15131
        
        item_id = para['ItemId']
        stat = self.mod.exchangeGeneralCard(item_id)
        if stat is False:
            return Gcore.error(optId, -15131001) #数量不足，兑换失败
                                            # + 也可能是ItemId不正确
        else:
            #将武将卡放到背包
            modBag = Gcore.getMod('Bag', self.uid)
            modBag.addGoods(2, item_id, 1, False)
            recordData = {'uid':self.uid,'ValType':item_id,'Val':1}#任务
            return Gcore.out(optId, stat, mission=recordData)

    @inspector(15132)
    def GetPatchNum(self, para={}):
        '''获取碎片的数量'''
        optId = 15132
        
        #获得碎片的数量
        patchs_num = self.mod.getPatchNum()
        #获得各种武将卡的数量
        cards_num = self.mod.getGeneralCardNum() #是个字典
        
        #武将卡的所有类型
        item_ids = Gcore.getCfg('tb_cfg_general_patch').keys()
        
        #组合成返回结果
        rels = []
        for item_id in item_ids:
            item = {'ItemId':item_id, 'Number':cards_num.get(item_id, 0), 
                    'Patch1':0, 'Patch2':0,
                    'Patch3':0, 'Patch4':0,
                    }
            for patch_num in patchs_num:
                if patch_num['ItemId'] == item_id:
                    item.update(patch_num)
                    break
            #if item['Number'] or item['Patch1'] or item['Patch2'] or \
            #    item['Patch3'] or item['Patch4']:
            rels.append(copy.deepcopy(item))
        
        return Gcore.out(optId, rels)
    
    @inspector(15133, ['ItemId', 'ItemNum'])
    def ConvertGeneralCard(self, para={}):
        '''将武将卡转换成晶石'''
        optId = 15133
        
        ItemId = para['ItemId']
        ItemNum = para['ItemNum']
        
        cfg = Gcore.getCfg('tb_cfg_general_patch', ItemId)
        if cfg is None:
            return Gcore.error(optId, -15133001) #武将卡ID不正确
        convert_min = cfg['ConvertMin']
        convert_max = cfg['ConvertMax']
        goods_id = cfg['ConvertItemId']

        rand = random.randint(convert_min, convert_max)
        print '每个武将卡可兑换%d个晶石' % rand
        goods_num = int(ItemNum) * rand

        modBag = Gcore.getMod('Bag', self.uid)
        item_own = modBag.countGoodsNum(ItemId)
        if ItemNum > item_own:
            return Gcore.error(optId, -15133002) #武将卡数量不足
        
        stat = modBag.addGoods(2,
                               goods_id,
                               goods_num,
                               False)
        if stat <= 0:
            return Gcore.error(optId, -15133003) #背包空间不足
        
        stat = modBag.useItems(ItemId, ItemNum)
        if stat != 1:
            return Gcore.error(optId, -15133004) #武将卡数量不足(并发导致)
        
        body = {}
        body['GainItemId'] = goods_id
        body['GainItemNum'] = goods_num
        
        return Gcore.out(optId, body)        
#end class BuildingUI

def _test():
    '''测试'''
    uid = 43557
    c = Building_pubUI(uid)
    print c.ExchangeGeneralCard({})
    #print c.ConvertGeneralCard({"ItemId":1101, "ItemNum":1})
    
if __name__ == '__main__':
    _test()
    Gcore.runtime()