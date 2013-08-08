# -*- coding:utf-8 -*-
# author:
# date:2013-1-
# 游戏外部接口  地图
import sys

from sgLib.core import Gcore,inspector

class MapUI(object):
    """测试 ModId:99 """
    def __init__(self, uid):
        '''注释'''
        self.uid = uid
        self.mod = Gcore.getMod('Map',uid)
        #print 'MapUI.__init__',uid
        self.mod_building = Gcore.getMod('Building',uid)
        
    def test(self,p={}):
        '''测试方法'''
        
    @inspector(14001)
    def getScene(self,p={}):
        '''获取场景'''
        optId = 14001
        BuyMapInfo = self.mod.getMyBuyMap() #已购买地皮，待优化
        BuildingInfo = self.mod_building.getAllBuildingCoord()
        
        modInteract=Gcore.getMod('Interact',self.uid)
        interactGids=modInteract.getHaveMcoinGeneralIds()#获取有交流记录的武将ID Add by Yew
        
        body = {'BuildingInfo':BuildingInfo,'BuyMapInfo':BuyMapInfo,'InteractGids':interactGids}
        
        return Gcore.out(optId,body) 
    
    @inspector(14002,['x','y'])
    def BuyMap(self,p={}):
        '''购买地图'''

        optId = 14002
        if 'x' not in p or 'y' not in p:
            return Gcore.error(optId,-14002001) #非法参数 
        
        x = p['x']
        y = p['y']
        if not self.mod.checkBuyStartCoord(x,y):
            print self.mod.db.sql
            return Gcore.error(optId,-14002002) #所传的坐标非可购买坐标的起点
            
        if self.mod.checkHadBuy(x,y):
            return Gcore.error(optId,-14002003) #你已经购买过此坐标
        
        MapBuyTimes = Gcore.getMod('Player',self.uid).getMapBuyTimes()
        CostValue = Gcore.getCfg('tb_cfg_map_cost',MapBuyTimes,'Cost')
        print CostValue
        #开始支付
        modCoin = Gcore.getMod('Coin',self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        pay = modCoin.PayCoin(optId, 3, CostValue, classMethod, p)
        achieve = {'uid':self.uid,'ValType':0,'Val':1}#成就记录
        if pay < 0:
            Gcore.error(optId, -14002995) #支付失败
        else:
            if not self.mod.doBuyMap(x,y):
                return Gcore.error(optId,-14002004) #购买失败
            else:
                return Gcore.out(optId,achieve=achieve)
            
def _test():
    uid = 1001
    c = MapUI(uid)
    c.getScene()
    #c.BuyMap({'x':14,'y':62})
    
if __name__ == '__main__':
    _test()
