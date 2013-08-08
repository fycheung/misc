# -*- coding:utf-8 -*-
# author:Yew
# date:2013-3-28
# 游戏内部接口,模型层(被*UI调用)

from sgLib.core import Gcore
from sgLib.base import Base
import datetime
import time
class FriendMod(Base):
    def __init__(self,uid):
        Base.__init__(self,uid)
        self.uid=uid
    
    def addFavor(self,friendUserId,gainFavor):
        '''
                    添加好感度
        @return >=0返回实际增加的好感度
                -1对方不是好友
        '''
        favorCfg=Gcore.getCfg('tb_cfg_friend_grade')
        maxkey=max(favorCfg.iterkeys(),key=lambda k:favorCfg[k])
        maxFavor=favorCfg[maxkey]['Favor']
        favor=self.getFavor(friendUserId)
        if not favor and favor != 0:
            return -1
        newFavor=min(favor+gainFavor,maxFavor)
        self.updateFavor(friendUserId,newFavor)
        Gcore.getMod('Event',self.uid).favorGet(friendUserId,gainFavor)#获得好感度事件
        return newFavor-favor
    
    def getFriends(self):
        '''获取玩家的好友 by Lijs'''
        
        fields=['u.UserId','NickName','UserIcon','f.Favor','u.UserLevel',
                'VipLevel','IF(u.LastLoginTime>u.LastLogoutTime,1,0) AS Online',
                '(UNIX_TIMESTAMP()-u.LastLogoutTime)/86400 AS Offlinedays']
        where='f.UserId=%s AND f.FriendStatus=2 AND f.FriendUserId=u.UserId ORDER By Online desc,NickName'%(self.uid)
        return self.db.out_rows('tb_user u,tb_friend f',fields,where)


    def getFriendList(self, fields = None):
        '''获取所有朋友'''
        
        if not fields:
            fields = ['UserId', 'NickName', 'UserIcon', 'UserLevel'\
                    ,'UserHonour', 'LastLoginTime', 'LastLogoutTime', 'Favor']
        fields.append('IF(u.LastLoginTime > u.LastLogoutTime, 1, 0) AS IsOnline')
        for i in xrange(len(fields)):
            if 'UserId' == fields[i]:
                fields[i] = 'u.UserId'
                        
        where='f.UserId=%s AND f.FriendStatus=2\
               AND f.FriendUserId=u.UserId ORDER By IsOnline DESC, Favor DESC, CONVERT(NickName USING gbk)'%self.uid
        return self.db.out_rows('tb_user u, tb_friend f', fields, where)
    
    def getApplyList(self):
        '''获取待审查信息'''
        
        fields = ['f.UserId', 'NickName', 'UserIcon', 'UserLevel',\
                'LastChangeTime', 'LastLoginTime', 'LastLogoutTime', 'VipLevel', 'IF(u.LastLoginTime>u.LastLogoutTime,1,0) AS IsOnline']
        t = Gcore.common.nowtime() - 3*24*60*60#3天前的时间戳
        where = 'f.FriendUserId=%s AND f.FriendStatus=1\
               AND f.UserId=u.UserId AND LastChangeTime>=%s ORDER By IsOnline DESC, LastChangeTime ASC'%(self.uid, t)
        
        return self.db.out_rows('tb_user u, tb_friend f', fields, where)

    def getUserByRand(self, userCamp):
        '''随机查找18个用户'''
        if not userCamp:
            userCamp = self.getUserCamp()
        #三天内申请过的不再出现在随机列表中
        t=Gcore.common.nowtime() - 3*24*60*60#3天前的时间戳
        applyedList = self.db.out_list('tb_friend', 'FriendUserId', 'UserId=%s and FriendStatus=1 and LastChangeTime>=%s'%(self.uid, t))
        applyedList = map(str, applyedList)
        #已成为好友的也不再出现在随机列表中
        friendList = self.db.out_list('tb_friend', 'FriendUserId', 'UserId=%s and FriendStatus=2'%self.uid)
        applyedList += map(str, friendList)
        #对方申请过成为玩家好友的也不再出现
        uapplyedList = self.db.out_list('tb_friend', 'UserId', 'FriendUserId=%s and FriendStatus=1 and LastChangeTime>=%s'%(self.uid, t))
        applyedList += map(str, uapplyedList)
        if applyedList:
            applyedStr = '(' + str.join(',', applyedList) + ',' + str(self.uid) + ')'
            where = 'UserCamp=%s AND UserId not in %s'%(userCamp, applyedStr)
        else:
            where = 'UserCamp=%s AND UserId <> %s'%(userCamp, self.uid)
        #print applyedStr
        table = 'tb_user'
        fields=['UserId','UserIcon','NickName','UserLevel','VipLevel']
        return self.db.out_rand(table, fields, where, 18)
    
    def refuseApply(self, userIds, friendIds, tm):
        '''拒绝好友申请'''
        if not userIds or not friendIds:
            return 0
        tm = tm if tm else int(time.time())
        if type(userIds) not in (tuple, list):
            userIds = [userIds]
        userIds = map(str, userIds)
        where = ' UserId = ' + 'OR UserId = '.join(userIds)
            
        if type(friendIds) not in (tuple, list):
            friendIds = [friendIds]
        friendIds = map(str, friendIds)
        where += ' AND FriendUserId = ' + 'OR FriendUserId = '.join(friendIds)
        
        where += ' AND FriendStatus=1'
        row = {'FriendStatus': 0, 'LastChangeTime': tm}
        return self.db.update('tb_friend', row, where)
    
    def insFriendShip(self, userId, friendUserId, FriendStatus = 1, isPush = False):
        '''添加FriendShipStatus为1的好友关系，如果已存在，则更新 相当于重新申请'''
        
        row = {'UserId': userId, 'FriendUserId': friendUserId, 'Favor': 0, 'FriendStatus': FriendStatus
              ,'VisitTime': 0, 'LastChangeTime': int(time.time())}
        row_check = {'UserId': userId, 'FriendUserId': friendUserId}
        
        if isPush:
            Gcore.push(106,friendUserId)
        
        return self.db.insert_update('tb_friend', row, row_check)
    
    def getLastDeleteTime(self):
        table='tb_friend'
        where="UserId=%s AND FriendStatus=3 ORDER BY LastChangeTime desc limit 1"%(self.uid)
        return self.db.out_field(table,'LastChangeTime',where)
    

    def updateFriendShip(self,userIds,friendUserIds,friendStatus,changeTime=None):
        '''
                    更新好友关系
        @param userId:关系的主用户
        @param friendUserId:关系的朋友用户
        @param friendStatus:要更新的关系状态
        '''
        table='tb_friend'
        if changeTime is None:
            changeTime=int(time.time())
        field='FriendStatus=%s,LastChangeTime=%s'%(friendStatus,changeTime)
        if isinstance(friendUserIds,(tuple,list)):
            friendUserIds = map(str, friendUserIds)
            where = "FriendUserId IN ("+str.join(",",friendUserIds)+") AND UserId='%s'"%(userIds)
        elif isinstance(userIds,(tuple,list)):
            userIds = map(str, userIds)
            where = "UserId IN ("+str.join(",",userIds)+") AND FriendUserId='%s'"%(friendUserIds)
        else:
            where='UserId=%s AND FriendUserId=%s'%(userIds,friendUserIds)
        sql='UPDATE '+table+' SET '+field+' WHERE '+where
        
        result = self.db.execute(sql)
        return result
    
    def countApply(self):
        '''
                    统计未处理好友申请个数
        '''
        t=Gcore.common.nowtime()-3*24*60*60
        where='FriendUserId=%s AND tb_friend.FriendStatus=1 AND LastChangeTime>=%s'%(self.uid,t)
        return self.db.out_field('tb_friend','count(1)',where)


    def countDeleteFriend(self):
        '''
                    统计当日已经删除的朋友个数
        '''
        today=datetime.date.today()
        t=time.mktime(today.timetuple())
        where='tb_friend.UserId=%s AND tb_friend.FriendStatus=3 AND LastChangeTime>%s'%(self.uid,t)
        return self.db.out_field('tb_friend','count(1)',where)
    
    def countFriend(self, friendStatus, online = False):
        '''
                    统计朋友个数
        @param online:是否查找在线的,True为查找在线,False查找所有
        @param friendStatus：2为已是好友的关系
        '''
        
        if online:
            where = 'tb_friend.UserId=%s AND FriendStatus=%s AND Online=1 AND tb_friend.FriendUserId = tb_user.UserId'%(self.uid, friendStatus)    
        else:
            where = 'tb_friend.UserId=%s AND tb_friend.FriendStatus=%s AND tb_friend.FriendUserId = tb_user.UserId'%(self.uid, friendStatus)
      
        return self.db.out_field('tb_friend,tb_user', 'count(tb_friend.UserId)', where)
    
    
    def getFavor(self,friendUserId):
        '''
                    获取好感度
        '''
        where="UserId=%s AND FriendUserId='%s' AND FriendStatus=2"%(self.uid,friendUserId)
        return self.db.out_field('tb_friend','Favor',where)
    
    def getVisitTime(self,friendUserId):
        '''
                    获得访问历史
        '''
        where='UserId=%s AND FriendUserId=%s AND FriendStatus=2'%(self.uid,friendUserId)
        result= self.db.out_field('tb_friend','VisitTime',where)
        return result

    def getFriendStatus(self,friendUserId):
        '''获得好友关系状态'''
        where='UserId=%s AND FriendUserId=%s'%(self.uid,friendUserId)
        return self.db.out_field('tb_friend','FriendStatus',where)
    

    def validateFriend(self,friendUserId):
        '''判断是否为好友'''
        where='UserId=%s and FriendUserId=%s and FriendStatus=2'%(self.uid,friendUserId)
        res=self.db.out_field('tb_friend','count(1)',where)
        return True if res else False
   
    
    def updateFavor(self,friendUserId,newFavor):
        '''更新好感度'''
        table='tb_friend'
        row={'Favor':newFavor}
        where='UserId=%s AND FriendUserId=%s AND FriendStatus=2'%(self.uid,friendUserId)   
        self.db.update(table,row,where)
        where='UserId=%s AND FriendUserId=%s AND FriendStatus=2'%(friendUserId,self.uid)   
        self.db.update(table,row,where)
    
    def updateVisitTime(self,friendUserId,visitTime=None):
        '''更新访问历史'''
        if visitTime is None:
            visitTime=time.time()
        table='tb_friend'
        row={'VisitTime':visitTime}
        where='UserId=%s AND FriendUserId=%s AND FriendStatus=2'%(self.uid,friendUserId)
        return self.db.update(table,row,where)



    def clearFriendShip(self,friendStatus=1):
        '''
                    清理好友关系
        @param friendStatus:要清理的好友状态,0为已拒绝的,1为未验证,3为删除的
        '''
        now=datetime.datetime.now()

        if friendStatus==0:
            where='FriendStatus=0'
        if friendStatus==1:
            d=now+datetime.timedelta(days=-3)
            day=time.mktime(d.timetuple())
            where='FriendStatus=1 AND LastChangeTime<%s'%day
        if friendStatus==3:
            d=now+datetime.timedelta(days=-1)
            day=time.mktime(d.timetuple())
            where='FriendStatus=3 AND LastChangeTime<%s'%day
        
        self.db.delete('tb_friend',where)
        #删除好友关系
        
    def getFriendShipInfo(self,userId,friendUserId,fields=['*']):
        table='tb_friend'
        where='UserId=%s AND FriendUserId=%s'%(userId,friendUserId)
        return self.db.out_fields(table,fields,where)
    
    def getUserByNickName(self, nickName):
        '''通过昵称查找好友'''
        where="NickName='%s'"%nickName
        return self.db.out_fields('tb_user', ['UserId','UserCamp'], where)
    
    def validateUser(self, userId):
        '''判断用户是否存在'''
        return self.db.out_field('tb_user', 'count(1)', "UserId=%s"%userId)
    
    def getBuildingCount(self, friendUserId):
        '''获取建筑个数'''
        tb_building = self.tb_building(friendUserId)
        return self.db.out_field(tb_building, 'count(1)', "UserId=%s"%friendUserId)
    

def test():
    uid = 43508
    f = FriendMod(uid)
    t=Gcore.common.nowtime() - 3*24*60*60#3天前的时间戳
    applist = f.db.out_list('tb_friend', 'FriendUserId', 'UserId=%s and FriendStatus=1 and LastChangeTime>=%s'%(uid, t))
    randlist = f.getUserByRand(f.getUserCamp())
    print '=============================='
    print 'applist:'
    print applist
    print '=============================='
    print 'randlist:'
    rl = []
    for r in randlist:
        rl.append(r['UserId'])
    print rl
    print '=============================='
    for fid in applist:
        if fid in rl:
            print 'failed'  

    
if __name__ == '__main__':
    #uid=1012
    #uid = 1005
    #f=FriendMod(uid)
    #lists = f.getFriendList()
    #for i in lists:
    #    print i
    test()
    #print f.validateUser(99999)
    #f.maxFavorss()
    #print f.validateUser(123213)
    #print f.getLastDeleteTime()
    #f.countDeleteFriend()
    #print s
    #print f.getFriendShipInfo(1012, 1011)
    #for i in range(1001,1012):
    #    print f.getBuildingCount(i)
    


    
        
