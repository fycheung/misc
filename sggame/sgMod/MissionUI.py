# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-5-6
# 模块说明

import sys
from sgLib.core import Gcore, inspector
import sgLib.common as com


class MissionUI(object):
    '''任务系统'''
    def __init__(self,uid):
        self.mod = Gcore.getMod('Mission', uid)
        self.uid = uid
    
    def GetMissionList(self,p={}):
        '''
                    查询任务列表
        '''
        optId=22001
        re=self.mod.getMyMissions()
        re = com.list2dict(re,0)
        return Gcore.out(optId,{'MLS':re})
    
    @inspector(22002,['MID'])
    def CheckMission(self,p={}):
        '''查看新任务'''
        optId=22002
        mId=p['MID']
        mCfg = Gcore.getCfg('tb_cfg_mission',mId)
        if mCfg is None:
            return Gcore.error(optId,-22002001)#任务不存在
        self.mod.actionMyMission(mId)
        return Gcore.out(optId,{})
    
    @inspector(22003,['MID'])
    def GetReward(self,p={}):
        '''
                    领取任务奖励
        '''
        optId=22003
        mId=p['MID']
        
        mCfg = Gcore.getCfg('tb_cfg_mission',mId)
        if mCfg is None:
            return Gcore.error(optId,-22003001)#任务不存在
#         mInfo = self.mod.getMissionInfo(mId)
#         if mInfo is None:
#             return Gcore.error(optId,-22003001)#任务不存在
#         #1: 新接,2:进行中,3:已完成,4:已领取奖励
#         elif mInfo.get('Status')!=3:
#             return Gcore.error(optId,-22003002)#任务未完成
        whereClause = 'UserId=%s AND MissionId=%s AND Status=3'%(self.uid,mId)
        updateFlag = self.mod.updateMissionByWhere({'Status':4},whereClause)#先更新任务状态，防止并发
        if not updateFlag:
            return Gcore.error(optId,-22003002)#任务未完成
        #领取奖励
        coinMod = Gcore.getMod('Coin',self.uid)
        playerMod = Gcore.getMod('Player',self.uid)
        rewardMod = Gcore.getMod('Reward',self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        
        expReward = mCfg.get('RewardExp',0)
        JCReward = mCfg.get('RewardJCoin',0)
        GCReward = mCfg.get('RewardGCoin',0)
        GReward = mCfg.get('RewardGold',0)
        
        #发放奖励
        playerMod.addUserExp(0,expReward,optId)
        coinMod.GainCoin(optId,1,GReward,classMethod,p)
        coinMod.GainCoin(optId,2,JCReward,classMethod,p)
        coinMod.GainCoin(optId,3,GCReward,classMethod,p)
        
        rt1 = mCfg.get('RewardType1',0)
        rt2 = mCfg.get('RewardType2',0)
        equipIds = []
        if rt1!=0:
            f = rewardMod.reward(optId,p,rt1,mCfg['GoodsId1'],mCfg['GoodsNum1'])
            if rt1==1 and isinstance(f,list):
                equipIds = equipIds+f
        if rt2!=0:
            f = rewardMod.reward(optId,p,rt2,mCfg['GoodsId2'],mCfg['GoodsNum2'])
            if rt2==1 and isinstance(f,list):
                equipIds = equipIds+f
#         self.mod.updateMissions({mId:{'Status':4}})
        self.mod.getNewMission(mId)
        
        myMissions =self.mod.getMyMissions()
        myMissions = com.list2dict(myMissions,0)
        re={'EIds':equipIds,'MLS':myMissions}
        return Gcore.out(optId,re)
    
    @inspector(22004,['EID'])
    def EventTrigger(self,p={}):
        '''事件触发
        1.建筑完成，
        2.建筑升级完成，
        3.科技升级完成'''
        optId = 22004
        eId  = p['EID']
        if eId not in [1,2,3]:
            return Gcore.error(optId,-22004001)#事件ID未定义
        self.mod.missionTrigger(eId)
        Gcore.getMod('Building_home',self.uid).achieveTrigger(eId)

        return Gcore.out(optId,{})
    

    def TouchMission(self,p={}):
        '''前台触发任务完成，将弃用'''
        optId = 22006
        mId = p['MID']
        mCfg = Gcore.getCfg('tb_cfg_mission',mId)
        if mCfg is None:
            return Gcore.error(optId,-22003001)#任务不存在
        mOptId = mCfg.get('OptId')
        if str(optId)!=mOptId:
            return Gcore.error(optId,-22003002)#此任务非前台触发
        mInfo = self.mod.getMissionInfo(mId,['Status'])
        if mInfo is None:
            return Gcore.error(optId,-22003003)#此任务未接收
        ms = mInfo['Status']
        if ms!=1 or ms!=2:
            return Gcore.error(optId,-22003004)#此任务已完成
        self.mod.updateMissions({mId:{'Status':3}})
        return Gcore.out(optId,{})
    
    def CheckMissionStatus(self ,p={}):
        '''检查任务状态'''
        optId = 22005
        self.mod.updateAllMissions()
        
        Gcore.getMod('Building_home',self.uid).updateAllAchieves()
        return Gcore.out(optId)
    

    



def test():
    """测试方法"""
    uid = 43522
    m = MissionUI(uid)
#     m.GetMissionList()
#     m.CheckMission({'MID':1003})
#    m.TouchMission({'MID':1003})
#     print m.GetReward({'MID':1163})
#     print Gcore.getCfg('tb_cfg_mission',1003).keys()
#     print m.EventTrigger({'EID':3})
#     print m.CheckMissionStatus()

    
if __name__ == '__main__':
    test()