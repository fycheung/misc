# -*- coding:utf-8 -*-
# author: Lizr
# date:2013-7-10
# 系统公告模型

from sgLib.core import Gcore
from sgLib.base import Base
import time
import gevent

intervalTime = 10 #检查间隔
refreshTime = 180 #刷新公告时间
if Gcore.TEST:
    refreshTime = 30

class SystemNotice():
    """系统模型，暂只用于系统自动发 公告广播等消息"""
    def __init__(self):
        '''注释'''
        self.db = Gcore.getDB()
        self.dictNotice = {}

    def test(self):
        '''测试方法'''
        
    def loop(self):
        '''循环执行'''
        print 'SystemNotice.loop()'
        sumTime = 0
        self.dictNotice = self._refreshNotice() #获取公告
        while True:
            self.pubNotice()
            gevent.sleep(10)
            sumTime += 10
            if sumTime > 180:
                sumTime = 0
                self.dictNotice = self._refreshNotice() #获取公告
                
    def pubNotice(self):
        '''发布消息'''
        #print 'Stop pubNotice'
        #return  # 暂停发送
        delKeys = []
        curTime = time.time()
        for k,row in self.dictNotice.iteritems():
            if row['NoticeCycle'] == 0: #不是循环 
                Channel = self._transToChannel(row['NoticeType'])
                Gcore.push(110,[],{'Channel': Channel, 'Content':row['NoticeContent'], 'Color':row.get('NoticeColor')}) 
                delKeys.append(k)
            else: #是循环的
                if row['NextSentTime']<=curTime:
                    #print '>>>send',row
                    Channel = self._transToChannel(row['NoticeType'])
                    Gcore.push(110,[],{'Channel': Channel, 'Content':row['NoticeContent'], 'Color':row.get('NoticeColor')}) 
                    self.dictNotice[k]['NextSentTime'] =  curTime + row['NoticeTimeInterval']*60  #分钟
        
        for dKey in delKeys:
            self.dictNotice.pop(dKey,None) #不是循环的从缓存中清除
            self.db.update('tb_notice',{'NoticeSent':1},'NoticeId=%s'%dKey)
            #print 'in pubNotice',self.db.sql
        #print 'end pubNotice()'
            
    def _refreshNotice(self):
        '''获得要发送的消息,每隔一段时间更新一次'''
        #print '_refreshNotice()'
        where = "NoticeType>0 AND NoticeStartTime<=UNIX_TIMESTAMP() AND NoticeEndTime>=UNIX_TIMESTAMP() AND (NoticeCycle='1' OR (NoticeCycle='0' AND NoticeSent='0'))"
        rows = self.db.out_rows('tb_notice','*',where)

        newNotice = {}
        for row in rows:
            NoticeId = row['NoticeId']
            if NoticeId in self.dictNotice:
                row['NextSentTime'] = self.dictNotice[NoticeId]['NextSentTime'] #如果是旧记录 保持时间间隔
            else:
                row['NextSentTime'] = 0 #下次需要发送的时候
                
            newNotice[row['NoticeId']] = row
        #Gcore.printd(newNotice)
        return newNotice
            
    def _transToChannel(self,NoticeType):
        '''将公告类型转换为聊天类型
        1:公告, 2:活动, 3:广播
        7:公告, 8:活动, 9:广播
        '''
        if NoticeType==1:
            return 7
        elif NoticeType==2:
            return 8
        elif NoticeType==3:
            return 9
        else:
            return 0

if __name__ == '__main__':
    c = SystemNotice()
    c.test()
    c.loop()
    #c._getNotice()