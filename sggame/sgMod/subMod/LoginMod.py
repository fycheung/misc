# -*- coding:utf-8 -*-
# author:Lizr
# date:2013-5-20
# 游戏内部接口,登录模型

import time
from sgLib.core import Gcore
from sgLib.base import Base

class LoginMod(Base):
    """登录模型"""
    def __init__(self, uid):
        '''注释'''
        Base.__init__(self,uid)
        self.uid = uid
        self.logId = None
        #print self.db #数据库连接类

    def test(self):
        '''测试方法'''
    
    def cacheUserData(self, UserId=None, CacheAll=True):
        '''获取用户的信息，用于缓存,登录时调用'''
        
        #获取用户的阵营
        if not UserId:
            UserId =  self.uid
        print 'LoginMod.cacheUserInfo()',UserId
        #UserCamp ,NickName 暂不会改变
        row = self.getUserInfo(['UserCamp', 'NickName','VipLevel','UserLevel','UserIcon','UserType'])
        if not row:
            print 'error: not found user %s'%UserId
            return 
        UserCamp = row['UserCamp']
        NickName = row['NickName']
        VipLevel = row['VipLevel']
        UserLevel = row['UserLevel']
        UserIcon = row['UserIcon']
        UserType = row['UserType']
        
        if CacheAll:
            #获取用户的军团,用户更换军团的时候必须调用Gcore.setUserData(self.uid,{'ClubId':'xx'})
            ClubId = self.db.out_field('tb_club_member', 'ClubId', 'UserId="%s" AND MemberState="%s"' % (UserId, 1))
            
            #玩家未完成的成就
            activeAchieve = Gcore.getMod('Building_home',self.uid).getAchievements()
            activeAchieve = [k for k in activeAchieve if activeAchieve[k]['Finished']==0]
            
            #玩家活跃任务
            activeMission = self.db.out_rows('tb_mission',['MissionId','GetValue'],'UserId=%s AND Status in (1,2)'%UserId)
            activeMission = {k['MissionId']:k for k in activeMission}
            
            #用户升级或Vip升级的时候必须调用Gcore.setUserData(self.uid,{'xxx':'xx'})
            DataDict =  {'UserCamp':UserCamp, 'UserIcon':UserIcon, 'ClubId':ClubId, 'NickName':NickName,
                         'VipLevel':VipLevel,'UserLevel':UserLevel,'UserType':UserType,
                         'ActiveMission':activeMission,'ActiveAchieve':activeAchieve} 
        else: #战斗服务器使用
            DataDict =  {'UserCamp':UserCamp, 'NickName':NickName,'VipLevel':VipLevel,'UserLevel':UserLevel, 'UserIcon':UserIcon} 
        Gcore.setUserData(UserId, DataDict)

    def login(self,loginIp=None,loginMode=None):
        '''登入时调用的方法'''
        now = time.time()
        sql = "UPDATE tb_user SET LastLoginTime=UNIX_TIMESTAMP(),Online=1,LoginTimes=LoginTimes+1 WHERE UserId=%s"%self.uid
        self.db.execute(sql)
        
        #if not self.uid in Gcore.StorageUser: #缓存基础用户信息
        if 1: # fixed by zhoujingjiang
            self.cacheUserData(self.uid)

        UserType = Gcore.getUserData(self.uid,'UserType')   
        #添加登录日志
#         loginLogTB = 'tb_log_login201306'
        loginLogTB = self.tb_log_login()
        data = {'UserId':self.uid,'LoginTime':now,'UserType':UserType,
                'LoginModel':loginMode,'LoginIP':loginIp}
        self.logId = self.db.insert(loginLogTB,data)
        print self.uid,'login get logId:%s at %s'%(self.logId,now)
        
        key = Gcore.redisKey(self.uid)
        Gcore.redisM.hset('sgLogin',key,'1')
        UserLevel = self.getUserLevel()
        modActivity=Gcore.getMod('Activity',self.uid)
        modActivity.signin(0,'')
        if UserLevel>=Gcore.loadCfg(9301).get('FightLevel'):
            row = {}
            row['Online']=1 
            row['UserId']=self.uid
            #Gcore.sendmq(1, 10000, row) #发送到总服更新
            
    
    def logout(self):
        '''登出时调用的方法'''
        now = time.time()
        sql = "UPDATE tb_user SET LastLogoutTime=UNIX_TIMESTAMP(),Online=0 WHERE UserId=%s"%self.uid
        #print sql
        self.db.execute(sql)
        #更新登录日志

        loginLogTB = self.tb_log_login()
        if self.logId:
            loginLogId = self.logId
        else:
            loginLogId = self.db.out_field(loginLogTB,'LogId','UserId=%s ORDER BY LogId DESC LIMIT 0,1'%self.uid)
            
        sql = '''UPDATE %s  
                SET LogoutTime=%s,OnlineTime=%s-LoginTime  
                WHERE LogId=%s'''%(loginLogTB,now,now,loginLogId)
        print self.uid,'logout at %s'%now,sql
        self.db.execute(sql)
        
        Gcore.getMod('Redis', self.uid).offCacheAll() #更新Redis
        
        row = self.getUserInfo(['UserId','UserLevel','UserCamp','ProtectEndTime']) #只是用于查询 不是十分准确
        if row['UserLevel']>=Gcore.loadCfg(9301).get('FightLevel'):
            row['Online']=0 
            #Gcore.sendmq(1, 10000, row) #发送到总服更新
        
        key = Gcore.redisKey(self.uid)
        ProtectEndTime = Gcore.redisM.hget('sgProtect',key)
        if not ProtectEndTime:
            ProtectEndTime = 0
        if row['ProtectEndTime'] > int(ProtectEndTime): #更新保护时间
            Gcore.redisM.hset('sgProtect',key,row['ProtectEndTime'])
        
        modActivity=Gcore.getMod('Activity',self.uid)
        modActivity.refreashTime()#在线奖励活动更新时间 Yew
        
        Gcore.redisM.hdel('sgLogin',key)
    
    
        
        
        

if __name__ == '__main__':
    uid = 1001
    c = LoginMod(uid)
    c.login()
    c.logout()
    
    uid = 1011
    c = LoginMod(uid)
    c.login()
    c.logout()
#     c.login(123,456)
    #print c.getLogTable()
    #c.logout()
    '''
    for uid in Gcore.getDB(0).out_list('tb_user','UserId','UserId=1004'):
        c = LoginMod(uid)
        c.logout()
    '''
    import time
    time.sleep(2)