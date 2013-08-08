# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-1-13
# 装备模型

import time
import math
from sgLib.core import *
from sgLib.base import Base
from sgLib.defined import *
import sgLib.common as comm



class EquipMod(Base):
    """装备模型"""
    def __init__(self,uid):
        Base.__init__(self, uid)
        self.uid = uid
        self._equipTB = {1:Base.tb_equip(self),4:'tb_equip_warbook',5:'tb_equip_treasure'}
        self._cfgEquipTB = {1:'tb_cfg_equip',4:'tb_cfg_equip_warbook',5:'tb_cfg_equip_treasure'}
        
#------------------------------------------------------------------------------ 
#装备内部接口

    

    def getEquipTB(self,goodsType):
        '''获取装备表'''
        return self._equipTB.get(goodsType)
    
    def getCfgEquipTB(self,goodsType):
        '''获取装备配置表'''
        return self._cfgEquipTB.get(goodsType)

    def getEquipsByGeneral(self,generalId):
        '''获取武将装备信息'''
        generalTable = self.tb_general()
        ids = self.db.out_fields(generalTable,['HelmetId','ArmourId','SashId','BootsId','WeaponId','JewelryId'],'GeneralId=%s'%generalId)
        if ids is None:
            return {}
        return ids
    
    def getAllValidEquip(self):
        '''获取玩家的所有可用装备'''
        table = self.tb_equip()        
        fields = ['EquipId','EquipType','StrengthenLevel',
                  'EnhanceForce','EnhanceSpeed','EnhanceWit','EnhanceLeader',
                  'GeneralId']
        where = 'UserId=%s AND EquipStatus not in (3, 4)' % self.uid
        es = self.db.out_rows(table,fields, where)
        for e in es:
            e['Price'] = self.calSalePrice(1,e['EquipType'],e['StrengthenLevel'])
        return es
    
    def validEquipOnGeneral(self,equipId,generalLevel,goodsType=1):
        '''
        :验证武将能否穿戴某装备
        @param equipId:装备Id
        @param generalId:武将等级
        @param goodsType:装备类型1普通4兵书5宝物
        @return: 可以穿戴返回True
        '''
        equipInfo = self.getEquipInfo(goodsType,equipId,['EquipType','StrengthenLevel'])
        requireLevel = Gcore.getCfg(self.getCfgEquipTB(goodsType),equipInfo['EquipType'],'RequireLevel')
        if generalLevel<requireLevel or equipInfo['StrengthenLevel']>generalLevel:
            return False
        return True
    
    
    def addEquipLog(self,optId,goodsType,equipType,num):
        '''装备获得日志'''
        data = {'UserId':self.uid,
                'UserType':Gcore.getUserData(self.uid,'UserType'),
                'OptId':optId,
                'GoodsType':goodsType,
                'EquipType':equipType,
                'GetNum':num,
                'CreateTime':time.time()}
        self.db.insert('tb_log_equip',data,isdelay=True)
    
#------------------------------------------------------------------------------ 
#模块内调用
        
    def initEquip(self,goodsType,equipType,obtainWay=1):
        ''' 初始化一件装备'''
        ctime = time.time()
        if goodsType==1:
            eb = Gcore.getCfg('tb_cfg_equip',equipType)
            data = {'UserId':self.uid,'EquipType':equipType,
                    'StrengthenLevel':0,
                    'EnhanceForce':eb['AddForce'],'EnhanceWit':eb['AddWit'],
                    'EnhanceLeader':eb['AddLeader'],'EnhanceSpeed':eb['AddSpeed'],
                    'ObtainWay':obtainWay,'ObtainTime':ctime
                    }
        elif goodsType in (4,5):#兵书,宝物
            data = {'UserId':self.uid,'EquipType':equipType,'ObtainTime':ctime}
        else:
            return 0
        return self.db.insert(self.getEquipTB(goodsType),data)
    
    
    def getSmithyInfo(self):
        '''
        :查询铁匠铺信息
        '''
        buildingMod = Gcore.getMod('Building',self.uid)
        b = buildingMod.getBuildingByType(11)
        b = b[0] if len(b)>=1 else None 
        return b

   
                
        
    
    def equipStrengthen(self,buildingId,equipId,equipType,strengthData):
        '''装备强化'''
        equipTable = self.tb_equip()
        needTime = Gcore.loadCfg(Gcore.defined.CFG_EQUIP)['StrengthenCD']
#         needTime = Gcore.loadCfg(CFG_BUILDING)['MakeCD']['11']#从配置获取冷却时间
        createTime = time.time()
        stopTime = time.time()+int(needTime)
        record = {'UserId':self.uid,
                  'UserType':Gcore.getUserData(self.uid,'UserType'),
                  'EquipId':equipId,
                  'EquipType':equipType,
                  'StrengthenNum':1,
                  'StrengthenLevel':strengthData['StrengthenLevel'],
                  'CreateTime':createTime,
                  'NeedTime':needTime,
                  'StopTime':stopTime,
                  'BuildingId':buildingId,
                  }
        self.db.update(equipTable,strengthData,'EquipId=%s'%equipId)#更新武器信息
        self.changeStrengthNum(-1,buildingId)#减少一次强化次数
        self.db.insert('tb_log_equip_strengthen',record)#插入强化记录

    
    def changeStrengthNum(self,num,buildingId=None):
        '''
        :增加（减少）强化次数
        @param num:
        '''
        pTb = 'tb_process_equip'
        if buildingId is None:
            building = self.getSmithyInfo()
            if not building:
                return -1
            buildingId = building.get('BuildingId')
            
        record  = self.db.out_fields(pTb,['*'],'UserId=%s'%self.uid)
        now = int(time.time())
        if not record:
            record = {'UserId':self.uid,'BuildingId':buildingId,'ExtraNum':0,
                      'LastStartTime':0,'LastEndTime':0,'LastChangeTime':now}
            pid = self.db.insert(pTb,record)
            record['ProcessId'] = pid
        
        result = 0
        
        pid = record.get('ProcessId')
        lastEndTime = record.get('LastEndTime')
        extraNum = record.get('ExtraNum')
        needTime = Gcore.loadCfg(Gcore.defined.CFG_EQUIP)['StrengthenCD']
        
        if num>=1:#增加强化次数
            updateData = {}
            if lastEndTime>now:
                maxAddNum = math.ceil((lastEndTime-now)/float(needTime))
                if num>maxAddNum:
                    updateData = {'LastEndTime':now,'ExtraNum':num-maxAddNum,'LastChangeTime':now}
                else:
                    newEndTime = max(lastEndTime-needTime*num,now)
                    updateData = {'LastEndTime':newEndTime,'LastChangeTime':now}
            else:
                updateData = {'ExtraNum':extraNum+num,'LastChangeTime':now}
            result = self.db.update(pTb,updateData,'ProcessId=%s'%pid)
               
        elif num<=-1:#减少强化次数
            cutNum = abs(num)
            updateData = {}
            if extraNum:#先减超出的
                if extraNum>=cutNum:
                    updateData['ExtraNum'] = extraNum-cutNum
                    cutNum=0
                else:
                    updateData['ExtraNum'] = 0
                    cutNum = cutNum-extraNum
                    
            if cutNum:#再扣时间
                if lastEndTime<now:
                    updateData['LastStartTime'] = now
                    updateData['LastEndTime'] = now+cutNum*needTime
                    updateData['LastChangeTime'] = now
                else:
                    updateData['LastEndTime'] = lastEndTime+cutNum*needTime
                    updateData['LastChangeTime'] = now
                    
            if self.db.update(pTb,updateData,'ProcessId=%s'%pid):
                result = abs(num)
                
        return result
    
    def getMaxStrength(self,buildingId):
        '''获取最大可用强化次数'''
        now = int(time.time())
        #次数上限
        buildingMod = Gcore.getMod('Building',self.uid)
        bi = buildingMod.getBuildingById(buildingId,['BuildingType','BuildingId'])
        m = Gcore.getCfg('tb_cfg_building_up',(bi['BuildingType'],bi['BuildingRealLevel']),field='MakeValue')
        
        #可用次数
        useable = m
        pTb='tb_process_equip'
        record  = self.db.out_fields(pTb,['*'],'UserId=%s'%(self.uid))
        lastEndTime = record.get('LastEndTime')
        extraNum = record.get('ExtraNum',0)
        if lastEndTime>now:
            needTime = Gcore.loadCfg(Gcore.defined.CFG_EQUIP)['StrengthenCD']
            u = math.ceil((lastEndTime-now)/float(needTime))
            useable = (m-u)
        useable = useable+extraNum
        return {'Available':int(useable),'MaxNum':m}
     
    
    def updateEquipsStatus(self):
        '''更新装备状态'''
        now = int(time.time())

        ids = self.db.out_rows('tb_equip_sale',['SaleId','GoodsType','GoodsId'],'UserId=%s AND Status=1 AND DeadLine<%s'%(self.uid,now))
        if not ids:
            return
        for i in ids:
            goodsType = i['GoodsType']
            if goodsType in (1,4,5):#更新装备表
                equipTable = self.getEquipTB(goodsType)
                self.db.update(equipTable,{'EquipStatus':4},'EquipId=%s'%i['GoodsId']) 
            self.db.update('tb_equip_sale',{'Status':3},'SaleId=%s'%i['SaleId'])#更新出售表       
        
    def buyMyGoods(self,sId,goodsType,goodsId,goodsNum):
        '''回购出售的物品'''
        equipTable = self.getEquipTB(goodsType)
        buyBackTime = time.time()
        bagMod = Gcore.getMod('Bag',self.uid)
        if goodsType in (1,4,5):
            self.db.update(equipTable,{'EquipStatus':1},'EquipId=%s'%goodsId)#将回购装备设置为空闲
            bagMod.moveEquip(add=goodsId,goodsType=goodsType)
        else:
            bagMod.addGoods(goodsType,goodsId,goodsNum)
        self.db.update('tb_equip_sale',{'Status':2,'BuyBackTime':buyBackTime},'SaleId=%s'%sId)
        
    def saleGoods(self,goodsType,goodsId,goodsNum):
        '''出售物品'''
        equipTable = self.getEquipTB(goodsType)
        buyLimit = Gcore.loadCfg(CFG_EQUIP)['BuyBackLimit']#读取回购限制时间
        saleTime = time.time()
        deadline = saleTime+int(buyLimit)
        record = {'UserId':self.uid,
                  'GoodsType':goodsType,
                  'GoodsId':goodsId,
                  'GoodsNum':goodsNum,
                  'SaleTime':saleTime,
                  'Deadline':deadline,
                      }
        if goodsType in (1,4,5):#更新装备状态
            self.db.update(equipTable,{'EquipStatus':3},'EquipId=%s'%goodsId)#将回购装备设置为出售
        self.db.insert('tb_equip_sale',record)#插入出售记录

        
    def getSaleGoods(self):
        '''
                            查询在商店中可回购的物品
        '''
        equipTable = self.tb_equip()
        self.updateEquipsStatus()#先更新装备状态
        #装备
        equipFields = ['EquipId','EquipType','StrengthenLevel','EnhanceForce','EnhanceWit',
                       'EnhanceSpeed','EnhanceLeader']
        equips = self.db.out_rows(equipTable, equipFields,'UserId=%s AND EquipStatus=3'%self.uid)
        for equip in equips:
            equip['Price'] = self.calSalePrice(1,equip['EquipType'], equip.get('StrengthenLevel'))
        #兵书
        warBooks = self.getEquipByIds(4,fields=['EquipId','EquipType','StrengthenLevel'], state=[3])
        #宝物
        treasures = self.getEquipByIds(5,fields=['EquipId','EquipType','StrengthenLevel'], state=[3])
        #查询可回购物品列表
        itemFields = ['SaleId','GoodsType','GoodsId','GoodsNum']
        items = self.db.out_rows('tb_equip_sale',itemFields,'UserId=%s AND Status=1 ORDER BY SaleTime'%self.uid)
      
        return {'Equip':equips,'WarBook':warBooks,'Treasure':treasures,'Sale':items}
    
    def calSalePrice(self,goodsType,equipType,strengthLevel):   
        '''
        :计算出售价格
        @param goodsType:装备类别1装备4兵书5宝物
        @param equipType:装备类型
        @param strengthCost:强化累积
        '''
        cost = 0
        equipCfgTB = self.getCfgEquipTB(goodsType)
        equipCfg = Gcore.getCfg(equipCfgTB,equipType)
        basePrice = equipCfg.get('Price')
        if goodsType==1:
            eq = equipCfg.get('Quality')
            ep = equipCfg.get('EquipPart')
            
            equipUpCfg = Gcore.getCfg('tb_cfg_equip_up')
            strengthCost = sum([equipUpCfg[k]['CostQuality%s'%eq] for k in equipUpCfg if k[0]<= strengthLevel and k[1]==ep])
            SRatio = Gcore.loadCfg(Gcore.defined.CFG_EQUIP).get('StrengthenRatio')
            cost = basePrice+strengthCost*SRatio#出售价格
        else:
            cost = basePrice
        return cost
    
        
    def getEquipInfo(self,goodsType,equipId,fields=['*']):
        '''获取单件装备所有信息（原始表信息）'''
        equipTable = self.getEquipTB(goodsType)
        return self.db.out_fields(equipTable,fields,'EquipId=%s AND UserId=%s'%(equipId,self.uid))
    
    def updateEquipInfo(self,goodsType,data,where):
        ''' 更新装备信息'''
        return self.db.update(self.getEquipTB(goodsType),data,where)
    
    def getSaleInfo(self,sId,field=['*']):
        '''获取物品出售信息'''
        return self.db.out_fields('tb_equip_sale',field,'SaleId=%s'%sId)

# #------------------------------------------------------------------------------ 
#兵书宝物
    def getEquipByIds(self,goodsType,equipIds=None,fields=['*'],state=None):
        '''
        :查询装备信息，兵书宝物包含强化属性
        @param goodsType:
        @param equipIds:默认全部
        @param fields:
        @param state:1:空闲 2:已装备 3:已出售 4:已回收
        '''
        
        if not isinstance(fields, (list, tuple)):
            fields = [fields]

        if goodsType==1:
            equipTable = self.getEquipTB(1)+' e'
            where = 'e.UserId=%s '%self.uid
            
        elif goodsType==4:#兵书
            equipTable = 'tb_equip_warbook e,tb_cfg_equip_warbook c'
            fields = ['e.'+f for f in fields]
            for cf in ['Life','Attack','Defense']:
                fields.append('ROUND(c.Base%s+e.StrengthenLevel*c.Grow%s,2) as Enhance%s'%(cf,cf,cf))
            where = 'e.UserId=%s AND e.EquipType=c.WarBookType '%self.uid
            
        elif goodsType==5:#宝物
            equipTable = 'tb_equip_treasure e,tb_cfg_equip_treasure c'
            fields = ['e.'+f for f in fields]
            for cf in ['Force','Wit','Leader','Speed']:
                fields.append('ROUND(c.Base%s+e.StrengthenLevel*c.Grow%s,2) as Enhance%s'%(cf,cf,cf))
            where = 'e.UserId=%s AND e.EquipType=c.TreasureType '%self.uid
            
        else:
            return 0
        
        #装备状态
        if state and isinstance(state, (list,tuple)):
            where = where + 'AND e.EquipStatus IN ('+','.join(map(str,state))+')'
        elif state:
            where = where + 'AND e.EquipStatus=%s'%state

        if equipIds and isinstance(equipIds, (list,tuple)):
            ids = '('+','.join(map(str,equipIds))+')'
            where = where + ' AND e.EquipId IN %s'%ids
            return  self.db.out_rows(equipTable,fields,where)
        elif equipIds:
            where = where + ' AND e.EquipId=%s'%equipIds
            return self.db.out_fields(equipTable,fields,where)
        else:
            return  self.db.out_rows(equipTable,fields,where)
        
        
    def highEquipStengthen(self,goodsType,equipId,getExp):
        '''兵书，宝物强化'''
        equipInfo = self.db.out_fields(self.getEquipTB(goodsType),['*'],'EquipId=%s'%equipId)
        currentExp = equipInfo.get('CurrentExp')
        strengthenLevel = equipInfo.get('StrengthenLevel')
        equipType = equipInfo.get('EquipType')
        equipCfg = Gcore.getCfg(self.getCfgEquipTB(goodsType),equipType)
        quality = equipCfg['Quality']
        equipUpCfg = Gcore.getCfg(self.getCfgEquipTB(goodsType)+'_up')
        
        nextLevel = strengthenLevel+1
        currentExp = currentExp+getExp
        levelUpNeedExp = equipUpCfg.get(nextLevel,{}).get('Need%s'%quality)
        maxLevel = max(equipUpCfg.keys())

        while currentExp>=levelUpNeedExp and levelUpNeedExp is not None:
            currentExp = currentExp-levelUpNeedExp
            nextLevel += 1
            levelUpNeedExp = equipUpCfg.get(nextLevel,{}).get('Need%s'%quality)
        
        if nextLevel-1==maxLevel:
            currentExp = equipUpCfg.get(maxLevel,{}).get('Need%s'%quality)
        
        flag = self.db.update(self.getEquipTB(goodsType),{'StrengthenLevel':nextLevel-1,'CurrentExp':currentExp},'EquipId=%s'%equipId)
        if flag:
            return (nextLevel-1,currentExp)
        else:
            return (strengthenLevel,currentExp)
        
        
    def test(self,equipId):
        '''测试用'''
        return self.db.out_field('tb_equip','UserId','EquipId=%s'%equipId)
    
def _test():
    """注释"""
    uid = 44493
    e = EquipMod(uid)
#    print e.validEquipOnGeneral(3,11)
#    print e.getStrengthenInfo(4)
#    print e.getStrengthenCost(10, 2)
#     e.updateEquipsStatus()
    
#    e.equipStrengthen(41, 4)
#     print e.getMaxStrength(9275)
#    print e.getEquipsByGeneral(4)
#     print e.getSmithyInfo()

#    print e.updateEquip({"UserId":2}, 'UserId=1003 AND EquipId=1')
    #print e.getEquipsByGeneral(2)
#     print e.getAllValidEquip()
#     print e.calSalePrice(1,11)
#     print e.getSaleGoods()
#    print e.addEquipLog(999,101,9)

#     print e.changeStrengthNum(5)

#     print e.getCfgEquipTB(5)

#     print e.highEquipStengthen(4,2,1350)
    print Gcore.printd(e.getEquipByIds(5))

#     print e.validEquipOnGeneral(18,18,4)



if __name__ == '__main__':
    _test()