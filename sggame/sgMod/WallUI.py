# -*- coding:utf-8 -*-
# author:Lizr
# date:2013-3-7
# 游戏外部接口 城墙 布防

from sgLib.core import Gcore
from sgLib.core import inspector
from random import randint
class WallUI(object):
    """城墙ModId:92 
    :程序说明：
    WallDefenseId  DefenseId 在程序中出现代表是一样的东西 DefenseId只是简写
    DefenseType派生于 SoldierType ,DefenseType是200~299的SoldierType
    """
    def __init__(self, uid):
        '''注释'''
        self.uid = uid
        self.mod = Gcore.getMod('Wall',uid)
        
        
    @inspector(92001, ['DefenseType','x','y','xSize','ySize'])
    def CreateWallDefense(self,p={}):
        '''建造防御工事  Lizr'''
        optId = 92001
        defenseType = int(p['DefenseType'])
        x = p['x']
        y = p['y']
        xSize = p['xSize']
        ySize = p['ySize']
        
        buildingInfo = self.mod.getWallInfo()
        if buildingInfo is None:
            return Gcore.error(optId,-92001998)#非法操作
        wallLevel = buildingInfo.get('BuildingRealLevel')
        
        if defenseType/100 != 2: #200~299
            return Gcore.error(optId,-92001998) #非法操作
        
        Size = Gcore.getCfg('tb_cfg_soldier',defenseType,'Size')
        
        if str(xSize)+'*'+str(ySize)!=Size and str(ySize)+'*'+str(xSize)!=Size: #非配置的尺寸 1*3
            return Gcore.error(optId,-92001001) #尺寸不合法
        
#        if not self.mod.checkWallCoord(x,y): #@todo: 加上布防坐标验证
#            return Gcore.error(optId,-92001002) #坐标不合法
        
        maxCount = Gcore.getCfg('tb_cfg_wall',wallLevel,'DefenseType%s'%defenseType)
      
        defenseNum = self.mod.getDefenseNum()
        
        if defenseNum.get(defenseType,0)>=maxCount:
            return Gcore.error(optId,-92001003) #超出最大可建数量
        bookMod = Gcore.getMod('Book',self.uid)
        coinMod = Gcore.getMod('Coin',self.uid)
        defenseLevel = bookMod.getTechsLevel(1).get(defenseType,0)#从书院获取
        if defenseLevel==0:
            defenseLevel=1
        defenseCfg = Gcore.getCfg('tb_cfg_soldier_up',(defenseType,defenseLevel))
        cost = defenseCfg.get('MakeCost')
        costType = defenseCfg.get('MakeCostType')
        payState = coinMod.PayCoin(optId,costType,cost,'WallUI.CreateWallDefense',p)
#        payState = 1
        if payState:
            data={
                  'UserId':self.uid,
                  'SoldierType':defenseType,
                  'SoldierLevel':defenseLevel,
                  'xSize':xSize,'ySize':ySize,
                  'x':x,'y':y,
                  'MakeCost':cost,
                  }
            DefenseId = self.mod.createDefense(data)
            recordData = {'uid':self.uid,'ValType':0,'Val':1,'Level':defenseLevel}
            return Gcore.out(optId,{'WallDefenseId':DefenseId},mission=recordData)

        else:
            Gcore.error(optId,-92001995) #支付失败
        
    def MoveElement(self,p={}):
        '''批量移动布防内的元素'''
        optId = 92002
        ''' 参数例子:
        p = {}
        p['DefenseInfo'] = [
                             {'WallDefenseId':4,'x':1,'y':1,'xSize':1,'ySize':3},
                             {'WallDefenseId':5,'x':11,'y':13,'xSize':2,'ySize':2},
                             ]
        p['GeneralInfo'] = [
                             {'GeneralId':1,'x':8,'y':14},
                             {'GeneralId':2,'x':4,'y':43},
                             ]
        '''
#        if 'DefenseInfo' in p:
#            WallDefenseIds = [ r['WallDefenseId'] for r in p['DefenseInfo'] ]
#            
#            rows = self.mod.getDefenseInfo(WallDefenseIds)
#            for row in rows:
#                SoldierType = row['SoldierType']
#                xSize = row['xSize']
#                ySize = row['ySize']
#                Size = Gcore.getCfg('tb_cfg_soldier',SoldierType,'Size')
#
#                if str(xSize)+'*'+str(ySize)!=Size and str(ySize)+'*'+str(xSize)!=Size:
#                    return Gcore.error(optId,-92002998) #非法操作
#                #@todo 坐标验证
                
        result = self.mod.moveElement(p)
        if not result:
            return Gcore.error(optId,-92002997) #系统错误
        else:
            return Gcore.out(optId)
        
    @inspector(92003, ['WallDefenseId'])
    def DeleteWallDefense(self,p={}):
        '''拆除工事布防''' 
        optId = 92003
        defenseId = p['WallDefenseId']

        defenseInfo = self.mod.getDefenseInfo(defenseId)
        if not defenseInfo:
            return Gcore.error(optId,-92003998)#非法操作
        
        if self.mod.deleteDefense(defenseId):
            defenseType = defenseInfo.get('SoldierType')
            defenseLevel = defenseInfo.get('SoldierLevel')
            defenseCfg = Gcore.getCfg('tb_cfg_soldier_up',(defenseType,defenseLevel))
            cost = defenseCfg.get('MakeCost')
            costType = defenseCfg.get('MakeCostType')
            returnCost = cost*0.5
            coinMod = Gcore.getMod('Coin',self.uid)
            coinMod.GainCoin(optId,costType,returnCost,'WallUI.DeleteDefense',p)
            return Gcore.out(optId)
        else:
            return Gcore.error(optId,-92003995)
        
    
    def DefenseInfo(self,p={}):
        '''布防信息界面 Lizr'''
        optId = 92004
        buildingInfo = self.mod.getWallInfo()
        if not buildingInfo:
            return Gcore.error(optId,-92004998)
        
        wallLevel = buildingInfo.get('BuildingRealLevel')

        bookMod = Gcore.getMod('Book',self.uid)
        TechsDic =  bookMod.getTechsLevel(1)
        DefenseCount = self.mod.getDefenseCount() #分类统计防御工事数量
        DefenseLevels = {}
        for k,v in TechsDic.iteritems():
            if k>200 and k<300:
                if v==0:
                    v = 1
                DefenseLevels[k]=v
                if k not in DefenseCount: #没有负为0
                    DefenseCount[k] = 0
        
        DefenseInfo = self.mod.getAllDefenseInfo()
        import copy
        TrapInfo = {}
        for k,v in copy.deepcopy(DefenseInfo).iteritems():
            if v.get('SoldierType')>300:
                TrapInfo[k] = DefenseInfo.pop(k)
                
        GeneralInfo = self.mod.getDefenseGeneral()
        
        body = {
                'WallLevel':wallLevel,
                'DefenseLevels':DefenseLevels,
                'DefenseInfo':DefenseInfo,
                'TrapInfo':TrapInfo,
                'GeneralInfo':GeneralInfo,
                'DefenseCount':DefenseCount,
                'OpenSoldier':Gcore.common.list2dict(Gcore.getMod('Building_camp',self.uid).openSoliders()) #最高等级兵营开放的兵种，按开放等级排序
                }
        recordData = {'uid':self.uid,'ValType':0,'Val':1}
        return Gcore.out(optId,body,mission=recordData)
    
    def GeneralList(self,p={}):
        '''布防武将,武将列表'''
        optId = 92005
        body = {}
        body['GeneralList'] = self.mod.getWallGeneralList() 
        return Gcore.out(optId, body)
    
    @inspector(92006, ['GeneralId','x','y'])
    def SetGeneral(self,p={}):
        '''布置武将,布置上场'''
        optId = 92006
        #@todo: 加上布防坐标验证
        GeneralId = p.get('GeneralId')
        x = p.get('x')
        y = p.get('y')
        row = Gcore.getMod('General', self.uid).getGeneralInfo(GeneralId)
        if not row or row.get('UserId') != self.uid:  #武将不存在或不属于自己 
            return Gcore.error(optId,-92006998) #非法操作
        
        GeneralNum = self.mod.getWallGeneralNum() #超出可布防武将数量上限

        if GeneralNum >= 5:
            return Gcore.error(optId,-92006001)
        
#        if not self.mod.checkWallCoord(x,y,3,3): #@todo: 加上布防坐标验证
#            return Gcore.error(optId,-92006002) #坐标不合法
        
        self.mod.setGeneral(GeneralId,x,y)
        return Gcore.out(optId)
    
    @inspector(92007, ['GeneralId'])
    def RemoveGeneral(self,p={}):
        '''布置武将:移除'''
        optId = 92007
        GeneralId = p.get('GeneralId')
        result =  self.mod.removeGeneral(GeneralId)
        if result is False:
            return Gcore.error(optId,-92007996) #操作失败
        else:
            return Gcore.out(optId)
    
    @inspector(92008, ['GeneralId','SoldierType'])
    def ChangeTypeGeneral(self,p={}):
        '''布置武将:更换带兵类型'''
        optId = 92008
        GeneralId = p['GeneralId']
        TakeType = p['SoldierType']
        result =  self.mod.changeTypeGeneral(GeneralId,TakeType)
        if result is False:
            return Gcore.error(optId,-92008996) #操作失败
        else:
            return Gcore.out(optId)
       
    def BattleReport(self,p={}):
        '''战报'''
        optId = 92009
        pageNum = 20
        BattleReport = self.mod.lastBattleReport(pageNum)
        return Gcore.out(optId,{'BattleReport':BattleReport})
    
    def GetWallDefenseNum(self,p={}):
        '''获取防御工事数量'''
        optId = 92010
        defenseNum = self.mod.getDefenseNum()
        return Gcore.out(optId,{'DefenseNum':defenseNum})
    
    def RepairWallDefense(self,p={}):
        '''修复防御工事'''
        optId = 92011
        coinType = 2
        coinValue = self.mod.getRepaireCoin()
        print 'coinValue',coinValue
        if coinValue>0:
            coinMod = Gcore.getMod('Coin', self.uid)
            payState = coinMod.PayCoin(optId,coinType,coinValue,'WallUI.RepairWallDefense',p)
            if payState:
                repairNum = self.mod.repairWallDefense()
                if repairNum: #修复了多少个
                    recordData = {'uid':self.uid,'ValType':0,'Val':repairNum}
                    return Gcore.out(optId, {'coinType':coinType,'coinValue':coinValue,'repairNum':repairNum},mission=recordData )
                else:
                    return Gcore.error(optId,-92011997) #系统失败
            else:
                return Gcore.error(optId,-92011995) #支付失败
        else:
            return Gcore.error(optId,-92011001) #无可修复防御工事
        
    def CleanWallDefense(self,p={}):
        '''回收损毁的防御工事'''
        optId = 92012
        CoinValue = self.mod.clearWallDefense()
        if CoinValue:
            Gcore.getMod('Coin',self.uid).GainCoin(optId,2,CoinValue,'WallUI.CleanWallDefense',p)#返回军资
            reward = self.mod.getWallBoxReward() #获取遗落宝箱的奖励
            if reward:#有奖励
                rewardType = reward['RewardType']
                goodsId = reward['GoodsId']
                goodsNum = reward['GoodsNum']
                ids = Gcore.getMod('Reward',self.uid).reward(optId,p,rewardType,goodsId,goodsNum)
                #reward['WillGet'] = 1
                if rewardType==1:
                    if isinstance(ids,list):
                        reward['EquipIds'] = ids
                    else:
                        reward['EquipIds'] = []
                
            else:#无奖励
                #reward = {'WillGet':0}
                reward = {}
   
            recordData = {'uid':self.uid,'ValType':0,'Val':1,'WillGet':reward.get('WillGet')}
            body = {"CoinType":2,"CoinValue":CoinValue,"Reward":reward}
            return Gcore.out(optId,body,mission=recordData)
        else:
            return Gcore.error(optId,-92012001) #没有可回收的防御工事
            
        

def test():
    uid = 1011 #43277
    c = WallUI(uid)
    #p = {"DenfenseInfo": [{"y": 46, "x": 20, "GeneralId": 10697}], "ClientTime": 0}
#    p = {"DenfenseInfo": [{"ySize": 3, "DefenseId": "215", "xSize": 2, "DefenseType": "205", "y": 57, "x": 21}], "ClientTime": 0}
#    c.MoveElement(p)

#    para = {
#                "DefenseType":  "203",
#                "x":    "28",
#                "y":    "10",
#                "xSize":        "1",
#                "ySize":        "3"
#        }
#    c.CreateWallDefense(para)
    
   
#    c.DeleteWallDefense({'DefenseId':9}) #拆除工事
#    c.GeneralList() #选择武将列表
#    c.DefenseInfo() #布防界面
#    c.SetGeneral({"y": 40, "x": 13, "GeneralId": 10692}) #布置武将上场
    
    
#    c.SetGeneral({"GeneralId":15092,"x":31,"y":11}) #布置武将上场
#    c.SetGeneral({"GeneralId":15094,"x":41,"y":11}) #布置武将上场

#     c.RemoveGeneral({"GeneralId":6}) #布置武将:移除
#     c.ChangeTypeGeneral( {"GeneralId":5,"TakeType":2} )  #布置武将:更换带兵类型
#    c.BattleReport() #战报
#     c.ErrorTest()
#    print Gcore.getCfg('tb_cfg_map_valid_siege').keys()
#    c.RepairWallDefense()
    print c.CleanWallDefense()


if __name__ == '__main__':
    test()
