# -*- coding:utf-8 -*-
# author:Yew
# date:2013-4-24
#交互系统Mod

import datetime
import time
from sgLib.core import Gcore
from sgLib.base import Base

class InteractMod(Base):
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
        self.modFriend = Gcore.getMod('Friend', self.uid)
    
        
    def getGeInteractLog(self, generalId):
        '''
                    根据武将获取武将交流记录
        '''
        fields = ['NickName', 'McoinNum', 'InteractTime']
        where = 'GeneralId=%s AND isGet=0 AND u.UserId=g.UserId order by InteractTime'%generalId
        return self.db.out_rows('tb_interact_general g, tb_user u', fields, where)
    
        
    
    def setGeInteractGet(self, generalId):
        '''
                    设置武将交流记录领取状态为已领取
        '''
        row = {'isGet': 1}
        where = 'GeneralId=%s AND isGet=0'%generalId
        return self.db.update('tb_interact_general', row, where)
    
    def getHaveMcoinGeneralIds(self):
        '''
                    获取有未领取美酒的武将ID
        '''
        where = 'GeneralUserId=%s AND isGet=0 group by GeneralId'%self.uid
        return self.db.out_list('tb_interact_general','GeneralId', where)
        #group by GeneralId
    
    def getInteractTime(self, interactType):
        '''
                        获取交互次数
        @param interactType: 交互类型
        '''
        if interactType == 1:
            table='tb_interact_visit'
        if interactType == 3:
            table='tb_interact_general'
        
        today = datetime.date.today()
        day = time.mktime(today.timetuple())
        where='UserId=%s AND InteractTime>%s'%(self.uid, day)
        return self.db.out_field(table, 'count(1)', where)
    
    def insertVisitInteract(self,friendUserId,mcoinNum):
        '''
                    添加初次访问好友日志
        @param friendUserId:
        @param mcoinNum:
        '''
        now=Gcore.common.nowtime()
        row={'UserId':self.uid,
             'VisitUserId':friendUserId,
             'McoinNum':mcoinNum,
             'interactTime':now}
        
        return self.db.insert('tb_interact_visit',row)
    
    def insertGeneralInteract(self,friendUserId,generalId,mcoinNum):
        '''
                    添加武将交流记录
        @param friendUserId:
        @param generalId:
        @param mcoinNum:
        '''
        

        now=Gcore.common.nowtime()
        row={'UserId':self.uid,
             'GeneralId':generalId,
             'GeneralUserId':friendUserId,
             'McoinNum':mcoinNum,
             'interactTime':now,
             'isGet':0}
        
        re=self.db.insert('tb_interact_general',row)
        
        where='isGet=0 AND GeneralId=%s AND GeneralUserId=%s'%(generalId,friendUserId)
        if self.db.out_field('tb_interact_general','count(1)',where)==1:
            Gcore.push(104,friendUserId,{'InteractGid':generalId})
            
        return re
   
    def InteractJudgement(self, friendUserId, interactType):
        '''
                    互动判断
        @return: 
        '''
        if self.getInteractTime(interactType) < 10:
            if interactType == 1:
                today = datetime.date.today()
                day = time.mktime(today.timetuple())
                if self.modFriend.getVisitTime(friendUserId) > day:                  
                    return False
            return True
        else:
            return False
        
    def InteractAward(self, friendUserId, interactType, optId, param, judge=False):
        '''
                    交互奖励
        @param friendUserId:
        @param interactType:
        @param optId:
        @param param:
        @param judge:互动判断条件，若不需要判断直接传True
        
        @result Judge:是否获得互动奖励
        @result GainAward 实际获得的奖励
        '''
        
        if judge == False:
            judge = self.InteractJudgement(friendUserId, interactType)
        if judge:
            modReward = Gcore.getMod('Reward',self.uid)
            favor = self.modFriend.getFavor(friendUserId)
            gradeCfg = Gcore.getCfg('tb_cfg_friend_grade').values()
            
            gradeCfgList = filter(lambda gradeCfgInfo: gradeCfgInfo['Favor'] <= favor, gradeCfg)
            if gradeCfgList:
                friendGradeCfg = max(gradeCfgList, key=lambda cfg: cfg['FriendGrade'])
                friendGrade = friendGradeCfg['FriendGrade']
            else:
                friendGrade = 1

            interactCfg = Gcore.getCfg('tb_cfg_friend_interact')
            interactCfg = filter(lambda dic:dic['InteractType'] == interactType and dic['FriendGrade'] == friendGrade, interactCfg.values())
            interactCfg = interactCfg[0]
            gainFavor = self.modFriend.addFavor(friendUserId, interactCfg['AddFavor'])
            gainMcoin = modReward.reward(optId, param, 3, 4, interactCfg['GainMcoin'], False) if interactCfg['GainMcoin'] >= 0 else 0
            
            return {'Judge': judge, 'GainAward': {'GainFavor': gainFavor, 'GainMcoin': gainMcoin}}
        else:
            return {'Judge': judge, 'GainAward': {}}
                
def _test():
    '''测试'''
    uid = 43299
    moda=InteractMod(uid)
    print moda.getHaveMcoinGeneralIds()
    #print moda.getInteractTime(3)
    #print moda.InteractJudgement(1011,3)
        
if __name__ == '__main__': 
    _test()      
                
   
    
    
    