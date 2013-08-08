# -*- coding:utf-8 -*-
# author:
# date:2013-1-
# 游戏外部接口模板
import time
from sgLib.core import Gcore
from sgLib.core import inspector

class Building_homeUI(object):
    """测试 ModId:99 """
    def __init__(self, uid):
        '''注释'''
        self.uid = uid
        self.mod = Gcore.getMod('Building_home', uid)
        #print self.mod\
        
    def GetInters(self,p={}):
        '''查询内政加成'''
        optId = 15110
        inters = self.mod.getInters()
        recordData = {'uid':self.uid,'ValType':0,'Val':1}#成就、任务记录
        return Gcore.out(optId,inters,mission=recordData)
    
    def GetAchievements(self,p={}):
        '''获取我的成就'''
        optId = 15111
        achieves = self.mod.getAchievements()
        recordData = {'uid':self.uid,'ValType':0,'Val':1}#成就、任务记录
        return Gcore.out(optId,{'Achieves':achieves},mission=recordData)
        
    
    @inspector(15112,['AchieveType'])
    def GetReward(self,p={}):
        '''领取奖励'''
        optId = 15112
        achieveType = p['AchieveType']
        
        achiCfg = Gcore.getCfg('tb_cfg_achieve',achieveType)
        if achiCfg is None:
            return Gcore.error(optId,-15112001)#无此项成就
        
        achieve = self.mod.getAchieveInfo(achieveType)#查询成就信息
        current = achieve.get('CurrentAchieve')
        currentAchieveId = achieve.get('CurrentAchieveId')
        rewAchieveId = achieve.get('NextAchieveId')#领取的奖励
        rewAchieve = achiCfg.get(rewAchieveId).get('AchieveRequire')
        if current < rewAchieve:
            return Gcore.error(optId,-15112002)#成就未达成
        
        if achieve['Finished']==1:
            return Gcore.out(optId,{'Finished':1,'GetAchieve':rewAchieveId})#成就已完成
        
        maxAchieveId = max(achiCfg.keys())#最大成就值
        
        if  rewAchieveId==maxAchieveId:#成就完成
            data = {'NextAchieveId':rewAchieveId,'Finished':1,'CurrentAchieveId':rewAchieveId}
            mission = {'uid':self.uid,'ValType':0,'Val':1}#任务记录
        else:
            data = {'NextAchieveId':rewAchieveId+1,'Finished':0,'CurrentAchieveId':rewAchieveId}
            mission  = {}
        updateWhere = 'UserId=%s AND AchieveType=%s AND CurrentAchieveId=%s'%(self.uid,achieveType,currentAchieveId)
        if self.mod.updateAchieveByWhere(data,updateWhere):
            achiCfg = achiCfg.get(rewAchieveId)
            rewardType = achiCfg.get('RewardType')
            rewardValue = achiCfg.get('AchieveReward')
            coinMod = Gcore.getMod('Coin',self.uid)
            coinMod.GainCoin(optId,rewardType,rewardValue,'Building_homeUI.GetReward',p)
            return Gcore.out(optId,data,mission=mission)
        else:
            return Gcore.error(optId,-15112996)#操作失败
        
    def test(self,para={}):
        '''测试方法'''
        print 333
        
    
    
        

def test():
    uid = 1032
#     uid = 43275
    c = Building_homeUI(uid)
#     p = c.GetInters()
#     p = b.GetReward({'AchieveType':1})
    p = c.GetAchievements()
    print p

if __name__ == '__main__':
    test()
