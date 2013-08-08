# -*- coding:utf-8 -*-
# author:JJ
# date:2013-1-3
# 游戏外部接口,资源

from sgLib.core import Gcore, inspector

class Building_resourceUI(object):
    '''
    建筑功能接口。
    '''
    def __init__(self, uid):
        self.mod = Gcore.getMod('Building_resource', uid)
        self.buildingMod = Gcore.getMod('Building',uid)
        self.coinMod = Gcore.getMod('Coin', uid)
        self.uid = uid
        
    @inspector('15005',['BuildingId',])
    def CollectCoin(self, param = {}):
        '''磨坊2，铸币厂5：收集资源'''
        #By Zhanggh 2013-3-20
        optId = 15005
        BuildingId = param.get('BuildingId')
        CollectTimeStamp = param.get('ClientTime')
        StorageReq = param.get('StorageReq')
        
        #验证客户端与服务器的时差

        BuildingInfo = self.buildingMod.getBuildingById(BuildingId)
        if not BuildingInfo:
            return Gcore.error(optId, -15005901) #用户没有该建筑
        BuildingType = BuildingInfo['BuildingType']
        if BuildingType !=2 and BuildingType!=5:
            return Gcore.error(optId, -15005998) #建筑非军需所或铸币厂
        if BuildingInfo.get('BuildingState')==2:
            return Gcore.error(optId, -15005905)#建筑升级中
        
        #收集资源，返回收集资源后剩余的部分与误差
        returnInfo = self.mod.collectCoin(optId,BuildingType,BuildingId,CollectTimeStamp,StorageReq,param)
        if returnInfo==0:
            return Gcore.error(optId, -15005001) #没有可收集资源
        elif returnInfo==-1:
            return Gcore.error(optId, -15005002) #建筑修复中
        
        CoinType = 2 if BuildingType == 2 else 3
        CollectNum = returnInfo.pop('CNum')   
        recordData = {'uid':self.uid,'ValType':CoinType,'Val':CollectNum}#成就记录
            
        return Gcore.out(optId,returnInfo,achieve=recordData,mission=recordData)
        
    
    @inspector(15009,['BuildingId'])
    def GetStorage(self, param = {}):
        '''磨坊，铸币厂:获取存储量'''
        optId = 15009
        BuildingId = param['BuildingId']
        ClientTime = param['ClientTime']
                
        #验证客户端与服务器的时差

        BuildingInfo = self.buildingMod.getBuildingById(BuildingId)
        if not BuildingInfo:
            return Gcore.error(optId, -15009901) #用户没有该建筑
        BuildingType = BuildingInfo['BuildingType']
        if BuildingType == 2 or BuildingType == 5: #军需所或铸币厂
            BuildingStorage = self.mod.touchBuildingStorage(BuildingId,ClientTime).get('Storage')
            return Gcore.out(optId, {"BuildingStorage":BuildingStorage})
        return Gcore.error(optId, -15009998) #建筑非军需所或铸币厂



def _test():
    '''测试'''
    #磨坊军资2，铸币，铜钱5
    import time
    uid = 44448 #1013,1001
    c = Building_resourceUI(uid)
#    print Gcore.loadCfg(1501)['InitJcoin']
#    ct = time.time()
#     print c.GetStorage({"BuildingId":761})
    print c.CollectCoin({"BuildingId":20726})
#     print c.GetStorage({'BuildingId':41})
#    print ct

if __name__ == '__main__':
    _test()
    Gcore.runtime()
