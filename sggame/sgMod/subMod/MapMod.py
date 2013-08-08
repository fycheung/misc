# -*- coding:utf-8 -*-
# author:
# date:2013-1-
# 游戏内部接口,模型模板

from sgLib.core import Gcore
from sgLib.base import Base

Coord = Gcore.Coord
class MapMod(Base):
    """地图模型"""
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
        
    def cacUsedCoords(self, AllBuildings):
        '''计算被建筑占用的坐标'''
        UsedCoords = [Coord.ExpandCoord(Building['x'], Building['y'], Building['xSize']) 
                      for Building in AllBuildings
                      if Building['xSize'] != 0]
        return reduce(lambda init, subList:init + subList, UsedCoords, [])
    
    def getAllUsefulCoords(self):
        '''获取所有可用坐标'''
        TotalCoords = Gcore.getCfg('tb_cfg_map_valid')
        return [k for k, v in TotalCoords.iteritems() if not v['used']]
    
    def getCoords(self, x, y, size):
        '''获取以(x, y)为起点大小为size的区域的坐标列表'''
        return Coord.ExpandCoord(x, y, size)      
        
    def checkCoord(self, x, y, size):
        '''检查坐标是否可用'''
        modBuilding = Gcore.getMod('Building', self.uid)
        Buildings = modBuilding.getBuildingById()
        #return Buildings
        UsedCoords = [Coord.ExpandCoord(Building['x'], Building['y'], Building['xSize']) for Building in Buildings]
        UsedCoords = reduce(lambda init, subList:init + subList, UsedCoords, []) 
        
        TotalCoords = Gcore.getCfg('tb_cfg_map_valid')
        CanUseCoords = filter(lambda dic : dic.get('used', 1) == 0, TotalCoords.values())
        CanUseCoords = [(coord['x'], coord['y']) for coord in CanUseCoords]

        if (x,y) in UsedCoords or (x,y) not in CanUseCoords:
            return False
        return True
        
    def checkBuyStartCoord(self,x,y):
        '''检查是否可购买地图的第一个坐标'''
        where = "used=2 AND x='%s' AND y='%s'"%(x,y)
        count = self.db.out_field('tb_cfg_map_valid', 'COUNT(*)', where)
        return bool(count)
    
    def checkHadBuy(self,x,y):
        '''检查是否已经购买过'''
        where = "UserId='%s' AND x1='%s' AND y1='%s'"%(self.uid,x,y)
        count = self.db.out_field('tb_map_buy', 'COUNT(*)', where)
        return bool(count)
    
    def doBuyMap(self,x,y):
        '''执行购买地皮'''
        (x1,y1),(x2,y2),(x3,y3),(x4,y4) = Coord.ExpandCoord(x,y,Gcore.defined.CFG_BUYMAP_SIZE)
        data = {}
        data['UserId']=self.uid
        data['x1']=x1
        data['x2']=x2
        data['x3']=x3
        data['x4']=x4
        data['y1']=y1
        data['y2']=y2
        data['y3']=y3
        data['y4']=y4
        result = self.db.insert('tb_map_buy', data)
        if result:
            self.db.execute("UPDATE tb_user SET BuyMapTimes=BuyMapTimes+1 WHERE UserId=%s"%self.uid)
        return result
    
    def getMyBuyMap(self):
        return ()
        '''sql = "SELECT x1 AS x,y1 AS y FROM tb_map_buy WHERE UserId='%s'"%self.uid
        data = self.db.fetchall(sql)
        return data'''
    
if __name__ == '__main__':
    uid = 1005
    c = MapMod(uid)
    #print c.getCoords(1,2,3)
    print (32L, 54L) in c.getAllUsefulCoords()
    print len(c.getAllUsefulCoords())
    