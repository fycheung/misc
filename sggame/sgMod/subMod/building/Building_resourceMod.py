# -*- coding:utf-8 -*-
# author:Lizr
# date:2013-1-3
# 游戏内部接口:建筑

from __future__ import division
import time
import math
from sgLib.core import Gcore
from sgLib.base import Base

class Building_resourceMod(Base):
    '''资源模型'''
    
    def __init__(self, uid):
        '''构造函数'''
        self.uid = uid
        Base.__init__(self,uid)
        self.buildingMod = Gcore.getMod('Building', uid)
    
    def touchBuildingStorage(self, BuildingId,TimeStamp=None):
        '''
                    创建或更新建筑的存储信息
        @param BuildingId:建筑ID
        @param TimeStamp:收集时间
        @return:
                Storage当前储量
                MaxSave最大储量
        '''
        TimeStamp = time.time() if TimeStamp is None else int(TimeStamp)
        stat = self.db.out_fields('tb_building_storage', ['StorageNum', 'LastChangedTime'], 'UserId=%s AND BuildingId=%s' % (self.uid, BuildingId))
        buildingInfo = self.buildingMod.getBuildingById(BuildingId)
        BuildingLST = buildingInfo['LastChangedTime']#建筑lasChangeTime
        CompleteTime = buildingInfo['CompleteTime']
        BuildingType = buildingInfo['BuildingType']
        BuildingLevel = buildingInfo['BuildingRealLevel']#建筑当前等级
        MaxSave = self.getMaxSave(BuildingType, BuildingLevel)
        #第一次计算资源生产时候，存储表中不存在该建筑的信息，新增一条
        if not stat:
            CoinType = 2 if BuildingType == 2 else 3
            valueClause = {"BuildingId":BuildingId,
                           "UserId":self.uid,
                           "StorageNum":0,
                           "LastChangedTime":CompleteTime,
                           "BuildingType":BuildingType,
                           "CoinType":CoinType
                          }
            self.db.insert('tb_building_storage', valueClause)
            stat = valueClause
        
        #判断是否暂停计算资源
        LastChangeTime = stat.get('LastChangedTime')
        if TimeStamp <= LastChangeTime:#当前时间少于上次
            return {'Storage':stat['StorageNum'],'MaxSave':MaxSave}
        if BuildingLST <= TimeStamp <= CompleteTime:#建筑升级中,停止生产资源
            TimeStamp = BuildingLST
        else:#非升级中，取建筑完成后，最接近当前时间开始计算
            LastChangeTime = LastChangeTime if LastChangeTime>CompleteTime else CompleteTime
        
        TimeDelta = int(TimeStamp - LastChangeTime)
        HourValue = self.getOutRate(BuildingType, BuildingLevel)
        TheoryProduce = int(int(TimeDelta / 10)* 10 * HourValue / 3600)
        StorageNum = min(TheoryProduce + stat['StorageNum'], MaxSave) 
#        setClause = {"StorageNum":StorageNum,
#                        "LastChangedTime":TimeStamp - TimeDelta % 10
#                    }
#        self.db.update('tb_building_storage', setClause, 'UserId=%s AND BuildingId=%s' % (self.uid, BuildingId))
        return {'Storage':StorageNum,'MaxSave':MaxSave}
    
    def collectCoin(self,optId,BuildingType,BuildingId,CollectTimeStamp=None,StorageReq=None,param=''):
        '''
        :收集资源
        @param optId:协议号
        @param BuildingType:建筑类型
        @param BuildingId:建筑ID
        @param CollectTimeStamp:计算时间
        @param StorageReq:请求收集资源（大于后台时候以后台计算为准）
        @return: 
            {}: 成功收集
             0：没有可收集资源
             -1：建筑修复中
        '''
        coinMod = Gcore.getMod('Coin',self.uid)
        CoinType = 2 if BuildingType == 2 else 3
        MyCoin = coinMod.getCoinNum(CoinType)#获取我的储量
        CoinVol = self.buildingMod.cacStorageSpace(CoinType)#查询资源容量
        MyCoin = CoinVol if MyCoin>CoinVol else MyCoin#当已有资源大于容量时候，将拥有数目设置为最大
        CollectTimeStamp = time.time() if CollectTimeStamp is None else CollectTimeStamp
        
        StorageInfo = self.touchBuildingStorage(BuildingId,CollectTimeStamp)
        StorageCal = StorageInfo.get('Storage')
        if StorageCal==0:#没可收集资源
            return {'Remain':StorageCal,'Diff':0,'CNum':0,'NowCoin':MyCoin}
        elif StorageCal<=0:#修复中
            return -1
        
        #计算收集数量，剩余数量
        if not StorageReq:
            diff = 0
        else:
            diff = StorageCal-StorageReq
            StorageCal = StorageReq if 0<StorageReq<=StorageCal else StorageCal#消除误差，前台计算总比后台少
        
        #藩国损失
        hasHolder = Gcore.getMod('Building_hold',self.uid).hasHolder()
        collectRatio = (1-Gcore.loadCfg(Gcore.defined.CFG_BUILDING_HOLD).get('GiveRatio',0.05)) if hasHolder else 1
        storageReduce = StorageCal*collectRatio
        if (MyCoin+storageReduce)>CoinVol:
            CollectNum = CoinVol-MyCoin
            Remain = StorageCal-math.ceil(CollectNum/collectRatio)
        else:
            Remain = 0
            CollectNum = storageReduce    
        
#         Remain = MyCoin+StorageCal-CoinVol
#         Remain = 0 if Remain <0 else Remain
#         CollectNum = StorageCal-Remain#收集数量
        
        #增加资源数量并更新剩余
        flag = coinMod.GainCoin(optId,CoinType,CollectNum,'Building_resoureUI.CollectCoin',param)
        if flag:
            self.updateStorage(Remain,BuildingId,CollectTimeStamp)
        
        return {'Remain':Remain,'Diff':diff,'CNum':CollectNum,'NowCoin':MyCoin+CollectNum,'Storage':Remain}
    
    
        
    def getOutRate(self,BuildingType,BuildingLevel):
        '''计算产率,（可在这里添加计算策略）'''
        bCfg = Gcore.getCfg('tb_cfg_building_up')
        rate = bCfg.get((BuildingType, BuildingLevel),{}).get('HourValue',0)
        interMod = Gcore.getMod('Inter',self.uid)
        if BuildingType==2:#磨坊
            rate = interMod.getInterEffect(1,rate)#丰登内政
        elif BuildingType==5:#铸币厂
            rate = interMod.getInterEffect(2,rate)#铸造内政
            
        return rate
    
    def getMaxSave(self,BuildingType,BuildingLevel):
        '''计算最大储量'''
        bCfg = Gcore.getCfg('tb_cfg_building_up')
        capacity = bCfg.get((BuildingType, BuildingLevel),{}).get('SaveValue',0)
        return capacity
    
    def updateStorage(self,StorageNum,BuildingId, TimeStamp, updateMethod=1):
        '''更新存储'''
        table = 'tb_building_storage'
        if updateMethod == 1:
            setClause = {"StorageNum":StorageNum, "LastChangedTime":TimeStamp}
            whereClause = 'UserId=%s AND BuildingId=%s' % (self.uid, BuildingId)
            return self.db.update(table, setClause, whereClause)
        else:
            raise NotImplementedError, "删除建筑尚未实现"
        
    def getAllStorage(self):
        '''
                      获取所有铸币厂，军需所储量
        @return: 
        '''
        curTime = time.time()
        tb_building = self.tb_building()
        result = {}
        Buildings = self.db.out_rows(tb_building,('BuildingId'),'UserId=%s AND BuildingType in (2,5)'%self.uid)
        if Buildings is not False:
            for building in Buildings:
                result[building['BuildingId']] = {}
                result[building['BuildingId']]['Storage'] = self.touchBuildingStorage(building['BuildingId'],curTime).get('Storage')
                result[building['BuildingId']]['CalTime'] = curTime
        return result
    
    def predictOutValue(self):
        '''预计每小时产量  modify by Lizr'''
        #hour = Gcore.loadCfg(Gcore.defined.CFG_PVC).get('AddPredictHour',1)
        hour = 1 
        result = {2:0,3:0}
        t2 = self.buildingMod.getBuildingByType(2)#磨坊
        for t in t2:
            if t.get('BuildingState')==0:
                result[2] = result[2]+self.getOutRate(2,t.get('BuildingLevel'))*hour
        t5 = self.buildingMod.getBuildingByType(5)#铸币厂
        for t in t5:
            if t.get('BuildingState')==0:
                    result[3] = result[3]+self.getOutRate(5,t.get('BuildingLevel'))*hour
        return result
    
    def lostCoin(self,coinDict,optId=0):
        '''
        :扣减资源
        @param coinDict:扣减资源类型 
                -key String or int : 2,军资  3,铜钱
                -value int :扣减量
        @todo 修改扣资源方式，value/总产量（不包括升级中）
        '''
        for ct in coinDict:
            cutType = int(ct)
            value = coinDict.get(ct)          
            buildingType = 2 if cutType==2 else 5       
            coinMod = Gcore.getMod('Coin',self.uid)
            nowCoin = coinMod.getCoinNum(cutType)
            
            #库存足够，只扣库存
            if nowCoin>=value:
                coinMod.PayCoin(optId,cutType,value,'Building_resourceMod.cutOutValue',coinDict)
            
            #库存不够扣
            else:
                coinMod.PayCoin(optId,cutType,nowCoin,'Building_resourceMod.cutOutValue',coinDict)
                cutValue = value-nowCoin
                outValue = {}#每个建筑产出速度
                
                #收集资源
                t2 = self.buildingMod.getBuildingByType(buildingType)
                for t in t2:
                    if t.get('BuildingState')==0:
                        outValue[t['BuildingId']] = self.getOutRate(buildingType,t.get('BuildingLevel'))
                        self.collectCoin(optId,buildingType,t['BuildingId'],param=coinDict)
                
                
                outValueSum = sum(outValue.values())
                if outValueSum:
                    cutTime = (cutValue/outValueSum)*60
                    #暂停建筑
                    for k in outValue:
                        StorageNum = int(outValue[k]/60*cutTime)
                        sql = "UPDATE tb_building_storage SET StorageNum=StorageNum-%s Where UserId=%s AND BuildingId=%s"%(StorageNum,self.uid,k)
                        self.db.execute(sql)
        
        #扣完钱要更新redis
        Gcore.getMod('Redis',self.uid).offCacheCoin()
    
    def collectAll(self,optId=0):
        ''' 收集地里的所有资源
        @return : {
            'CoinInfo':{2:'当前军资',3:'当前铜钱'},
            'BuildingInfo':[
               {"Storage": 0, "CalTime": 0, "BuildingId": 4913},
               {"Storage": 0, "CalTime": 0, "BuildingId": 4914},
             ]
        @note : Building_holdMod.getMyHolder() 如果得到的是(0,0) 是没藩国的状态 不用扣 ,否则在收入的时候扣GiveRatio
        GiveRatio = Gcore.loadCfg(1506).get('GiveRatio',0.05)
        @remark: self.collectCoin() 当是别人藩国的状态 收入也会减少GiveRatio,就是说从地里收1000(地里实际减少了1000),玩家增钱950
        '''
        #NowCoin = {}
        collectInfos = {}
        now = time.time()
        coinMod = Gcore.getMod('Coin',self.uid)
        
        hasHolder = Gcore.getMod('Building_hold',self.uid).hasHolder()
        collectRatio = (1-Gcore.loadCfg(Gcore.defined.CFG_BUILDING_HOLD).get('GiveRatio',0.05)) if hasHolder else 1
        
        #计算
        for coinType,buildingType in {2:2,3:5}.iteritems():
            print coinType,buildingType
            myCoin = coinMod.getCoinNum(coinType)#获取我的储量
            #NowCoin[coinType] = myCoin
            
            coinVol = self.buildingMod.cacStorageSpace(coinType)#查询资源容量
            myCoin = coinVol if myCoin>coinVol else myCoin#当已有资源大于容量时候，将拥有数目设置为最大
            
            collectInfo = []
            
            buildings = self.buildingMod.getBuildingByType(buildingType)
            for building in buildings:
                if building.get('BuildingState')==0:
                    buildingId = building.get('BuildingId')
                    storageInfo  = self.touchBuildingStorage(buildingId)

                    storageCal = storageInfo.get('Storage')
                    
                    if storageCal>0 and myCoin<coinVol:
                        storageReduce = storageCal*collectRatio
                        if (myCoin+storageReduce)>coinVol:
                            collectNum = coinVol-myCoin
                            remain = storageCal-math.ceil(collectNum/collectRatio)
                        else:
                            remain = 0
                            collectNum = storageReduce                          
#                         remain = myCoin+storageCal-coinVol
#                         remain = 0 if remain <0 else remain
#                         collectNum = storageCal-remain#收集数量
                        myCoin +=collectNum
                        collectInfo.append({'CollectNum':collectNum,'Storage':remain,'CalTime':now,'BuildingId':buildingId})
            
            collectInfos[coinType] = collectInfo
        
        #收资源
        for coinType in collectInfos:
            collectNum = 0
            for building in collectInfos[coinType]:
                buildingId = building['BuildingId']
                self.updateStorage(building.get('Storage'),buildingId,now)
                collectNum += building.pop('CollectNum')
            
            print 'coinType',coinType
            print 'collectNum',collectNum
            if collectNum:
                flag = coinMod.GainCoin(optId,coinType,collectNum,'Building_resoureMod.collectAll','')
            #if flag:
            #    NowCoin[coinType] += collectNum
        
        rowCurr = Gcore.getMod('Coin',self.uid).getCurrency()
        return {
                'CoinInfo':{2:rowCurr['Jcoin'],3:rowCurr['Gcoin']},
                'BuildingInfo':collectInfos[2]+collectInfos[3]
                }
    
    def test(self):
        '''test'''
        return self.db.out_fields(self.tb_building(),('BuildingId','BuildingType'),'UserId = %s And BuildingType=99')
    


    
def _test():
    '''测试方法'''
    uid = 43798
    
    c = Building_resourceMod(uid) 
    ct = 1370680852
#    ct = 1359094231#1865,10000/1863.9800
    
#     print c.collectCoin(999,5,761)
#     print c.touchBuildingStorage(761) #刷新军需所生产  
#    print c.getAllStorage()  
#    print c.test()

#    print c.getOutRate(2, 3)
#     print c.lostCoin({2:700,3:700})
#     print c.predictOutValue()

#     print c.collectAll()
    print Gcore.getCfg('tb_cfg_building_up', (5,5), 'SaveValue')


if __name__ == '__main__':
    _test()
    Gcore.runtime()
