# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-1-13
# 游戏外部系统 ，装备系统

import random
from sgLib.core import Gcore, inspector
import sgLib.common as com

class EquipUI(object):
    """装备系统外部接口"""
    def __init__(self,uid = 0):
        self.uid = uid
        self.mod = Gcore.getMod('Equip',uid)
        self.coinMod = Gcore.getMod('Coin',uid)
    
    def GetStrengthNum(self,p={}):
        '''获取强化数量'''
        optId = 16000
        building = self.mod.getSmithyInfo()
        if not building:
            return Gcore.error(optId,-16000901)#建筑不存在
        buildingId = building['BuildingId']
#         self.mod.updateEquipsStatus()#更新装备状态
        
        strNum = self.mod.getMaxStrength(buildingId)
        strNum['MaxNum'] = 99999999#可用强化次数没有上限
        return Gcore.out(optId,strNum)
    
    @inspector(16001,['EquipId','GeneralId'])
    def EquipStrengthen(self,p={}):
        '''强化装备'''
        optId = 16001
        equipId = p['EquipId']
        generalId = p['GeneralId']
        building = self.mod.getSmithyInfo()
        if not building:
            return Gcore.error(optId,-16001901)#建筑不存在
        buildingId = building['BuildingId']
        equipInfo = self.mod.getEquipInfo(1,equipId)#装备信息
        if not equipInfo or equipInfo['UserId'] != self.uid:
            return Gcore.error(optId,-16001910)#装备不存在
        generalMod = Gcore.getMod('General',self.uid)
        generalInfo = generalMod.getLatestGeneralInfo(GeneralIds=generalId)
        
        if not generalInfo:
            return Gcore.error(optId,-16001001) #武将不存在
        if equipId not in self.mod.getEquipsByGeneral(generalId).values():
            return Gcore.error(optId,-16001004)#武器不在该武将身上
        
        equipType = equipInfo['EquipType']
        equipCfg = Gcore.getCfg('tb_cfg_equip',equipType)#装备配置
        strengthenLimit =  equipCfg.get('StrengthenLimit')
        equipPart = equipCfg.get('EquipPart')
        
        equipLevel = equipInfo.get('StrengthenLevel')
        generalLevel = generalInfo.get('GeneralLevel')
        free = self.mod.getMaxStrength(buildingId)['Available']
        if free == 0:
            return Gcore.error(optId,-16001002)#强化次数不足
        elif equipLevel >= generalLevel or equipLevel>= strengthenLimit:
            return Gcore.error(optId,-16001003)#已达最大等级
        
        equipUpCfg = Gcore.getCfg('tb_cfg_equip_up',(equipLevel+1,equipPart))#装备强化配置
        costType = equipUpCfg.get('StrengthenCostType')
        cost = equipUpCfg.get('CostQuality%s'%equipCfg.get('Quality'))
#         print '==Pre:',cost
        
        #计算内政对强化花费的影响
        interMod = Gcore.getMod('Inter',self.uid)
        cost = interMod.getInterEffect(8,cost)
#         print '===Reday:',cost
        flag = self.coinMod.PayCoin(optId,costType,cost,'EquipUI.EquipStrengthen',p)
        if flag>0:
            strengthData = {'StrengthenLevel':equipLevel+1,
                            'EnhanceForce':equipInfo['EnhanceForce']+equipCfg['GrowForce'],
                            'EnhanceWit':equipInfo['EnhanceWit']+equipCfg['GrowWit'],
                            'EnhanceSpeed':equipInfo['EnhanceSpeed']+equipCfg['GrowSpeed'],
                            'EnhanceLeader':equipInfo['EnhanceLeader']+equipCfg['GrowLeader']
                            }
            self.mod.equipStrengthen(buildingId, equipId,equipType,strengthData)
            generalMod.changeAttr(generalId,equipCfg['GrowForce'],equipCfg['GrowSpeed'],equipCfg['GrowWit'],equipCfg['GrowLeader'])
            recordData = {'uid':self.uid,'ValType':0,'Val':1,'EquipType':equipType,'EquipLevel':equipLevel+1}#成就、任务记录
            return Gcore.out(optId,achieve=recordData,mission=recordData)
        else:
            return Gcore.error(optId,-16001995) #支付失败 
    
          
    @inspector(16002,['EquipType'])
    def BuyEquip(self,p={}):
        '''购买装备'''
        optId = 16002
        equipType = p['EquipType']
        building = self.mod.getSmithyInfo()
        if not building:
            return Gcore.error(optId,-16002901)#建筑不存在
        # 出售配置
        eCfg = {}
        for cfg in Gcore.getCfg('tb_cfg_equip_sale').values():
            if cfg['EquipType']==equipType:
                eCfg = cfg
                break
        if not eCfg:
            return Gcore.error(optId,-16002002)#该装备不能购买
#         buildingLevel = building.get('BuildingRealLevel')
#         if buildingLevel<eCfg.get('RequireLevel'):
#             return Gcore.error(optId,-16002003)#购买该装备需要更高等级铁匠铺
        
        bagMod = Gcore.getMod('Bag',self.uid)
        if not bagMod.inclueOrNot(1,equipType,1):
            return Gcore.error(optId,-16002001)#背包空间不足
        
        equipCfg = Gcore.getCfg('tb_cfg_equip',equipType)
        cost = equipCfg.get('Price')
#         print '装备价钱',cost
#         print '我的金币',self.coinMod.getCoinNum(3)
        
        flag = self.coinMod.PayCoin(optId,3,cost,'EquipUI.BuyEquip',p)
        if flag>0:
            equipIds = Gcore.getMod('Bag',self.uid).addGoods(1,equipType,addLog=optId) #add by Lizr 0524
            
            recordData = {'uid':self.uid,'ValType':equipType,'Val':1}#成就、任务记录 
            return Gcore.out(optId,{'EquipId':equipIds[0]},mission=recordData)
        elif flag==-2:
            return Gcore.error(optId,-16002994)#支付失败
        else:
            return Gcore.error(optId,-16002995)#支付失败
        
    @inspector(16003,['SID'])   
    def BuyMyEquip(self,p={}):
        '''回购出售的装备'''
        optId = 16003
        sId = p['SID']
                
        building = self.mod.getSmithyInfo()
        if building is None:
            return Gcore.error(optId,-16003901)#建筑不存在
        self.mod.updateEquipsStatus()# 更新装备信息
        
        saleInfo = self.mod.getSaleInfo(sId)
        if not saleInfo:
            return Gcore.error(optId,-16003001)#没有出售记录
        
        saleStatus = saleInfo['Status']
        if saleStatus != 1:
            return Gcore.error(optId,-16003002)#该物品不能回购
        
        goodsType = saleInfo['GoodsType']
        goodsId = saleInfo['GoodsId']
        goodsNum = saleInfo['GoodsNum']
        
        if not Gcore.getMod('Bag',self.uid).inclueOrNot(goodsType,goodsId,goodsNum):
            return Gcore.error(optId,-16003003)#背包空间不足
        
        if goodsType in (1,4,5):#回购装备
            equipInfo = self.mod.getEquipInfo(goodsType,goodsId)
            cost = self.mod.calSalePrice(goodsType,equipInfo['EquipType'],equipInfo['StrengthenLevel'])
            
        else:#回购道具
            itemCfg = Gcore.getCfg('tb_cfg_item',goodsId)
            cost = itemCfg['PriceInShop']
            cost = cost*goodsNum
        
        flag = self.coinMod.PayCoin(optId,3,cost,'EquipUI.BuyMyEquip',p)
        if flag>0:
            self.mod.buyMyGoods(sId,goodsType,goodsId,goodsNum)
            return Gcore.out(optId)
        elif flag==-2:
            return Gcore.error(optId,-16003994)#货币不足
        else:
            return Gcore.error(optId,-16003995)#支付失败
    
    @inspector(16004,['Position'])    
    def SaleEquip(self,p={}):
        '''出售装备或道具'''
        optId = 16004

        goodsNum = p.get('GoodsNum',1)
        position = p['Position']

        building = self.mod.getSmithyInfo()
        if building is None:
            return Gcore.error(optId,-16004901)#建筑不存在
        modBag=Gcore.getMod('Bag',self.uid)
        gInfo = modBag.getFromPosition(position)
        if not gInfo:
            return Gcore.error(optId,-16004001)#物品不在背包中
        goodsType = gInfo['GoodsType']
        goodsId = gInfo['GoodsId']
        keepNum = gInfo['GoodsNum']
        if keepNum<goodsNum:
            return Gcore.error(optId,-16004002)#物品出售数量有误
        
        #计算当前可用
        buildingMod = Gcore.getMod('Building',self.uid)
        maxSave = buildingMod.cacStorageSpace(3)#最大储量
        curSave = self.coinMod.getCoinNum(3)#当前数量
        leftSave = maxSave-curSave

        flag = 0
        #出售流程
        if goodsType in (1,4,5):#出售装备
            equipInfo = self.mod.getEquipInfo(goodsType,goodsId)
            if not equipInfo:
                return Gcore.error(optId,-16004006)#装备不属于你

            cost = self.mod.calSalePrice(goodsType,equipInfo['EquipType'],equipInfo['StrengthenLevel'])
            if cost<=leftSave:
                flag = modBag.moveEquip(remove=goodsId,goodsType=goodsType)
            else:
                
                return Gcore.error(optId,-16004004)#没有足够空间存放货币
            
        else:#出售道具
            itemCfg = Gcore.getCfg('tb_cfg_item',goodsId)
            saled = itemCfg['SaleOrNot']
            if saled != 1:
                return Gcore.error(optId,-16004003)#该道具不可售
            cost = itemCfg['PriceInShop']
            cost = cost*goodsNum
            
            if cost<=leftSave:
                flag = modBag.useItems(goodsType,goodsNum,position)
            else:
                return Gcore.error(optId,-16004004)#没有足够空间存放货币
        
        #获得货币流程
        if flag:
            self.coinMod.GainCoin(optId,3,cost,'EquipUI.SaleEquip',p)
            self.mod.saleGoods(goodsType,goodsId,goodsNum)
            
            recordData = {'uid':self.uid,'ValType':goodsType,'Val':goodsNum,'GoodsId':goodsId}#成就、任务记录 
            return Gcore.out(optId,{'Cost':cost},mission=recordData)
        else:
            return Gcore.error(optId,-16004005)#出售失败
        
        
    def GetShopEquips(self,p={}):
        '''查询商店中玩家可回购装备以及背包信息'''
        optId = 16005
        building = self.mod.getSmithyInfo()
        if building is None:
            return Gcore.error(optId,-16005901)#建筑不存在
        result = self.mod.getSaleGoods()
        result['Sale'] = com.list2dict(result['Sale'],offset=0)
        if not result['Sale']:
            del result['Sale']
        bagMod = Gcore.getMod('Bag',self.uid)
        bagGoods = bagMod.getGoods(0)
        bag = {}
        bag['GS'] = com.list2dict(bagGoods, offset=0)
        bag['Size'] = bagMod.getBagSize()
        result['Bag'] = bag
        return Gcore.out(optId,result)
    
    @inspector(16006,['From','To'])
    def DivertEquip(self,p={}):
        '''装备传承'''
        optId = 16006
        fromId = p['From']
        toId = p['To']
        fromEquip = self.mod.getEquipInfo(1,fromId)
        toEquip = self.mod.getEquipInfo(1,toId)
        
        if not fromEquip or not toEquip:
            return Gcore.error(optId,-16006999)#参数无效
        
        if (fromEquip['EquipStatus'] not in (1,2)) or (toEquip['EquipStatus'] not in (1,2)):
            return Gcore.error(optId,-16006001)#装备不存在
        fromLevel = fromEquip.get('StrengthenLevel')
        toLevel = toEquip.get('StrengthenLevel')
        fromType = fromEquip.get('EquipType')
        toType = toEquip.get('EquipType')
        fromCfg = Gcore.getCfg('tb_cfg_equip',fromType)
        toCfg = Gcore.getCfg('tb_cfg_equip',toType)
        toMaxLevel = toCfg.get('StrengthenLimit')
        
        if fromLevel<1:
            return Gcore.error(optId,-16006002)#源装备等级大于0
        if toLevel>=toMaxLevel:
            return Gcore.error(optId,-16006003)#目标装备等级已达最大
        
        equipUpCfg = Gcore.getCfg('tb_cfg_equip_up')
        
        #判断目标装备是否穿戴在武将身上，升级受武将等级限制
        toGeneralId = toEquip.get('GeneralId')
        generalInfo = Gcore.getMod('General',self.uid).getLatestGeneralInfo(GeneralIds=toGeneralId)
        generalLevel = generalInfo['GeneralLevel'] if (toGeneralId and generalInfo) else 9999
        
        #计算源装备强化总强化费用
        fromCost = 0
        fromPart = fromCfg['EquipPart']
        fromQuality = fromCfg['Quality']
        for i in range(1,fromLevel+1):
            fromCost += equipUpCfg[(i,fromPart)]['CostQuality%s'%fromQuality]
        
        
        #计算传承后等级
        toLevelUp,leftCost = self._calLevelByCost(toType,toLevel,fromCost,min(toMaxLevel,generalLevel)) 
        fromLevelDown = self._calLevelByCost(fromType,0,leftCost)[0]
        
        fromData = {'EnhanceForce':fromCfg['AddForce']+fromCfg['GrowForce']*fromLevelDown,
                    'EnhanceLeader':fromCfg['AddLeader']+fromCfg['GrowLeader']*fromLevelDown,
                    'EnhanceSpeed':fromCfg['AddSpeed']+fromCfg['GrowSpeed']*fromLevelDown,
                    'EnhanceWit':fromCfg['AddWit']+fromCfg['GrowWit']*fromLevelDown,
                    'StrengthenLevel':fromLevelDown
                    }
        toData = {'EnhanceForce':toCfg['AddForce']+toCfg['GrowForce']*toLevelUp,
                    'EnhanceLeader':toCfg['AddLeader']+toCfg['GrowLeader']*toLevelUp,
                    'EnhanceSpeed':toCfg['AddSpeed']+toCfg['GrowSpeed']*toLevelUp,
                    'EnhanceWit':toCfg['AddWit']+toCfg['GrowWit']*toLevelUp,
                    'StrengthenLevel':toLevelUp
                    }
        divertCost = Gcore.loadCfg(Gcore.defined.CFG_EQUIP).get('DivertCost')
        divertCostType = Gcore.loadCfg(Gcore.defined.CFG_EQUIP).get('DivertCostType')
        payState = self.coinMod.PayCoin(optId,divertCostType,divertCost,'EquipUI.DivertEquip',p)
        if payState:
            self.mod.updateEquipInfo(1,fromData,'UserId=%s AND EquipId=%s'%(self.uid,fromId))
            self.mod.updateEquipInfo(1,toData,'UserId=%s AND EquipId=%s'%(self.uid,toId))
            return Gcore.out(optId,{'FromInfo':fromData,'ToInfo':toData,'Cost':payState})
        elif payState==-2:
            return Gcore.error(optId,-16006994)#货币不足
        else:
            return Gcore.error(optId,-16006995)#支付失败
        
        

    @inspector(16007,['UPT','EID','OFS'])
    def HighEquipStrengthen(self,p={}):
        '''兵书宝物升级'''
        optId = 16007
        goodsType = p['UPT']
        equipId = p['EID']
        offerIds = p['OFS']
        
        if (not isinstance(offerIds,(list,tuple))) or (goodsType not in (4,5)) or (not offerIds) or(equipId in offerIds):
            return Gcore.error(optId,-16007999)
        cfgEquipTable = self.mod.getCfgEquipTB(goodsType)
        
        equipInfo = self.mod.getEquipByIds(goodsType,equipId)
        if not equipInfo:
            return Gcore.error(optId,-16007001)#装备不存在

        generalId = equipInfo['GeneralId']

        generalInfo = Gcore.getMod('General',self.uid).getLatestGeneralInfo(GeneralIds=generalId)
        if not generalId or not generalInfo:
            return Gcore.error(optId,-16007002)#须让武将戴上才能升级
        
        equipLevel = equipInfo.get('StrengthenLevel')
        generalLevel = generalInfo.get('GeneralLevel')
        
        equipCfgs = Gcore.getCfg(cfgEquipTable)
        equipUpCfgs = Gcore.getCfg(cfgEquipTable+'_up')
        
        equipType = equipInfo.get('EquipType')
        equipCfg = equipCfgs.get(equipType)
        strengthenLimit = equipCfg['StrengthenLimit']
        if equipLevel>= generalLevel or equipLevel>=strengthenLimit:
            return Gcore.error(optId,-16007003)#已达最大等级
        
        #计算升级消耗货币，增加的经验
        offers = self.mod.getEquipByIds(goodsType,offerIds)#返回列表
        strengthenCostType = equipCfg['NeedCostType']
        deleteIds = []
        strengthCost = 0
        strengthGetExp = 0
        
        for offer in offers:
            deleteIds.append(offer['EquipId'])
            offerType = offer.get('EquipType')
            offerCfg = equipCfgs.get(offerType)
            offerUpCfg = equipUpCfgs.get(offer.get('StrengthenLevel'))
            
            baseExp = offerCfg['BaseExp']
            offerQuality = offerCfg['Quality']
            strengthGetExp = strengthGetExp+baseExp+offerUpCfg['Offer%s'%offerQuality]
            strengthCost += offerCfg['NeedCost']
        #判断是否爆击
        exploded = 0 #是否爆击
        explodeRatio = Gcore.loadCfg(Gcore.defined.CFG_EQUIP)['ExplodeRatio'][str(goodsType)]
        explodeTimes = Gcore.loadCfg(Gcore.defined.CFG_EQUIP)['ExplodeTimes'][str(goodsType)]
        if random.randint(1,100)<=explodeRatio:
            strengthGetExp = strengthGetExp*explodeTimes
            exploded = 1 
        
        payState = self.coinMod.PayCoin(optId,strengthenCostType,strengthCost,'EquipUI.HighEquipStrengthen',p)
        if payState>0:
            newLevel,newExp = self.mod.highEquipStengthen(goodsType,equipId,strengthGetExp)
            Gcore.getMod('Bag',self.uid).deleteEquips(goodsType,deleteIds)
            return Gcore.out(optId,{'NL':newLevel,'EXP':newExp,'EXPD':exploded})
        elif payState==-2:
            return Gcore.error(optId,-16007994)#货币不足
        else:
            return Gcore.error(optId,-16007995)#支付失败
    
        
    def _calLevelByCost(self,equipType,currentLevel,cost,levelLimit=None):
        '''根据费用计算装备升级'''
        equipUpCfg = Gcore.getCfg('tb_cfg_equip_up')
        equipCfg = Gcore.getCfg('tb_cfg_equip',equipType)
        eq = equipCfg['Quality']
        ep = equipCfg['EquipPart']
        if levelLimit is None:
            levelLimit = equipCfg['StrengthenLimit']
        toLevelUpCost = equipUpCfg.get((currentLevel+1,ep)).get('CostQuality%s'%eq)
        while currentLevel<levelLimit and cost>=toLevelUpCost:
            currentLevel += 1
            cost -= toLevelUpCost
            toLevelUpCost = equipUpCfg.get((currentLevel+1,ep)).get('CostQuality%s'%eq)
        return (currentLevel,cost)
        
        

    
def _test():
    """注释"""
#     print Gcore.getCfg('tb_cfg_nickname')
    uid = 44493
#    bid = 41#铁匠铺ID
    c = EquipUI(uid)
#     c.EquipStrengthen({'EquipId':4,'GeneralId':8})#1003
#     print c.GetStrengthNum()
#     c.BuyEquip({'EquipType':51})
#     c.BuyMyEquip({'SID':196})
        
#    print c.SaleEquip({
#                "Position":     1,
#                "GoodsNum":     1
#        })
#     c.BuyMyEquip({'EquipId':2})
#     c.GetShopEquips()
#    Gcore.loadCfg(Gcore.defined.)
    print c.HighEquipStrengthen({'UPT':4,'EID':1,'OFS':[24]})
#     print c.DivertEquip({'From':3770,'To':3992})


if __name__ == '__main__':
    _test()
    
    