# -*- coding: utf-8 -*-
# author: qiudx
# date : 2013/07/15
# 给真网上没有防御工事的添加防御工事

from sgLib.core import Gcore
from sgLib.defined import CFG_BUILDING

class ReGiverDefense(object):
    
    def __init__(self):
        self.db = Gcore.getDB()
        self.needReGiveIds = []
        
        
    def checkNoDefense(self):
        '''查询无任何布防的角色ID'''
        UserIdList = self.db.out_list('tb_user', 'UserId')
        for userId in UserIdList:
            wallMod = Gcore.getMod('Wall', userId)
            if not wallMod.getDefenseGeneral():
                if not wallMod.getDefenseNum():
                    self.needReGiveIds.append(userId)
        print self.needReGiveIds
    
    def reGive(self):
        '''重新赠送布防'''
        buildCfg = Gcore.loadCfg(CFG_BUILDING)
        for userId in self.needReGiveIds:
            print '===',userId
            wallMod = Gcore.getMod('Wall', userId)
            generalMod = Gcore.getMod('General', userId)
            myGenerals = generalMod.getMyGenerals()
            if not myGenerals:
                print 'Plsyer:%s has no generals'%userId
            else:
                generalId = myGenerals[0]['GeneralId']
                #布防武将
                generalPosition = buildCfg['InitGeneralDefense']
                generalDefenseData = {'GeneralId': generalId, 'x': generalPosition['x'], 'y': generalPosition['y'], 'UserId': userId}
                self.db.insert('tb_wall_general', generalDefenseData)
            #初始防御工事
            initDefense = buildCfg['InitDefense']
            for defense in initDefense:
                size = Gcore.getCfg('tb_cfg_soldier', defense['SoldierType'], 'Size')
                xSize, ySize = size.split('*')
                ySize, xSize  = int(xSize), int(ySize) #横放
                defenseCfg = Gcore.getCfg('tb_cfg_soldier_up', (defense['SoldierType'], 1))
                cost = defenseCfg.get('MakeCost')
                defenseData = {'SoldierType': defense['SoldierType'],
                        'SoldierLevel': 1,
                        'MakeCost': cost,
                        'UserId': userId,
                        'x': defense['x'],
                        'y': defense['y'],
                        'xSize': xSize,
                        'ySize': ySize,
                        }
                defenseTable = wallMod.tb_wall_defense()
                self.db.insert(defenseTable, defenseData)
            
            Gcore.getMod('Redis', userId).offCacheWallDefense() #缓存布防工事
            Gcore.getMod('Redis', userId).offCacheGeneral()     #缓存布防武将
            
    def run(self):
        self.checkNoDefense()
        if not self.needReGiveIds:
            print 'No user need regive defense!'
            return
        self.reGive()
        
def test():
    reg = ReGiverDefense()
    reg.run()



if '__main__'==__name__:
    test()
    
