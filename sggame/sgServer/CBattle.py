# -*- coding:utf-8 -*-
# author:Lizr
# date:2013年1月8日
# 战斗用类
import time
import copy
import gevent
from sgLib.core import Gcore
from sgMod.subMod.BattleMod import BattleMod


class CBattleManager(object):
    '''战场管理器'''
    Bstorage = {} #所有战斗储存器
    Wstorage = {} #攻城战斗储存器
    Gstorage = {} #比武战斗储存器
    
    #_spawn = gevent.spawn
    def __init__(self):
        ''' '''
        #print self._spawn
        #self._checkBattle_let = self._spawn(self._checkBattle)

    def createWar(self,uid,para={}):
        '''为一个玩家创建一场战役战斗'''
        optId = 90001
        b = CBattle(uid)
        self.Wstorage[uid] = b
        
        return b.createWar(para)
    
    def createRankFight(self,uid,para={}):
        '''为一个玩家创建一场比武战斗'''
        optId = 94001
        b = CBattle(uid)
        self.Gstorage[uid] = b
        return b.createRankFight(para)
    
    def findSiege(self,uid,para={}):
        '''为一个玩家创建攻城战斗'''
        optId = 93001
        if uid in self.Wstorage:
            b = self.Wstorage[uid]
        else:
            b = CBattle(uid)
            self.Wstorage[uid] = b
        return b.findSiege(para)
    
    def startSiege(self,uid,para={}):
        '''玩家开始攻城战斗'''
        optId = 93002
        if not uid in self.Wstorage:
            b = CBattle(uid)
            self.Wstorage[uid] = b
        b = self.Wstorage[uid]
        return b.startSiege(para)
    
    def leftWBattle(self,uid,para={}):
        '''离开攻城战斗 回城'''
        optId = 93003
        if uid in self.Wstorage:
            b = self.Wstorage[uid]
            return b.leftSiege(para)
        else:
            return Gcore.error(optId)
    
    def synBattle(self,uid,para={}):
        '''验证同步'''
        optId = 93004
        #@todo 验证VT,VK的加密方式
        if uid in self.Wstorage:
            self.Wstorage[uid].synBattle(para)
        elif uid in self.Bstorage:
            self.Bstorage[uid].synBattle(para)
        elif uid in self.Gstorage:
            self.Gstorage[uid].synBattle(para)
            
        if para.get('Final'): #最后一次同步才返回
            return Gcore.out(optId)
        

    def endBattle(self,uid,para={}):
        '''立即结束各种战斗'''
        optId = 93009
        if uid in self.Bstorage:
            return self.Bstorage[uid].endBattle(para)
            
        elif uid in self.Wstorage:
            return self.Wstorage[uid].endBattle(para)
        
        elif uid in self.Gstorage:
            return self.Gstorage[uid].endBattle(para)
        else:
            print 'endBattle,%s have not any battle'%uid
    def destoryBattle(self,uid):
        '''删除玩家断线时删除各种战斗'''
        print 'CBattleManager.destoryBattle',uid
        if uid in self.Bstorage:
            self.Bstorage[uid].endBattle()
            del self.Bstorage[uid]
            
        if uid in self.Wstorage:
            self.Wstorage[uid].endBattle()
            del self.Wstorage[uid]
        
        if uid in self.Gstorage:
            self.Gstorage[uid].endBattle()
            del self.Gstorage[uid]


class CBattle(object):
    '''一场战斗  游戏内会涉及到多种战斗模式，竞技场战斗，副本战斗，国战战斗……均可由CBattle派生，保证扩展性。
    '''
    def __init__(self, uid):
        ''' '''
        print '构造CBattle'
        self.uid = uid
        self.mod = BattleMod(uid) #别用Gcore.getMod() 此处不缓存
        self.startTime = time.time() #战斗开始时间
        self.updateTime = time.time() #战斗更新时间
        
    def createWar(self, para):
        '''创建战役战斗
        para:
            'WarId' 剧情战场ID
        '''
        print 'ps createBattle ',para
        optId = 90001
        if 'WarId' not in para:
            return Gcore.error(optId,-90001999) #参考错误
        
        initResult = self.mod.initWar(para['WarId'])
        if initResult == -1:                    
            return Gcore.error(optId,-90001001) #没有兵出场
        elif initResult == -2:
            return Gcore.error(optId,-90001002) #越出每日可打上限
        elif initResult == -3:
            return Gcore.error(optId,-90001003) #战役未达到
        else:
            body = self.mod.getWarInfo()
            if not body:
                return Gcore.error(optId,-90001997) #系统错误
            
            return Gcore.out(optId,body)
    
    def createRankFight(self, para):
        '''创建比武战斗'''
        optId = 94001
        if 'OpUserId' not in para:
            return Gcore.error(optId,-94001999) #参考错误
        
        initResult = self.mod.initRankFight( para.get('OpUserId') )
        if initResult == -1:                    
            return Gcore.error(optId,-94001001) #没有兵出场
        elif initResult == -2:
            return Gcore.error(optId,-94001002) #越出每日可打上限
        elif initResult == -3:
            return Gcore.error(optId,-94001003) #不可与自己比武
        else:
            body = self.mod.getRankInfo()
            if not body:
                return Gcore.error(optId,-90001997) #系统错误
            
            return Gcore.out(optId,body)
        
    def findSiege(self, para):
        '''创建攻城 查找攻城战斗
        @param fromType': 1, #1查找 2复仇 3反抗 4抢夺 (#@todo战斗结束后具体效果还没做)
        @param serverId': 0, #1查找时不需要
        @param targetUserId':  0,  #1查找时不需要
         '''
        print 'ps findSiege ',para
        
        optId = 93001
        initResult = self.mod.initWar(0)
        if initResult<0: #重复@todo优化
            if initResult==-1:
                return Gcore.error(optId,-93001001) #尚未派兵出征,请先布阵
            elif initResult==-2:
                return Gcore.error(optId,-93001008) #剩余行动力不足
            elif initResult==-3:
                return Gcore.error(optId,-93001010) #战役未达到，不可攻打
            elif initResult==-4:
                return Gcore.error(optId,-93001009) #等级未达到，不可攻城
            else:
                return Gcore.error(optId,-93001997) #系统错误
            
        if para.get('serverId') == Gcore.getServerId() and para.get('targetUserId') == self.uid:
            return Gcore.error(optId,-93001002) #不可攻打自己
        
        try:
            body = self.mod.findSiege(para) #查找攻城
        except Exception,e:
            if Gcore.TEST:
                raise
            return Gcore.error(optId,-93001997,{'Exception':str(e)} ) #系统错误
        
        if not isinstance(body, dict):
            return Gcore.error(optId,body) #body 是错误编号 
        return Gcore.out(optId,body)
    
    def startSiege(self, para):
        '''开始城战'''
        optId = 93002
        body = self.mod.startSiege() #开始攻城战斗
        if not isinstance(body, dict):
            return Gcore.error(optId,body) #body 是错误编号 
        return Gcore.out(optId,body)
    
    def leftSiege(self,para={}):
        '''离开攻城战斗,'''
        optId = 93003
        self.mod.leftSiege()
        return Gcore.out(optId)
    
    def synBattle(self,para):
        '''验证同步战斗'''
        optId = 93004
        self.mod.synBattle(para)
        
    def endBattle(self,para={}):
        '''结束攻城战斗'''
        optId = 93009
        print 'Cbattle.endBattle'
        result = self.mod.endBattle(para) #结束攻城战斗
        if not isinstance(result, dict):
            return  # Gcore.error(optId,result) #result 是错误编号  (不用返回)
        body={0:result} #兼容扫荡结构
        return Gcore.out(optId,body)
    
    def checkOpt(self,optId,para):
        ''''''
        
if __name__ == '__main__':
    #43277 忆凡    1011 黄国剑
    uid = 1001
    c = CBattleManager() 
    #----------------战役测试------------------
    print c.createRankFight(uid,{'OpUserId':1005})  
#    print c.endBattle(uid)
#    print c.createWar(uid,{'WarId':101})   
#    p = {
#        'SynA':{'202':0,'201':0},
#        'SynB':{'10002':0},
#        }
#    c.synBattle(uid,p)
#    c.endBattle(uid, {})
#    #----------------攻城测试------------------
#    print c.findSiege(uid,{u'fromType': 3, 'ClientTime': 1371285830, u'targetUserId': 1, u'targetServerId': 1001})   
#    p = {
#        'SynA':{'202':0,'201':0},
#        'SynB':{'10002':0},
#        }
#    c.synBattle(uid,p)
#    c.endBattle(uid, {})
        
        
        
        
        
        
        
        
        
        
        