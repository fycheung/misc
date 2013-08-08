# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-4-3
# 模块说明

import math
from sgLib.core import Gcore, inspector
import sgLib.common as com

class BagUI(object):
    '''背包系统'''
    def __init__(self,uid):
        self.mod = Gcore.getMod('Bag', uid)
        self.uid = uid
     

#     @inspector(13061,['PageNum','GoodsType'])
    def GetGoods(self,p={}):
        '''分类查看物品
        GoodsType:1：装备,2:道具,3,不分种类'''
        optId = 13061
        goodsType = p.get('GoodsType')
        bagSize = self.mod.getBagSize()#背包容量
        maxSize = Gcore.loadCfg(Gcore.defined.CFG_PLAYER_BAG).get('MaxNum')
        full = 1 if bagSize==maxSize else 0
        if goodsType in (1,2):
            goods = self.mod.getGoods(goodsType)#背包物品
        else:
            goods = self.mod.sortBag()#排序背包物品并返回有序的物品
        goods = com.list2dict(goods, offset=0)
        recordData = {'uid':self.uid,'ValType':0,'Val':1}#成就、任务记录
        
        #兵书，宝物
        equipMod = Gcore.getMod('Equip',self.uid)
        warbooks = equipMod.getEquipByIds(4)
        treasures = equipMod.getEquipByIds(5)
        
        return Gcore.out(optId,{'GS':goods,'Size':bagSize,'Full':full,'WBS':warbooks,'TRS':treasures},mission=recordData)
        
            
    @inspector(13062,['From','To'])
    def MoveGoods(self,p={}):
        '''调整物品'''
        optId = 13062
        pFrom = p['From']
        pTo = p['To']
        bagSize = self.mod.getBagSize()
        if not(0<pFrom<=bagSize) or not(0<pTo<=bagSize):
            return Gcore.error(optId, -13062001)#背包位置不合法
        
        if pFrom == pTo:#会删除道具
            return Gcore.out(optId,{})
        
        gFrom = self.mod.getFromPosition(pFrom)
        gTo = self.mod.getFromPosition(pTo)
        if not gFrom:
            return Gcore.error(optId,-13062002)#当前没有物品
        
        #改变物品位置
        if not gTo:#将物品移动到空格
#             print '移动到',pFrom,pTo
#             print 'F',gFrom
            self.mod.updateBag(gFrom['BagId'],{'Position':pTo})
            
        #相同道具叠加
        elif gFrom['GoodsType']==gTo['GoodsType']==2 and gFrom['GoodsId']==gTo['GoodsId']:
#             print '道具叠加',pFrom,pTo
#             print 'F',gFrom
#             print 'T',gTo
            
            gFromNum = gFrom['GoodsNum']
            gToNum = gTo['GoodsNum']
            gToMax = Gcore.getCfg('tb_cfg_item',gTo['GoodsId'],'OverlayNum')
            if gToNum<gToMax:
                gToNum = gToNum+gFromNum
                if gToNum>gToMax:
                    gFromNum = gToNum-gToMax
                    gToNum = gToMax
                else:
                    gFromNum = 0
                self.mod.updateBag(gTo['BagId'],{'GoodsNum':gToNum})
                self.mod.updateBag(gFrom['BagId'],{'GoodsNum':gFromNum})     
                 
        #两物品交换位置   
        else:
#             print '交换位置',pFrom,pTo
#             print 'F',gFrom
#             print 'T',gTo
            
            self.mod.updateBag(gFrom['BagId'],{'Position':pTo})
            self.mod.updateBag(gTo['BagId'],{'Position':pFrom})
        return Gcore.out(optId,{})
        

    def ExpandBag(self,p={}):
        '''扩展背包格仔数'''
        optId = 13063
        bagSize = self.mod.getBagSize()
        bagCfg = Gcore.loadCfg(Gcore.defined.CFG_PLAYER_BAG)
        maxSize = bagCfg.get('MaxNum')
        if bagSize >= maxSize:
            return Gcore.error(optId,-13063001)#背包数量已达最大
        expandCost = bagCfg.get('PerExpandCost')
        expandSize = bagCfg.get('PerExpandNum')
        #支付
        coinMod = Gcore.getMod('Coin',self.uid)
        payState = coinMod.PayCoin(optId,1,expandCost,'BagUI.ExpandBag')
        if payState>0:
            self.mod.expandBag(bagSize,expandSize)
            recordData = {'uid':self.uid,'ValType':0,'Val':1,'BagSize':bagSize+expandSize}#成就、任务记录
            full = 1 if (bagSize+expandSize)==maxSize else 0
            return Gcore.out(optId,{'Size':bagSize+expandSize,'Cost':payState,'Full':full},mission=recordData)
        elif payState == -2:
            return Gcore.error(optId,-13063994)#货币不足
        else:
            return Gcore.error(optId,-13063995)#支付失败

def _test():
    """注释"""
    uid = 44493
    
    b = BagUI(uid)
#    b.ExpandBag()
#     print b.MoveGoods({'From':14,'To':11})
#     print 'xxx1'
#     print b.MoveGoods({'From':14,'To':14})
#     print 'xxx2'
#     print b.MoveGoods({'From':14,'To':11})
#    print b.GetGoods({'GoodsType':1,'PageNum':1})
    print b.GetGoods()
#     Gcore.runtime()

if __name__ == '__main__':
    _test()