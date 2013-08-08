# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-2-5
#模块说明

import time
from sgLib.core import Gcore, inspector
import sgLib.common as com

class BookUI(object):
    def __init__(self, uid):
        self.mod = Gcore.getMod('Book', uid)
        self.uid = uid
        
    @inspector(15050,['BuildingId'])
    def GetUpgradingTech(self,p={}):
        '''查询正在学习中的科技'''
        optId = 15050
        buildingId = p.get('BuildingId') 
        tech = self.mod.getUpgradingTech(buildingId)
        flag = 1 if tech else 0
        return Gcore.out(optId,{'IsUpgrading':flag,'Tech':tech})
    
    @inspector(15051,['BuildingId'])     
    def GetMyTech(self,p={}):
        '''获取我学习的所有科技'''
        optId = 15051
        buildingId = p['BuildingId']
        building = Gcore.getMod('Building',self.uid).getBuildingById(buildingId)
        if not building:
            return Gcore.out(optId)
        buildingType = building.get('BuildingType')
        
        st = self.mod.getTechs(1)#兵种科技
        soldierTechs = []#书院研究科技
        wallTechs = []#城墙研究科技
        
        for k,v in enumerate(st):
            if v['TechType']>=200:
                wallTechs.append(v)
            else:
                soldierTechs.append(v)
        
        if buildingType==12:#书院
            interTechs = self.mod.getTechs(2)#内政科技     
            reData = {'SoldierTechs':soldierTechs,'InterTechs':interTechs}
        else:
            reData = {'WallTechs':wallTechs}
        return Gcore.out(optId,reData)
       
    @inspector(15052,['TechCategory','TechType','BuildingId'])
    def UpgradeTech(self,p={}):
        '''学习科技,返回正在学习的科技
        :如果该科技未学习过则添加一条记录
        @param TechCategory:1兵种，2内政

        '''
        optId = 15052
        techCategory = p.get('TechCategory')
        techType = p.get('TechType')  
        buildingId = p.get('BuildingId')
        now = p.get('ClientTime')
         
        #判断传入参数是否合法
        if techCategory == 1 and techType<200:#兵种，器械科技
            techCfg = Gcore.getCfg('tb_cfg_tech_soldier')
            buildingType = 12
            ts = [k[0] for k in techCfg.keys()]
            if techType not in ts:
                return Gcore.error(optId,-15052999)
        
        elif techCategory == 1 and 200<techType<300:
            techCfg = Gcore.getCfg('tb_cfg_wall_school')
            buildingType = 19
            ts = [k[0] for k in techCfg.keys()]
            if techType not in ts:
                return Gcore.error(optId,-15052999) 
            
        elif techCategory == 2 :#内政科技1-10
            techCfg = Gcore.getCfg('tb_cfg_tech_inter')
            buildingType = 12
            ts = [k[0] for k in techCfg.keys()]
            if techType not in ts:
                return Gcore.error(optId,-15052999)  
        else:
            return Gcore.error(optId,-15052999)
        
        #获取外史院建筑信息
        building = Gcore.getMod('Building',self.uid).getBuildingById(buildingId)
        if not building or building.get('BuildingType')!=buildingType:
            return Gcore.error(optId,-15052901)#建筑不存在
        
        bookLevel = building.get('BuildingRealLevel')
        if bookLevel<1:
            return Gcore.error(optId,-15052905)#建筑正在建造
        
        flag = self.mod.getUpgradingTech(buildingId)
        if flag:
            return Gcore.error(optId,-15052001)#学习占用中
        
        tech = self.mod.getTech(techCategory,techType)
        techLevel = tech.get('TechLevel')
        techMaxLevel = self.mod.getTechMaxLevel(techCategory,techType,bookLevel)
        if techMaxLevel is None or techLevel >= techMaxLevel:
            return Gcore.error(optId,-15052002)#建筑等级不足
        
        techCfg = techCfg.get((techType,techLevel+1))#获取科技类型与等级配置
        needTime = techCfg.get('LearnTime')
        cost = techCfg.get('LearnCost')
        costType = techCfg.get('CostType')
        
        #书院升级科技时间受等级影响
        if buildingType==12:
            discount = 1-Gcore.getCfg('tb_cfg_building_up',(12,bookLevel),'ShortenRatio')
            needTime = techCfg.get('LearnTime')*discount
        
        payStatus = Gcore.getMod('Coin',self.uid).PayCoin(optId,costType,cost,'BookUI.UpgradeTech')#军资学习
#         payStatus = 1
        if payStatus >0:#支付成功
            data = {'TechLevel':techLevel+1,
                    'LastStartTime':now,
                    'LastEndTime':now+needTime,
                    'BuildingId':buildingId}
            
            self.mod.updateTech(techCategory,techType,data)
        elif payStatus == -2:
            return Gcore.error(optId,-15053994)#货币不足
        else:
            return Gcore.error(optId,-15053995)#支付失败
        
        tech = self.mod.getUpgradingTech(buildingId)
        if techCategory == 2:#内政科技，更新内政加成
            interMod = Gcore.getMod('Inter',self.uid)
            interMod.updateInterTech(techType,techLevel+1,now+needTime)
        recordData = {'uid':self.uid,'ValType':techCategory,'Val':1}#成就、任务记录 
        return Gcore.out(optId,{'Tech':tech},mission=recordData)
        
        
        
    @inspector(15053,['BuildingId'])
    def SpeedUpTech(self,p={}):
        '''加速学习科技'''
        optId = 15053
        buildingId = p.get('BuildingId') 
        now = p.get('ClientTime')
#         now = time.time()
        
        building = Gcore.getMod('Building',self.uid).getBuildingById(buildingId)
        if not building or building.get('BuildingType') not in [12,19]:
            return Gcore.error(optId,-15053901)#建筑不存在
        buildingType = building.get('BuildingType')
        
        tech = self.mod.getUpgradingTech(buildingId)
        if not tech:
            return Gcore.error(optId,-15053001)#科技已完成学习
        
        techCategory = tech.get('TechCategory')
        techType = tech.get('TechType')
        speedupTime = tech.get('LastEndTime')-now
        cost = com.calSpeedCost(2 if buildingType==12 else 6,speedupTime)
        coinMod = Gcore.getMod('Coin',self.uid)

        payStatus = coinMod.PayCoin(optId,1,cost,'BookUI.SpeedUpTech')
        if payStatus>0:
            data= {'LastEndTime':now}
            self.mod.updateTech(techCategory,techType,data)

        elif payStatus == -2:
            return Gcore.error(optId,-15053994)#货币不足
        else:
            return Gcore.error(optId,-15053995)#支付失败
        
        if techCategory==2:#内政科技，更新内政加成
            interMod = Gcore.getMod('Inter',self.uid)
            techLevel = tech.get('TechLevel')
            interMod.updateInterTech(techType,techLevel,now)
        
        recordData = {'uid':self.uid,'ValType':techCategory,'Val':1,'BuildingType':buildingType}#成就、任务记录  
        return Gcore.out(optId, {'TechCategory':techCategory,'TechType':techType,'Cost':cost},mission=recordData)
    
    @inspector(15054,['TechType','BuildingId'])
    def UpgradeWallTech(self,p={}):
        '''城墙升级科技'''
        optId = 15054
        techType = p.get('TechType')  
        buildingId = p.get('BuildingId')
        now = time.time() 
        techCategory = 1
        #判断传入参数是否合法

        techCfg = Gcore.getCfg('tb_cfg_wall_school')
        ts = [k[0] for k in techCfg.keys()]
        if techType<200 or techType not in ts:
            return Gcore.error(optId,-15054999)  

        
        #获院建筑信息
        building = Gcore.getMod('Building',self.uid).getBuildingById(buildingId)
        if not building or building.get('BuildingType')!=19:
            return Gcore.error(optId,-15054901)#建筑不存在
        
        bookLevel = building.get('BuildingRealLevel')
        flag = self.mod.getUpgradingTech(buildingId)
        if flag:
            return Gcore.error(optId,-15054001)#学习占用中
        
        tech = self.mod.getTech(techCategory,techType)
        techLevel = tech.get('TechLevel')
        techMaxLevel = self.mod.getTechMaxLevel(techCategory,techType,bookLevel)
        if techMaxLevel is None or techLevel >= techMaxLevel:
            return Gcore.error(optId,-15054002)#城墙等级不足
        
        techCfg = techCfg.get((techType,techLevel+1))#获取科技类型与等级配置
        
        needTime = techCfg.get('LearnTime')
        itemId = techCfg.get('ItemIdNeed')
        itemNum = techCfg.get('ItemNeedNeed')
        
        flag = Gcore.getMod('Bag',self.uid).useItems(itemId,itemNum)

        if flag:#支付成功
            data = {'TechLevel':techLevel+1,
                    'LastStartTime':now,
                    'LastEndTime':now+needTime,
                    'BuildingId':buildingId}
            
            self.mod.updateTech(techCategory,techType,data)
        else:
            return Gcore.error(optId,-15054003)#道具数量不足
        
        tech = self.mod.getUpgradingTech(buildingId)
        return Gcore.out(optId,{'Tech':tech})
    

def _test():
    '''测试方法'''
    uid = 44130
    b = BookUI(uid)
    print b.GetUpgradingTech({'BuildingId':17588})
    
#     print b.GetMyTech()
#     print b.UpgradeTech({'TechCategory':1,'TechType':6,'BuildingId':11464})
#    print b.SpeedUpTech({'Cost':500})
#    print b.UpgradeTech({'BuildingId':18,'TechCategory':1,'TechType':3})
#    print (1-Gcore.getCfg('tb_cfg_building_up',(12,11),'ShortenRatio'))



if __name__ == '__main__':
    _test()