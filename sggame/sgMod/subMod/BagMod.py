# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-4-3
# 模块说明

import time
import math
import copy
from sgLib.core import Gcore
from sgLib.base import Base


class BagMod(Base):
    '''背包模型'''
    def __init__(self,uid):
        Base.__init__(self, uid)
        self.uid = uid
#------------------------------START模块内部接口-------------------------------
#Author:Modify by Zhanggh 2013-4-10
    
    #def addGoods(self,goodsType,goodsId,goodsNum=1,emailed=True,addLog=0):
    def addGoods(self, goodsType, goodsId, goodsNum=1, emailed=True, addLog=0):
        '''
        :往背包中添加物品
        @param goodsType:物品类型 1:装备，2：道具
        @param goodsId:物品类型ID EquipType & ItemId
        @param goodsNum:物品数量
        @param emailed:是否将剩余物品用邮件发给玩家
        @return: 
                []:成功添加返回数组，添加装备时数组存放装备ID，道具时存放添加数量
                 0:背包没空间
                -1:道具或装备类型不存在
        '''
        bagTable = self.tb_bag()
#         now = time.time()
        where = 'UserId=%s ORDER BY Position'%(self.uid)
        goods = self.db.out_rows(bagTable,['*'],where)
        maxNum = self.getBagSize()#查询背包容量
        avlBag = self._getAvlInBag(goods, maxNum)#查询可用的格仔
        avlNum = len(avlBag)
        leftNum = goodsNum#剩余数量
        bagData = []#插入背包表数据
        result = []
        
        #道具    
        if goodsType==2:
            toolCfg = Gcore.getCfg('tb_cfg_item',goodsId)
            
            if toolCfg is None:#道具类型不存在
                return -1
                     
            #可叠加道具
            overLayNum = toolCfg['OverlayNum']
            #往可叠加相同道具类型增加数量
            for good in goods:
                gNum = good['GoodsNum']
                if good['GoodsType']==goodsType and good['GoodsId']==goodsId and gNum<overLayNum:
                    addNum = leftNum if overLayNum>=(gNum+leftNum) else overLayNum-gNum
                    self.db.update(bagTable,{'GoodsNum':gNum+addNum},'BagId=%s'%good['BagId'])
                    leftNum-=addNum
                    if leftNum <=0:
                        break
                    
            #没有可叠加项，且背包中有可用格仔则在新位置添加物品
            while leftNum>0 and avlNum>0:
                addNum = leftNum if overLayNum>=leftNum else overLayNum
                data = {'UserId':self.uid,'Position':avlBag.pop(0),
                        'GoodsType':2,'GoodsId':goodsId,
                        'GoodsNum':addNum}
                bagData.append(data)
                leftNum-=addNum
                avlNum = len(avlBag)
            result.append(goodsNum-leftNum)
            
            #添加道具日志 
            if addLog>0:
                Gcore.getMod('Item',self.uid).insertItemLog(addLog,goodsId,goodsNum,1)
#                return {'GoodsType':goodsType,'GoodsNum':goodsNum-leftNum}
                    
        #1装备,4兵书,5宝物
        elif goodsType in (1,4,5):
            equipMod = Gcore.getMod('Equip',self.uid)
            #判断装备类型是否存在
            cfgTable = equipMod.getCfgEquipTB(goodsType)
            equipCfg = Gcore.getCfg(cfgTable,goodsId)
            if equipCfg is None:
                return -1
            
            #往背包添加物品不能大于可用格仔
            while leftNum>0 and avlNum>0:
                    equipid = equipMod.initEquip(goodsType,goodsId)
                    data = {'UserId':self.uid,'Position':avlBag.pop(0),
                            'GoodsType':goodsType,'GoodsId':equipid}
                    bagData.append(data)
                    result.append(equipid)
                    leftNum-=1
                    avlNum = len(avlBag)
                    
            #添加装备日志 
            if addLog>0:
                equipMod.addEquipLog(addLog,goodsType,goodsId,goodsNum)
#            return {'GoodsType':goodsType,'GoodsNum':insertNum}

        
        #插入背包表
        if bagData:    
            self.db.insertmany(bagTable,bagData)
                
        #判断是否发邮件
        if emailed==True and leftNum>0:
            mailMod=Gcore.getMod('Mail',self.uid)
            goods=[{'GoodsType':goodsType,'GoodsId':goodsId,'GoodsNum':leftNum}]
            #mailMod.sendAttachment(self.uid,goods,'你的背包已经满','你的背包已经满')
            mailMod.sendSystemMail(self.uid, goods, addLog)
            
        
        if (goodsNum-leftNum)==0:
            return 0
        return result
    
    def addManyGoods(self,goods, emailed=True, addLog=0):
        result = {'EquipIds':[],'WarBookIds':[],'TreasureIds':[]}
        equipType = {1:'EquipIds',4:'WarBookIds',5:'TreasureIds'}
        leftGoods = []
        for g in goods:
            goodsType = g['GoodsType']
            goodsId = g['GoodsId']
            goodsNum = g['GoodsNum']
            leftNum = 0
            ids = self.addGoods(goodsType, goodsId, goodsNum, emailed=False, addLog=addLog)
            if isinstance(ids,(list,tuple)) and goodsType in (1,4,5):
                result[equipType[goodsType]].extend(ids)
                leftNum = goodsNum-len(ids)
            elif isinstance(ids,(list,tuple)) and goodsType==2:
                leftNum = goodsNum-ids[0]
            elif ids==0:
                leftNum = goodsNum
                    
            if leftNum>0 :
                leftGoods.append({'GoodsType':goodsType,'GoodsId':goodsId,'GoodsNum':leftNum})
        
        if emailed and leftGoods:
            Gcore.getMod('Mail',self.uid).sendSystemMail(self.uid, leftGoods, addLog)
        return result
                
            
            
    
    def moveEquip(self,add=None,remove=None,goodsType=1):
        '''
        :更新背包装备位置
        @param add:添加的装备ID
        @param remove:移除装备ID
        @param goodsType:装备类型 1装备4兵书 5宝物 
        @return: 0：失败，1：成功
        '''
        bagTable = self.tb_bag()
        #从背包移除装备
        if not add and remove:
            return self.db.delete(bagTable,'UserId=%s AND GoodsType=%s AND GoodsId=%s'%(self.uid,goodsType,remove))
        #往背包添加  装备
        elif add and not remove:
            #now = time.time()
            where = 'UserId=%s ORDER BY Position'%(self.uid)
            goods = self.db.out_rows(bagTable,['*'],where)
            maxNum = self.getBagSize()#查询背包容量
            avlBag = self._getAvlInBag(goods, maxNum)#查询可用的格仔
            if len(avlBag)>0:
                data = {'UserId':self.uid,'Position':avlBag.pop(0),
                        'GoodsType':goodsType,'GoodsId':add}
                self.db.insert(bagTable,data)
                return 1
            else:
                return 0
        #把添加的物品添加到移除物品的位置
        elif add and remove:
            return self.db.update(bagTable,{'GoodsId':add},'UserId=%s AND GoodsType=%s AND GoodsId=%s'%(self.uid,goodsType,remove))
    

    def useItems(self,itemType,itemNum=1,p=None):
        '''
        :使用道具
        @param itemType:道具类型
        @param itemNum:道具数量
        @param p:道具位置
        @return: 1:成功使用 -1：道具数量不足 -2:该位置没有道具
        '''
        bagTable = self.tb_bag()
        now = time.time()
        
        #使用某个位置的道具
        if p:
            item = self.getFromPosition(p,['BagId','GoodsNum'])
            if not item:
                return -2
            bagId = item.get('BagId')
            hasNum = item.get('GoodsNum',0)
            if hasNum>itemNum:
                self.db.update(bagTable,{'GoodsNum':hasNum-itemNum},'BagId=%s'%bagId)
                return 1
            elif hasNum<itemNum:
                return -1
            elif hasNum==itemNum:
                self.db.delete(bagTable,'BagId=%s'%bagId)
                return 1
        
        #不按位置使用道具
        else:
            where = 'UserId=%s AND GoodsType=2 AND GoodsId=%s ORDER BY Position'%(self.uid,itemType)
            items = self.db.out_rows(bagTable,['*'],where)
            #判断是否有足够数量
            itemsNum = sum([i.get('GoodsNum',0)for i in items])
            if itemsNum < itemNum:
                return -1#数量不足
            
            #使用已有 道具，当背包中一个位置的道具数量为0，删除记录
            for item in items:
                if itemNum>0:#itemNum为需要使用的数量，当数量用够itemNum为0
                    hasNum = item.get('GoodsNum',0)
                    bagId = item.get('BagId')
                    if hasNum>itemNum:
                        self.db.update(bagTable,{'GoodsNum':hasNum-itemNum},'BagId=%s'%bagId)
                        itemNum = 0 
                    elif hasNum<=itemNum:
                        itemNum = 0 if hasNum==itemNum else itemNum-hasNum
                        self.db.delete(bagTable,'BagId=%s'%bagId)
                else:
                    break
            return 1
    
    def countGoodsNum(self, goodsIds):
        '''获取道具的数量'''
        # author:zhoujingjiang
        # goodsIds - 道具ID 或 道具ID的序列
        # 返回值：如果goodIds是单个道具，返回该道具的数量；否则返回字典。
        item_ids = Gcore.getCfg('tb_cfg_item').keys()

        is_single = False
        if isinstance(goodsIds, (int, long, basestring)):
            is_single = int(goodsIds)
            goodsIds = [goodsIds]

        for goodsId in iter(goodsIds):
            if int(goodsId) not in item_ids:
                raise TypeError('%s is not an item' % goodsId)

        table = self.tb_bag()
        where = 'UserId=%s AND (GoodsId= ' % self.uid
        where += ' OR GoodsId= '.join(map(str, iter(goodsIds))) + ' ) '  
        fields = ['GoodsNum', 'GoodsId']
        items = self.db.out_rows(table, fields, where)
        
        combined = {}
        for item in items:
            combined[item['GoodsId']] = combined.get(item['GoodsId'], 0) \
                        + item['GoodsNum']
        for goodsId in iter(goodsIds):
            combined.setdefault(int(goodsId), 0)

        return combined if not is_single else combined[is_single]
    
    def deleteEquips(self,goodsType,goodsIds):
        '''
        :从背包删除装备，同时删除装备表中物品
        @param goodsType:装备类型，1普通装备，4兵书，5宝物
        @param goodsIds:一个或多个装备ID
        '''
        if goodsIds and isinstance(goodsIds,(list,tuple)):
            ids = '('+','.join(map(str,goodsIds))+')'
        elif goodsIds:
            ids = '(%s)'%goodsIds
        else:
            return
        
        equipMod = Gcore.getMod('Equip',self.uid)
        bagTB = self.tb_bag()
        equipTB = equipMod.getEquipTB(goodsType)
        bagSql = 'DELETE FROM %s WHERE UserId=%s AND GoodsType=%s AND GoodsId IN %s'%(bagTB,self.uid,goodsType,ids)
        equipSql = 'DELETE FROM %s WHERE UserId=%s AND EquipId IN %s'%(equipTB,self.uid,ids)
        self.db.execute(bagSql)
        self.db.execute(equipSql)
    
#-------------------------------END模块内部接口--------------------------------
   
    def inclueOrNot(self,goodsType,goodsId,goodsNum=1):
        '''
        :判断背包是否有足够空间存放物品
        @param goodsType:物品类型 1.装备，2道具 4兵书5宝物
        @param goodsId:装备道具类型
        @param goodsNum:存放数量
        '''
        bagTable = self.tb_bag()
        maxNum = self.getBagSize()#查询背包容量
        goods = self.db.out_rows(bagTable,['*'],'UserId=%s'%self.uid)
        avlBag = self._getAvlInBag(goods, maxNum)#查询可用的格仔
        if goodsType in (1,4,5):
            avlNum = len(avlBag)
            
        elif goodsType==2:#物品类型是否为道具
            overlayNum=Gcore.getCfg('tb_cfg_item',goodsId,'OverlayNum')#该类道具最大容量
            avlNum = len(avlBag)*overlayNum
            for good in goods:
                if good['GoodsType']==2 and good['GoodsId']==goodsId:
                    avlNum+=(overlayNum-good['GoodsNum'])
                
        if avlNum>=goodsNum:
            return True
        else:
            return False   
        
    
    def canAddInBag(self, goodsList):
        '''判断物品列表是否能够全部添加到当前玩家的背包@qiudx
           @goodsList: [{'GoodsType':xxx, 'GoodsId': xxx, 'GoodsNum': xxx},]
           @返回True or False
        ''' 
        needNum = 0 #统计添加物品列表所需的格子数
        tmpGoodsList = copy.deepcopy(goodsList)
        goods = self.db.out_rows(self.tb_bag(), ['*'], 'UserId=%s'%self.uid)
        for tmpGoods in tmpGoodsList:
            if tmpGoods['GoodsType'] in (1, 4, 5):  #装备，兵书，宝物一个格子只能放一件
                equipMod = Gcore.getMod('Equip', self.uid)
                cfgTable = equipMod.getCfgEquipTB(tmpGoods['GoodsType'])
                equipCfg = Gcore.getCfg(cfgTable, tmpGoods['GoodsId'])
                if not equipCfg:
                    continue
                needNum += tmpGoods['GoodsNum']
            elif tmpGoods['GoodsType'] == 2:        #道具可能一个格子放多个
                itemCfg = Gcore.getCfg('tb_cfg_item', tmpGoods['GoodsId'])
                if not itemCfg:
                    continue
                avlNum = int(itemCfg.get('OverlayNum', 1))
                for good in goods:
                    if good['GoodsType'] == 2 and good['GoodsId'] == tmpGoods['GoodsId']:
                        tmpGoods['GoodsNum'] -= avlNum - good['GoodsNum']
                        if tmpGoods['GoodsNum'] <= 0:
                            break
                needNum += int(math.ceil(float(tmpGoods['GoodsNum']) / avlNum))
        
        maxNum = self.getBagSize()#查询背包容量
        avlBag = self._getAvlInBag(goods, maxNum)#查询可用的格仔
        if len(avlBag) >= needNum:
            return True
        return False
        
            
    def _getAvlInBag(self,goods,maxNum):
        '''
        :获取背包中可用的格仔
        @param goods:背包中存在的物品
        @param maxNum:背包格数
        @return: list 升序排列的可用格仔编号
        '''
        nums = range(1,maxNum+1)
        for g in goods:
            p = g.get('Position')
            if p in nums:
                nums.remove(p)
        nums.sort()
        return nums
    
    
    def getGoodsNum(self,goodsType):
        '''
        :查询物品数量
        @param goodsType:
        '''
        bagTable = self.tb_bag()
        return self.db.out_field(bagTable,'Count(1)','UserId=%s AND GoodsType=%s'%(self.uid,goodsType))
    
    
    def getGoods(self,goodsType):
        '''查询背包中的物品
        @param goodsType:0:所有1:装备，2：道具,
        @todo: 包含装备信息'''
        bagTable = self.tb_bag()
        fields = ['BagId','UserId','Position','GoodsType','GoodsId','GoodsNum']
        if goodsType==0:
            where = 'UserId=%s ORDER BY Position'%(self.uid)
        else:
            where = 'UserId=%s AND GoodsType=%s ORDER BY Position '%(self.uid,goodsType)
        goods = self.db.out_rows(bagTable,fields,where)
        return goods
        
    def getBagSize(self):
        ''':查询背包容量'''
        maxSize = self.db.out_field('tb_bag_expand','MAX(ExpandNum)','UserId=%s'%self.uid)
        if maxSize is None:
            maxSize = Gcore.loadCfg(Gcore.defined.CFG_PLAYER_BAG).get('InitNum')#初始格仔数
        return maxSize
    
    def getFromPosition(self,p,fields='*'):
        '''
        :根据位置查询背包中的物品
        @param p:物品位置
        '''
        table = self.tb_bag()
        where = 'UserId=%s AND Position=%s'%(self.uid,p)
        return self.db.out_fields(table,fields,where)
    
    def updateBag(self,bagId,data):
        '''
        :更新背包物品信息
        @param bagId:物品原背包ID
        @param p:目标位置
        '''
        table = self.tb_bag()
        if data.get('GoodsNum')==0:#当物品数量为0时候删除物品
#             print '删除背包',bagId
            return self.db.delete(table,'BagId=%s'%bagId)
        return self.db.update(table,data,'BagId=%s'%bagId)
    
    def expandBag(self,curSize,expSize):
        '''
        :扩展背包
        @param curSize:当前格仔数
        @param expSize:扩展格仔数
        '''
        data = {'UserId':self.uid,'CurrentNum':curSize,
                'ExpandNum':curSize+expSize,'CreateTime':time.time()}
        return  self.db.insert('tb_bag_expand',data)
    
    def sortBag(self):
        '''排序背包物品并返回有序的物品'''
        bagTable = self.tb_bag()
        fields = ['BagId','UserId','Position','GoodsType','GoodsId','GoodsNum']
        where = 'UserId=%s ORDER BY Position'%(self.uid)
        goods = self.db.out_rows(bagTable,fields,where)
        p = 1
        for good in goods:
            gp = good['Position']
            bagId = good['BagId']
#             print 'CurP is ',good['Position'],'NewP is',p
            if p!=gp:
                if self.db.update(bagTable,{'Position':p},'BagId=%s'%bagId):
#                     print 'Position Update at=',bagId 
                    good['Position'] = p  
            p+=1            
        return goods
            
    def test(self):
        '''测试'''
#         return self.db.execute("insert into tb_battle_record values(22,1013, 1001, 1, 1, 1, 'lzsb', 0, 0, 0, 0, 121)")
#        return self.db.out_field('tb_bag_expand','MAX(ExpandNum)','UserId=%s'%self.uid)
        ids = [1403, 1402, 1400, 1401, 1399, 
               1404, 1405, 1406, 1407, 1408, 
               1409, 1414, 1413, 1412]
        
        nids = [i['BagId'] for i in self.db.out_rows(self.tb_bag(),['*'],'UserId=%s'%self.uid)]
        print 'xxx',nids
        for i in ids:
            if i not in nids:
                print i
                

        


def _test():
    """注释"""
    uid = 44493
    b = BagMod(uid)
     
#     print b.countGoodsNum('1101')
#    print Gcore.loadCfg(Gcore.defined.CFG_PLAYER_BAG)
#    print b.test()
#     print b.addGoods(5,9,1,addLog=123)    
#    print b.getFromPosition(13)
#    print b.getBagSize()
#    print b.useItems(103,6)
#    print Gcore.objCfg.loadAllCfg()
#     print b.test()
#    print b.moveEquip(add=8)
#    print b.inclueOrNot(1,1,1)
#     print b.sortBag()
#     print b.deleteEquips(4,2)

    print b.addManyGoods([{'GoodsType':4,'GoodsId':2,'GoodsNum':3},
                          {'GoodsType':5,'GoodsId':3,'GoodsNum':3},
                          {'GoodsType':4,'GoodsId':1,'GoodsNum':3},
                          {'GoodsType':5,'GoodsId':10,'GoodsNum':3},])


if __name__ == '__main__':
    _test()
    