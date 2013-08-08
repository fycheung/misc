# -*- coding:utf-8 -*-
# author:zhoujingjiang
# date:2013-1-30
# 游戏外部接口:点将台

import sys
from random import choice, randint

from sgLib.core import Gcore, inspector

class Building_trainUI(object):
    '''点将台功能外部接口'''
    def __init__(self, uid):
        self.uid = uid
        
    @inspector(15010, ['GeneralId', 'CoinType'])
    def TrainGeneral(self, param={}):
        '''点将台：培养武将'''
        optId = 15010
        
        GeneralId = param["GeneralId"]
        CoinType = param["CoinType"]
        
        #武将信息
        modGeneral = Gcore.getMod('General', self.uid)
        GeneralInfo = modGeneral.getLatestGeneralInfo(GeneralIds=GeneralId)
        if not GeneralInfo:
            return Gcore.error(optId, -15010997) #用户没有该武将 

        TrainCfg = Gcore.getCfg('tb_cfg_general_up', GeneralInfo['GeneralLevel'])
        #判断是否可培养:如果武力，智力，速度，统帅都得到培养上限则不可培养
        if GeneralInfo["TrainForceValue"]>=TrainCfg["TrainLimit"] \
           and GeneralInfo["TrainWitValue"]>=TrainCfg["TrainLimit"] \
           and GeneralInfo["TrainSpeedValue"]>=TrainCfg["TrainLimit"] \
           and GeneralInfo["TrainLeaderValue"]>=TrainCfg["TrainLimit"]:
            return Gcore.error(optId, -15010001) #该武将所有培养属性已达等级上限，不可培养
        
        #添加将卡培养判断 add by qiudx
        if CoinType == 3:
            generalType = GeneralInfo['GeneralType']
            quality = Gcore.getCfg('tb_cfg_general', generalType, 'Quality')
            if quality < 2:
                return Gcore.error(optId, -15010005) #三星以下武将无法进行将卡培养
            itemId = generalType + 1100
            bagMod = Gcore.getMod('Bag', self.uid)
            itemNum = bagMod.useItems(itemId)
            if itemNum < 1:
                return Gcore.error(optId, -15010006) #没有对应的武将卡
        
        Cfg = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_TRAIN)
        if int(CoinType) == 1: #黄金培养：随机值从5到20
            RandomForce = randint(Cfg["GoldCoinMin"],Cfg["GoldCoinMax"])
            RandomWit = randint(Cfg["GoldCoinMin"],Cfg["GoldCoinMax"])
            RandomSpeed = randint(Cfg["GoldCoinMin"],Cfg["GoldCoinMax"])
            RandomLeader = randint(Cfg["GoldCoinMin"],Cfg["GoldCoinMax"])
        elif int(CoinType) == 2: #军资培养：随即值从-15到20
            #把0从中删除
            rand_nums = list(range(Cfg["JCoinMin"],Cfg["JCoinMax"]+1))
            if 0 in rand_nums:
                rand_nums.remove(0)
            
            RandomForce = choice(rand_nums) if rand_nums else 0
            RandomWit = choice(rand_nums) if rand_nums else 0
            RandomSpeed = choice(rand_nums) if rand_nums else 0
            RandomLeader = choice(rand_nums) if rand_nums else 0
        elif int(CoinType) == 3: #将卡培养
            generalType = GeneralInfo['GeneralType']
            quality = Gcore.getCfg('tb_cfg_general', generalType, 'Quality') + 1
            started = Cfg["CardTrainMin" + str(quality)]
            ended = Cfg["CardTrainMax" + str(quality)]
            RandomForce = randint(started, ended)
            RandomWit = randint(started, ended)
            RandomSpeed = randint(started, ended)
            RandomLeader = randint(started, ended)
        else:
            return Gcore.error(optId, -15010002) #货币类型错误

        #随机值与武将现有培养属性的和不得大于培养上限
        if RandomForce + GeneralInfo["TrainForceValue"] >= TrainCfg["TrainLimit"]:
            RandomForce = TrainCfg["TrainLimit"] - GeneralInfo["TrainForceValue"]
        if RandomWit + GeneralInfo["TrainWitValue"] >= TrainCfg["TrainLimit"]:
            RandomWit = TrainCfg["TrainLimit"] - GeneralInfo["TrainWitValue"]
        if RandomSpeed + GeneralInfo["TrainSpeedValue"] >= TrainCfg["TrainLimit"]:
            RandomSpeed = TrainCfg["TrainLimit"] - GeneralInfo["TrainSpeedValue"]
        if RandomLeader + GeneralInfo["TrainLeaderValue"] >= TrainCfg["TrainLimit"]:
            RandomLeader = TrainCfg["TrainLimit"] - GeneralInfo["TrainLeaderValue"]
        
        #加上随即值之后，武将的培养属性不能小于0。
        if RandomForce + GeneralInfo["TrainForceValue"] < 0:
            RandomForce = - GeneralInfo["TrainForceValue"]
        if RandomWit + GeneralInfo["TrainWitValue"] < 0:
            RandomWit =  - GeneralInfo["TrainWitValue"]
        if RandomSpeed + GeneralInfo["TrainSpeedValue"] < 0:
            RandomSpeed = - GeneralInfo["TrainSpeedValue"]
        if RandomLeader + GeneralInfo["TrainLeaderValue"] <0:
            RandomLeader = - GeneralInfo["TrainLeaderValue"]

        TrainDic = {}
        TrainDic['GeneralId'] = GeneralId
        TrainDic['RandomForce'] = RandomForce
        TrainDic['RandomWit'] = RandomWit
        TrainDic['RandomSpeed'] = RandomSpeed
        TrainDic['RandomLeader'] = RandomLeader
        
        if CoinType == 1 or CoinType == 2:
            CostValueType = 'NormalTrainCost' if CoinType == 2 else 'GoldTrainCost'
            CostValue = TrainCfg[CostValueType]
            if CoinType == 2:
                CostValue = Gcore.getMod('Inter', self.uid).getInterEffect(10, CostValue)
        
            CoinMod = Gcore.getMod('Coin', self.uid)
            classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)    
            pay = CoinMod.PayCoin(optId,CoinType,CostValue,classMethod,param)
            if pay < 0:
                return Gcore.error(optId, -15010003) #支付失败
        
        modTrain = Gcore.getMod('Building_train', self.uid)
        ret_dic = {
                   "TrainForce":RandomForce, 
                   "TrainWit":RandomWit,
                   "TrainSpeed":RandomSpeed,
                   "TrainLeader":RandomLeader
                   }
        #普通培养
        if CoinType == 2:
            stat = modTrain.normalAddTrainNum(-1, **TrainDic)
            if stat == -1:
                #把扣的钱加回去
                CoinMod.GainCoin(optId,CoinType,CostValue,classMethod,param)
                return Gcore.error(optId, -15010004) #培养次数不足
            else:
                ret_dic["TrainNum"] = stat[0]
        #黄金培养
        elif CoinType == 1:
            modTrain.goldenTrain(GeneralId, RandomForce, RandomWit,
                                 RandomSpeed, RandomLeader)
        #将卡培养
        elif CoinType == 3:
            modTrain.saveTrainGeneral(GeneralId, RandomForce, RandomWit, RandomSpeed, RandomLeader)
        else:
            return Gcore.error(optId, -15010005) #货币类型错误
        
        #武将培养记录 add by zhanggh 5.29
        modGeneral.addTrainRecord(GeneralInfo['GeneralType'], CoinType)
        recordData = {'uid':self.uid, 'ValType':CoinType, 'Val':1}#成就、任务记录
        
        return Gcore.out(optId, body=ret_dic, achieve=recordData,mission=recordData)
    
    @inspector(15011, ['GeneralId'])
    def SaveTrain(self, param = {}):
        '''点将台：保留培养的属性'''
        optId = 15011
        
        GeneralId = param["GeneralId"]

        modTrain = Gcore.getMod('Building_train', self.uid)
        TrainInfo = modTrain.getTrainRandoms(GeneralId)
        if not TrainInfo:
            return Gcore.error(optId, -15011001) #没有该武将的培养信息
        
        #培养所得的属性值
        TrainForce = TrainInfo["RandomForce"]
        TrainWit = TrainInfo["RandomWit"]
        TrainSpeed = TrainInfo["RandomSpeed"]
        TrainLeader = TrainInfo["RandomLeader"]
        
        modTrain.cancTrainRandoms() #先将培养信息置为无效
        
        #更新武将表
        if TrainForce or TrainWit or TrainSpeed or TrainLeader:
            #如果全是0，直接返回。
            stat = modTrain.saveTrainGeneral(GeneralId, TrainForce, TrainWit, 
                                             TrainSpeed, TrainLeader)        
            if not stat:
                return Gcore.error(optId, -15011002) #用户没有该武将

        return Gcore.out(optId, {})
    
    @inspector(15012, ['GeneralId'])
    def DeleteGeneral(self, param = {}):
        '''点将台：遣散一名武将'''
        optId = 15012
        
        GeneralId = param['GeneralId']
        
        modGeneral = Gcore.getMod('General', self.uid)
        stat = modGeneral.deleteGeneralById(GeneralId)
        if stat == -1:
            return Gcore.error(optId, -15012001) #用户没有该武将
        if stat == -2:
            return Gcore.error(optId, -15012002) #武将身上有装备，无法遣散
        
        return Gcore.out(optId, {})
    
    @inspector(15013)
    def GetGenerals(self, param={}):
        '''点将台：获取所有武将的最新信息'''
        optId = 15013
        
        TimeStamp = param['ClientTime']
        uid = param.get('UserId')
        uid = uid if uid else self.uid
        
        modGeneral = Gcore.getMod('General', uid)
        Generals = modGeneral.getLatestGeneralInfo(TimeStamp=TimeStamp)

        return Gcore.out(optId, {"Generals":Generals})

    @inspector(15014)
    def GetTrainNum(self, param={}):
        '''点将台：获取点将台的可培养次数'''
        optId = 15014
        
        TimeStamp = param['ClientTime']
        
        modTrain = Gcore.getMod('Building_train', self.uid)
        TrainNum, MaxTrainNum = modTrain.normalAddTrainNum(TimeStamp=TimeStamp)
        return Gcore.out(optId, body={"TrainNum":TrainNum, 
                                      "MaxTrainNum":MaxTrainNum})
    
    @inspector(15015, ['GeneralId', 'EquipPart', 'EquipId'])
    def ChangeEquip(self, param={}):
        '''点将台：给武将穿装备或更换武将装备'''
        optId = 15015
        
        GeneralId = param['GeneralId']
        EquipPart = param['EquipPart']
        EquipId = param['EquipId']
        TimeStamp = param['ClientTime']
        Flag = param.get('Flag') #Falg-False换装备；1，换宝物；其他换兵书

        #武将信息
        modGeneral = Gcore.getMod('General', self.uid)
        General = modGeneral.getLatestGeneralInfo(GeneralIds=GeneralId,TimeStamp=TimeStamp)
        if not General:
            return Gcore.error(optId, -15015001) #玩家无此武将

        if not Flag:
            stat = modGeneral.changeEquip(General, EquipPart, EquipId)
            if stat == -1:
                return Gcore.error(optId, -15015002) #装备部位出错
            if stat == -2:
                return Gcore.error(optId, -15015003) #没有换装
            if stat == -3:
                return Gcore.error(optId, -15015004) #装备不存在
            if stat == -4:
                return Gcore.error(optId, -15015005) #装备正被其他武将穿着
            if stat == -5:
                return Gcore.error(optId, -15015006) #没达到可穿戴等级
            if stat == -6:
                return Gcore.error(optId, -15015007) #强化等级高于武将等级
            if stat == -7:
                return Gcore.error(optId, -15015008) #该装备不能穿在该部位
        else:
            print '更换兵书或宝物'
            stat = modGeneral.changeEquip_EX(General, EquipId, Flag)
            print 'stat', stat
            if stat == -1:
                return Gcore.error(optId, -15015009) #没有这个兵书或宝物
            if stat == -2:
                return Gcore.error(optId, -15015010) #要穿的兵书或宝物不处于空闲状态
            if stat == -3:
                return Gcore.error(optId, -15015011) #兵书或宝物正在武将身上穿着
            if stat == -4:
                return Gcore.error(optId, -15015012) #未达到穿戴等级
            if stat == -5:
                return Gcore.error(optId, -15015013) #装备强化度大于武将等级
        
        #返回
        recordData = {'uid':self.uid, 'ValType':0, 'Val':1}#成就、任务记录
        return Gcore.out(optId, body={}, mission=recordData)
    
    @inspector(15016, ['EquipPart', 'GeneralId'])
    def StripEquip(self, param={}):
        '''点将台：将武将某个部位的装备脱下来'''
        optId = 15016
        
        GeneralId = param['GeneralId']
        EquipPart = param['EquipPart']
        Flag = param.get('Flag') #False脱装备；1脱宝物；其他脱兵书
        
        modGeneral = Gcore.getMod('General', self.uid)
        General = modGeneral.getGeneralInfo(GeneralId)
        if not General:
            return Gcore.error(optId, -15016001) #玩家无此武将
        
        if not Flag:
            stat = modGeneral.stripEquip(General, EquipPart)
            if stat == -1:
                return Gcore.error(optId, -15016002) #装备部位不正确或该武将在该部位上没有装备
            if stat == -2:
                return Gcore.error(optId, -15016003) #向背包中增加装备失败
        else:
            stat = modGeneral.stripEquip_EX(GeneralId, Flag)
            if stat == -1:
                return Gcore.error(optId, -15016004) #没穿兵书或宝物
            if stat == -2:
                return Gcore.error(optId, -15016005) #背包已满

        #返回
        return Gcore.out(optId, body={})
#end class Building_trainUI

if __name__ == '__main__':
    o = Building_trainUI(44493)
    print Gcore.printd(o.GetGenerals())