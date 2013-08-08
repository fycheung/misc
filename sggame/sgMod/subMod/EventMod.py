# -*- coding:utf-8 -*-
# author:Zhanggh
# date:2013-6-5
# 模块说明:事件模型

from sgLib.core import *
from sgLib.base import Base

#自定义事件编号
'''
1.建筑完成，
2.建筑升级完成，
3.科技升级完成,
4.主角获得经验，(PlayerMod)
5.主角获得荣誉值，(PlayerMod)
6,计算兵营，工坊产兵数量，（）
7.获得资源（货币类型 1,2,3,4）
8.武将获得经验（）
9.获得好感度
10.PVE获得星
11.内政获得加成
12.战斗结束
13.校场算兵
14.武将四维变化
'''

class EventMod(Base):
    '''事件模型'''
    def __init__(self,uid):
        Base.__init__(self,uid)
        self.uid = uid
        
    def OptId2MyEvent(self,optId,data):
        '''OptId触发自定义事件
        15004触发1,2
        15053触发3
        '''
        achieveMod = Gcore.getMod('Building_home',self.uid)
        missionMod = Gcore.getMod('Mission',self.uid)
        if optId==15004:#建筑加速
            buildingLevel = data.get('BuildingLevel')
            if buildingLevel<=1:#建筑建造完成
                missionMod.missionTrigger(1)
                achieveMod.achieveTrigger(1)
            else:#升级完成
                missionMod.missionTrigger(2)
                achieveMod.achieveTrigger(2)
                
        elif optId==15053:#科技加速
            buildingType = data.get('BuildingType')
            if buildingType==12:#书院科技升级完成
                missionMod.missionTrigger(3)
                achieveMod.achieveTrigger(3)
    
    def payCoinTrigger(self,optId,coinValue):
        '''货币消耗事件触发'''
        #增加主角经验
        expCfg = Gcore.getCfg('tb_cfg_exp_get').values()
        getWays = [ec['GetWay'] for ec in expCfg if ec['GetWay']/100==0 and str(optId) in ec['OptId'].split(',')]
        for getWay in getWays:
            Gcore.getMod('Player',self.uid).addUserExp(getWay,amount=coinValue,optId=optId)
    
    def gainCoinTrigger(self,optId,coinType,coinValue,nowCoin,isFull):
        '''
         :获得资源
         :事件ID=7
        @param optId:
        @param coinType:
        @param coinValue:
        @param isFull:
        '''
        if coinValue>0:
            mData = {'ValType':coinType,'Val':coinValue,
                     'NowCoin':nowCoin,'isFull':isFull}
            Gcore.getMod('Mission',self.uid).missionTrigger(7,mData)
        
    
    def soldierGet(self,soldiers):
        '''
        :获得兵或器械(将弃用)
        :事件ID=6
        @param st:兵种类型
        @param num:数量
        '''
#         print '获得兵或器械',soldiers
        if soldiers:
            print '事件——获得兵',soldiers
            Gcore.getMod('Building_home',self.uid).achieveTrigger(6,{'ValType':0,'Val':1,'Soldiers':soldiers})
#             Gcore.getMod('Mission',self.uid).missionTrigger(6,{'ValType':0,'Val':1,'Soldiers':soldiers})
            
#     
    def generalExpGet(self,gt,exp):
        '''
        :武将获得经验
        :事件ID=8
        @param gt:武将类型
        @param exp:获得经验值
        '''
        print '获得武将经验'
        Gcore.getMod('Building_home',self.uid).achieveTrigger(8,{'ValType':gt,'Val':exp})
    
    def favorGet(self,friendId,num):
        '''
        :获得好感度
        :事件ID=9
        '''
        Gcore.getMod('Mission',self.uid).missionTrigger(9,{'ValType':0,'Val':num})
        Gcore.getMod('Mission',friendId).missionTrigger(9,{'ValType':0,'Val':num})
        
    def pveStarGet(self,num):
        '''
        :pve当前已获得星
        :事件ID=10
        '''
        Gcore.getMod('Building_home',self.uid).achieveTrigger(10,{'ValType':0,'Val':num})
    
    def interGet(self):
        '''内政获得加成
        :事件ID=11'''
        Gcore.getMod('Mission',self.uid).missionTrigger(11)
    
    def battleEnd(self,battleType,fromType,endType,troops,result,warId=0):
        '''
        :战斗结束
        :事件ID=12 
        @param battleType:战斗类型, #1PVE战役   2PVC攻城
        @param fromType:战斗方式PVE,0:非扫荡1:扫荡 ；PVP： 1, #1查找 2反击 3反抗 4抢夺 
        @param endType:结束类型 0:普通，1：立即结束
        @param troops:出兵{'兵种'：数量}
        @param result:{'Star':星,'Result':1成功2失败,'Coin':{'Jcoin','Gcoin'},'Honour':荣誉,'Expand':{1,3,3兵},'GeneralExp': 战役才有的武将经验}
        @param warId:战役Id 
        '''
        recordData = {'ValType':0,'Val':1,'BattleType':battleType,
                      'FromType':fromType,'EndType':endType,'Troops':troops,
                      'Result':result,'WarId':warId}
        
#         print '战斗结束EventMod',recordData
        
        Gcore.getMod('Mission',self.uid).missionTrigger(12,recordData)
        Gcore.getMod('Building_home',self.uid).achieveTrigger(12,recordData)
        Gcore.getMod('Activity',self.uid).actionTrigger(12,recordData)
        
        #战斗获得经验
        playerMod = Gcore.getMod('Player',self.uid)
        if battleType==1 and result.get('Result')==1:#PVE胜利
            playerMod.addUserExp(101,0,12)
        elif battleType==2 and result.get('Result')==1:#PVP攻城胜利
            playerMod.addUserExp(103,0,12)
    
    def updateSoldierNum(self,soldiers):
        '''
        :校场兵更新(将弃用)
        :事件ID=13
        @param soldiers:
        '''
        print '校场兵更新'
        Gcore.getMod('Mission',self.uid).missionTrigger(13,{'ValType':0,'Val':1,'Soldiers':soldiers})
    
    def generalChangeAttr(self,f,s,w,l):
        '''
        :武将属性变化
        :事件ID=14
        '''
        Gcore.getMod('Mission',self.uid).missionTrigger(14,{'ValType':0,'Val':1})
        
    def test(self):
        print '''sdfsadf'''

def test():
    """测试方法"""
    uid = 43553
    e = EventMod(uid)
#     print e.payCoinTrigger(15002,1)
#     e.soldierGet(6,11)
#     e.pveStarGet(9)
#     print e.interGet()
#     e.gainCoinTrigger(99999,2,1232,33333,0)

    Gcore.printd(Gcore.getCfg('tb_cfg_item_box'))
    
    
if __name__ == '__main__':
    test()
    
    
    