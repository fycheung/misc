# -*- coding:utf-8 -*-  
# author:lizr
# date:2013-4-24
# 推送 操作

import time
import gevent
#此处不能再引入Gcore，否则会交叉引用

'''推送协议号 101~999说明:
101:通知玩家收到邮件
102:通知玩家任务消息
103:通知玩家成就消息
104:互访奖励消息美酒
105:通知玩家被攻打 (被攻打 Data {'Fighter':'你大爷','FightRestTime':180})
106:通知玩家收到新的好友申请
107:通知玩家VIP已升级 Data {'VipLevel':10}
108:通知玩家主角升级 Data {'UserLevel':10}
109:通知玩家可领取的通用礼包数量
110:(聊天 {'Channel':频道,'Content':内容} Channel:  1世界, 2势力, 3军团, 4私聊, 5系统, 6喇叭, 7公告, 8活动, 9广播)
111:扫荡结果推送
112:通知玩家藩国状态变更,地里资源自动收了,加钱，更新资源建筑状态 ,格式如下:
{'HoldEndTime':藩国结束时间,'GiveRatio':进贡比例,'CoinInfo':{2:库存军资数量,3:库存铜钱数量}, 'BuildingInfo':{资源建筑ID:{'StorageNum':1000,'LastchangedTime':1324242342},... }}
Type 0 解释藩国  1 被设置藩国
113：通知玩家新军团ID


----------------------------------
公告广播 mark @todo
王健 14:11:15
你写一个process_broadcast，定时调用 
王健 14:11:36
每次只处理一定数量的广播请求 
王健 14:11:59
平时调用broadcast，就先把请求缓存起来 
王健 14:12:11
定时器到达以后再统一发送 
王健 14:20:38
万一还有别的公告需要广播，延迟会比较厉害 
王健 14:20:50
这个可以做个优先级处理 

             
'''
class Pusher(object):
    
    def __init__(self):
        self.timeInterval = 0.05 #同个用户每条聊天记录的消息间隔
        self.chatInterval = {} #  {uid:lastChatTime,}
        pass
        
    '''推送类 推送协议号定义:  101~999
    @note 统一通过 Gcore.push() 调用 参数一样
    '''
    def push(self,PushId, Users=0, Data={}, Type=0):
        #print 'Pusher.push',PushId,Users,Data,Type
        from sgLib.core import Gcore
        if Users and not isinstance(Users, (tuple,list)):
            Users = [Users]
        
        try:
            if not Users:
                Users = Gcore.StorageUser.keys()
        except:
            pass
            
        if PushId == 999: #对某个协议号特殊处理 
            if Users:
                for uid in Users:
                    if uid in Gcore.StorageUser:
                        self.send(PushId, uid, {'hi':'world'})            
        else: #统一处理
            if Users:
                for uid in Users:
                    if uid in Gcore.StorageUser:
                        self.send(PushId, uid, Data, Type)
                    else:
                        pass
                        #print 'uid %s not in Gcore.StorageUser'%uid

    def send(self, PushId, uid, Data, Type=0, temp=0):
        sendData = {
                    "opt_id":PushId,
                    "type":Type,
                    "body":Data,
                    }
        
        if PushId==110: #聊天
            t = time.time()
            if uid not in self.chatInterval:
                self.chatInterval[uid] = t
            
            #print '1 self.chatInterval[uid]',self.chatInterval[uid],t
            if self.chatInterval[uid]<=t: #也有可能是负数，还没达到下次可以说话的时间
                #print '%s can say now %s , %s'%(uid,t,temp)
                self.real_send(uid, sendData)  
                self.chatInterval[uid] = t + self.timeInterval #只要有说一次 就累计
                #print '%s can say next time is  %s'%(uid,self.chatInterval[uid])
            else:
                #self.real_send(uid, sendData)  
                dif = self.chatInterval[uid] - t
                gevent.spawn_later(dif, self.real_send, uid, sendData)
                self.chatInterval[uid] += self.timeInterval #只要有说一次 就累计
                #print '%s will say %s later %s at %s'%(uid,dif,temp,self.chatInterval[uid])
            
            Channel = Data.get('Channel')
            from sgLib.core import Gcore
            if Gcore.StorageListener:
                for ckey, v in Gcore.StorageListener.iteritems():
                    ListenChannel = v.get('ListenChannel')
                    if not ListenChannel or ListenChannel==Channel:
                        sendJson = Gcore.common.json_encode(sendData)
                        v['Channel']._send( sendJson )
        else:
            self.real_send(uid, sendData)  

    def real_send(self,uid,sendData):
        from sgLib.core import Gcore
        now = Gcore.common.now()
        t = time.time()
        
        #print ' >>>%s (%s) Pusher send to %s > '%(now,t,uid),sendData
        
        sendJson = Gcore.common.json_encode(sendData)
        try:
            Gcore.StorageUser[uid]['Channel']._send( sendJson )
        except:
            pass

if '__main__' == __name__:
    c = Pusher()
    #c.push(999, 1005, {'hi':'world'})
    #c.send(110,1002,{})
    for i in xrange(10):
        c.send(110,1001,{},0,i)
    #c.send(110,1003,{})
#    for i in xrange(100):
#        c.send(110,1004,{},0,i)
#    c.send(110,1005,{},0,i)
#    c.send(110,1006,{},0,i)
    
    gevent.sleep(100)
