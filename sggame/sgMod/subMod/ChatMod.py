# -*- coding:utf-8 -*-
# author:
# date:2013-1-
# 游戏内部接口,模型模板

from sgLib.core import Gcore
from sgLib.base import Base
from sgLib.common import filterInput
from sgLib.defined import CFG_CHANNEL

import time
import re

class ChatMod(Base):
    """聊天模型"""
    def __init__(self, uid):
        '''注释'''
        Base.__init__(self,uid)
        self.uid = uid
        self.lastspeaktime = 0
        #print self.db #数据库连接类
        
    def forbiddenChat(self, userId, endTime):
        '''对玩家userId禁言
            userId : 需要禁言的玩家ID
            endTime: 禁言时间长度，单位为秒
        '''
        startTime = int(time.time())
        endTime += startTime
        self.db.insert_update('tb_forbidden_chat', {'UserId': userId, 'ForbiddenStartTime': startTime, 'ForbiddenEndTime': endTime}, {'UserId': userId})
        
    def freeChat(self, userId):
        '''解禁'''
        self.db.delete('tb_forbidden_chat', 'UserId=%s'%userId)
        
    def say(self, optId, channel, content, toName = None):
        #fields = ['NickName', 'VipLevel', 'UserCamp', 'UserLevel']
        #playInfo = self.getUserInfo(fields)
        channel_list = Gcore.loadCfg(CFG_CHANNEL)['Channel']
        if channel in channel_list:
            forbiddenEndTime = self.db.out_field('tb_forbidden_chat', 'ForbiddenEndTime', 'Userid=%s'%self.uid)
            if forbiddenEndTime and forbiddenEndTime > int(time.time()):
                return -8
        playInfo = Gcore.StorageUser.get(self.uid)
        if channel not in (5, 6, 7, 8, 9):
            if self.isLimitTime(self.getUserInfo('UserLevel'), channel):
                return -1   #聊天间隔限制
            msgBody = filterInput(content,i_Min = 1, i_Max = 90, b_Replace = True,b_chat = True)
        else:
            msgBody = content   #管理员发布的消息不进行过滤    

        if not msgBody or int == type(msgBody):
            return -2       #消息未通过验证
        
        if channel == 1:    #世界
            users=[k for k in Gcore.StorageUser if Gcore.StorageUser[k] and Gcore.StorageUser[k].get('Channel')]
            data={'PlayerId':self.uid, 'Channel':channel, 'Content':msgBody, 'PlayerName':playInfo['NickName'], 'VIP':playInfo['VipLevel']}
            
        elif channel == 2:  #势力
            users = [ k for k in Gcore.StorageUser\
                   if Gcore.StorageUser[k] and Gcore.StorageUser[k].get('Channel') and Gcore.StorageUser[k]['UserCamp'] == self.getUserCamp() ]
            data = {'PlayerId':self.uid,'Channel':channel,'Content':msgBody,'PlayerName':playInfo['NickName'],'VIP':playInfo['VipLevel']}
            
        elif channel == 3:  #军团
            if not playInfo['ClubId'] or playInfo['ClubId'] == 0:
                return -5
            users = [ k for k in Gcore.StorageUser\
                   if Gcore.StorageUser[k] and Gcore.StorageUser[k].get('Channel') and Gcore.StorageUser[k]['ClubId'] == playInfo['ClubId'] ]
            data={'PlayerId':self.uid,'Channel':channel,'Content':msgBody,'PlayerName':playInfo['NickName'],'VIP':playInfo['VipLevel']}
            
        elif channel == 4:  #私聊
            if playInfo and toName == playInfo['NickName']:
                return -6
            users = [k for k in Gcore.StorageUser\
                   if Gcore.StorageUser[k] and Gcore.StorageUser[k].get('Channel') and Gcore.StorageUser[k]['NickName'] == toName and k != self.uid]
            if not users:
                return -3
            touserId = users[0]
            users.append(self.uid)
            print 'Users',users
            data = {'PlayerId':self.uid,'Channel':channel,'Content':msgBody,'PlayerName':playInfo['NickName'],'ToName':toName,'ToUserId':touserId}
            
        elif channel == 5:  #系统
            users = [k for k in Gcore.StorageUser if Gcore.StorageUser[k] and Gcore.StorageUser[k].get('Channel')]
            data = {'PlayerId':0,'Channel':channel,'Content':msgBody}
            
        elif channel == 6:  #喇叭
            users = [k for k in Gcore.StorageUser if Gcore.StorageUser[k] and Gcore.StorageUser[k].get('Channel')]
            data = {'PlayerId':self.uid,'Channel':channel,'Content':msgBody,'PlayerName':playInfo['NickName'],'VIP':playInfo['VipLevel']}
            modItem = Gcore.getMod('Item',self.uid)
            re = modItem.useItem(optId, 'say', {}, 801)
            #if not Gcore.TEST and re < 0:
            if re < 0:
                return -4
            
        elif channel == 7:  #GM发布公告
            userType = self.getUserInfo('UserType')
            if userType != 1:
                return -7   #非GM不允许发布公告
            users = [k for k in Gcore.StorageUser if Gcore.StorageUser[k] and Gcore.StorageUser[k].get('Channel')]
            data = {'Channel':channel, 'Content':msgBody}
            
        elif channel == 8:  #活动
            userType = self.getUserInfo('UserType')
            if userType != 1:
                return -7   #非GM不允许发布活动消息
            users = [k for k in Gcore.StorageUser if Gcore.StorageUser[k] and Gcore.StorageUser[k].get('Channel')]
            data = {'Channel':channel, 'Content':msgBody}
            
        elif channel == 9:  #广播
            userType = self.getUserInfo('UserType')
            if userType != 1:
                return -7   #非GM不允许发布广播
            users = [k for k in Gcore.StorageUser if Gcore.StorageUser[k] and Gcore.StorageUser[k].get('Channel')]
            data = {'Channel':channel, 'Content':msgBody}
            
        else:
            return -5

        Gcore.push(110, users, data)
        self.lastspeaktime = time.time()
        
        return data  
        
    def isLimitTime(self, level, channel):
        '''检查是否处于冷却
            channel: 聊天类型(1，世界。2，势力。3，军团。4，私聊。5，系统。6，喇叭)
            level  : 用户等级
        '''
        int2channel = {
            1 :  'World',
            2 :  'Camp',
            3 :  'Clud',
            4 :  'Private',
            5 :  'System',
            6 :  'Suona',
        }
        now = time.time()
        #距离上次发言的时间间隔
        time_interval = now - self.lastspeaktime
        #配置的相应等级，相应频道的时间间隔
        cfg_time_interval = Gcore.getCfg('tb_cfg_chat', level, int2channel[channel])
        #如果配置了该频道的聊天时间间隔，且距离上次聊天的时间间隔小于配置的时间，则不允许聊天
        if cfg_time_interval and time_interval < cfg_time_interval:
            return True
        
        return False
    


        
#def loadDataFrmFile(filePath, sep = None):
#    with open(filePath, 'rb') as fd:
#        return fd.read().decode('utf8').split(sep)
#
#def createWordTree(wordsList):
#    wordTree = [{}, 0]
#
#    for word in wordsList:
#        tree = wordTree[0]
#        for i  in range(0,len(word)):
#            index = ord(word[i])
#
#            if i ==  len(word) - 1: #最后一个字母
#                tree[index] = [{}, 1]
#            else:
#                tree.setdefault(index, [{}, 0])
#                tree = tree[index][0]
#
#    return wordTree
#
#



    
def test():
    uid = 43826
    c = ChatMod(uid)
    c.forbiddenChat(1001, 3600)
#     c.freeChat(1001)


    
if __name__ == '__main__':
    uid = 43368
    c = ChatMod(uid)
#     print c.say(11001, 1, 'Test')
    #Gcore.resetRuntime()
    #uid = 1012
    #c = ChatMod(uid)
    #p={'To':1012,'Type':4,'MsgBody':'毛泽东，大 SB'}
#    re=c.say(1,'hello world')
#    Gcore.runtime()
    #p={'Type':5,'MsgBody':'SB,hello'}
    #print c.say(p)
    #print c.say(1,'hello')
    test()