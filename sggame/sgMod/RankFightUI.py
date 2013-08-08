# -*- coding:utf-8 -*-
# author:Lizr
# date:2013-8-1
# 排名争斗 演武场 比武 

from sgLib.core import Gcore,inspector

class RankFightUI(object):
    """ 排名争斗 演武场 比武  """
    def __init__(self, uid):
        '''注释'''
        self.uid = uid
        self.mod = Gcore.getMod('RankFight',uid)
    
    def Test(self,para={}):
        '''测试方法'''
        optId = 24000
        
    def RankFightInfo(self,para={}):
        '''比武主界面 和 排名奖励界面 所需数据'''
        optId = 24001
        UserLevel = Gcore.getUserData(self.uid,'UserLevel')
        OpenLevel = Gcore.loadCfg(2401).get('RankFightOpenLevel')
        if UserLevel<OpenLevel:
            return Gcore.error(optId,-24001001)
        RankFightInfo = self.mod.getRankFightInfo()
        RankReward = self.mod.getRankReward()
        return Gcore.out(optId,{'RankFightInfo':RankFightInfo,'RankReward':RankReward})
    
    def SpeedupFightTime(self,para={}):
        '''加速比武冷却时间'''
        optId = 24002
        result = self.mod.speedupRankFight()
        return Gcore.out(optId,{'SpeedupResult':result})
    
    def GainRankReward(self,para={}):
        '''领取排名奖励'''
        optId = 24003
        checkstate = self.mod.checkGetReward()
        if checkstate == -1:
            return Gcore.error(optId,-24003001) #您今天已经领取过奖励
        if checkstate == -2:
            return Gcore.error(optId,-24003002) #不符合领取奖励条件
        else:
            gainRewardList = self.mod.gainRankReward(optId)
            return Gcore.out(optId,{'gainRewardList':gainRewardList})
    
    
if __name__ == '__main__':
    uid = 1001
    c = RankFightUI(uid)
    c.RankFightInfo()
    #c.RankReward()
    #c.SpeedupFightTime()
    #c.GainRankReward()