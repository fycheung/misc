# -*- coding:utf-8 -*-
# author:Yew
# date:2013-5-28
# 游戏内部接口,模型层(被*UI调用)

from sgLib.core import Gcore
from sgLib.base import Base
from sgLib.defined import CFG_ACT_SIGNIN, CFG_ACT_ONLINE_LIMIT
import datetime
import time
import calendar
from sgLib import common

class ActivityMod(Base):
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid

    def getDeadline(self, activityId):
        '''获取礼包截止日期'''
        return 0
        
    def insertGifts(self, activityId, awardId):
        '''
                     添加通用礼包记录
        @param activityId:活动Id，1首冲2签到3成长4活跃5鸿运6在线
        @param awardId:奖励Id，各个活动的奖励配置表的Id
        @param TimeStamp:获奖时间
        '''
        day = self.getDeadline(activityId)
        if day == 0:
            perm = 1
        else:
            perm = 0
        row={'UserId': self.uid,
             'ActivityId': activityId,
             'AwardId': awardId,
             'isGet': 0,
             'CreateTime': time.time(),
             'LimiteTime': day,
             'Perm': perm}
        table = 'tb_activity_gift'
        res = self.db.insert(table, row)
        #by qiudx 属于通用礼包的将推送给前端
        if res:
            activitys = Gcore.getCfg('tb_cfg_act').values()
            actIdList = [activity['ActivityId'] for activity in activitys if activity['GeneralShow'] == 1]
            #print actIdList
            if activityId in actIdList:
                num = self.pushGiftNum()
                Gcore.push(109, self.uid, {'GiftNum': num})
        return res
            
        
    def updateGifts(self, activityId, awardId):
        '''
                    更新通用礼包记录（目前只适用于）
        @param activityId:活动Id，1首冲2签到3成长4活跃5鸿运6在线
        @param awardId:奖励Id，各个活动的奖励配置表的Id
        '''
        row={'isGet': 1}
        where = 'UserId=%s AND AwardId=%s AND ActivityId=%s AND isGet=0 '%(self.uid, awardId, activityId)
        table = 'tb_activity_gift'
        return self.db.update(table, row, where)
        
    def giftList(self, gtList, fields = ['*'], get = 0, TimeStamp = None):
        '''
                     获取通用礼包记录
        @param TimeStamp:
                    -None：不限时间
        @param get:
                0:查询所有
                1:只查询可领取的礼包
        LimiteTime>%s
        '''
        table = 'tb_activity_gift'
        where = 'UserId=%s AND %s '%(self.uid,self.db.inWhere('ActivityId', gtList))
        if get:
            where += ' AND isGet=0 '
        if TimeStamp:
            where += ' AND (LimiteTime>%s OR Perm=1) '%TimeStamp
        where += 'Order By CreateTime ASC'
        return self.db.out_rows(table, fields, where)
    
    def getGiftInfoById(self, giftId):
        '''通过Id获取礼包信息'''
        table = 'tb_activity_gift'
        fields = ['GiftId', 'ActivityId', 'AwardId', 'CreateTime', 'LimiteTime']
        where = 'GiftId=%s AND isGet=0 AND (LimiteTime>%s OR Perm=1) AND UserId=%s'%(giftId, time.time(), self.uid)
        return self.db.out_fields(table, fields, where)
    
    def getGiftInfo(self, giftId):
        '''获取礼包的详细信息'''
        table = 'tb_activity_gift'
        fields = ['GiftId', 'ActivityId', 'AwardId', 'CreateTime', 'LimiteTime', 'isGet', 'IF(LimiteTime>%s OR Perm=1, 1, 0) AS Valid'%time.time()]
        where = 'GiftId=%s AND UserId=%s'%(giftId, self.uid)
        return self.db.out_fields(table, fields, where)
        
    def getSigninLog(self):
        '''获取签到记录'''
        table = 'tb_activity_signin'
        fields = ['Refill', 'SignInDate', 'SignInCount', 'SignInTime']
        where = 'UserId=%s'%self.uid
        re = self.db.out_fields(table, fields, where)
        now = common.nowtime()
        if not re:
            SignInDate = '0000000000000000000000000000000'
            openDay = self.OpenInThisMonth()
            if openDay:
                SignInDate = list(SignInDate)
                SignInDate[openDay-1] = '2'#开服当天标记
                SignInDate = ''.join(SignInDate)
            
            re={'UserId': self.uid,
                  'Refill': 0,
                  'SignInDate': SignInDate,
                  'SignInCount': 0,
                  'SignInTime': now}
            self.db.insert(table, re)
        return re
    
    def updateSigninLog(self, row):
        '''更新签到记录'''
        table = 'tb_activity_signin'
        where = 'UserId=%s'%self.uid
        self.db.update(table, row, where)
    
    def OpenInThisMonth(self):
        '''
                                判断是否是本月开服
                                本月开服则返回开服的具体日
                                否则返回0
        '''
        ServerOpenTime = Gcore.loadCoreCfg('ServerOpenTime')
        ServerOpenTime = ServerOpenTime.split(' ')[0]            #去掉开服日期的时分秒
        ServerOpenTime = map(int, ServerOpenTime.split('-'))     #将开服日期换成整数 
        now = datetime.datetime.now()
        if now.year == ServerOpenTime[0] and now.month == ServerOpenTime[1]:
            return ServerOpenTime[2]
        else:
            return 0
            
    def signin(self, optId, classMethod, date=None):
        '''签到'''
        now = datetime.datetime.now()
        signinLog = self.getSigninLog()
        signedtime = signinLog['SignInTime']
        signedtime = time.localtime(signedtime)
        #隔月清空签到数据和补签次数
        if now.year != signedtime[0] or now.month != signedtime[1]:
            signinLog['SignInDate'] = '0000000000000000000000000000000'
            signinLog['SignInTime'] = common.nowtime()
            signinLog['Refill'] = 0
            self.updateSigninLog(signinLog)

        signInDate = list(signinLog['SignInDate'])
        openDay = self.OpenInThisMonth()        #获取开服日
        cost = 0
        if date is None:
            date = now.day
        if signInDate[date - 1] == '1' or (openDay == date and signInDate[date - 1] == '3'):
            return -1#该日期已签
        if date != now.day:
            if date > now.day or date < openDay:
                return -2#日期错误
            if signinLog['Refill'] >= 5:
                return -3#没有重签次数
            modCoin = Gcore.getMod('Coin', self.uid)
            #signinFee = Gcore.getCfg('tb_cfg_act_signin_fee', signinLog['Refill'] + 1)
            signinFee = Gcore.loadCfg(2303).get( str(signinLog['Refill'] + 1) ) #by Lizr
            
            cost = signinFee
            re = modCoin.PayCoin(optId, 1, cost, classMethod)
            if re < 0:
                return -4#货币不足
            cost = re
            signinLog['Refill'] += 1
        
        #开服当天记录签到记录3，其他签到记录1
        if openDay == date:
            signInDate[date-1] = '3'
        else:
            signInDate[date-1] = '1'
        signinLog['SignInDate'] = ''.join(signInDate)
        signinLog['SignInCount'] += 1
        self.updateSigninLog(signinLog)
        
        count = signinLog['SignInCount'] % 30
        if count != 0:
            awards = Gcore.getCfg('tb_cfg_act_signin_award')
            awardId = filter(lambda dic:dic['Day'] == count, awards.values())[0]['AwardId']
        if count == 0:
            finalAwards = Gcore.loadCfg(CFG_ACT_SIGNIN)['FinalAwardId']
            #awards = finalAwards.split(',')
            awards = finalAwards
            n = ((signinLog['SignInCount']) / 30) % len(awards)
            if signinLog['SignInCount'] % 30 == 0:
                n -= 1
            awardId = int(awards[n])          
        self.insertGifts(2, awardId)
        #发放全勤奖
        daysOfMonth = calendar.monthrange(now.year, now.month)[1]
        if daysOfMonth == now.day:
            fullMonthOnline = True
            if openDay and signInDate[openDay-1] != '3':
                fullMonthOnline = False
            startDay = openDay
            if fullMonthOnline:
                for i in xrange(startDay, daysOfMonth):
                    if '1' != signInDate[i]:
                        fullMonthOnline = False
                        break
            if fullMonthOnline:
                if (daysOfMonth - openDay + 1) < 20:
                    awardId = 2001  #开服至今小于20天的礼包ID
                else:
                    awardId = 3000 + now.month
                self.insertGifts(2, awardId)
        
        return cost

    
    def getLuckLog(self):
        '''获取鸿运抽奖记录'''
        table = 'tb_activity_lucky'
        where = 'UserId=%s'%self.uid
        re = self.db.out_fields(table, '*', where)
        if not re:
            self.db.insert(table, {'UserId': self.uid, 'AwardId': 0, 'Gain': 0,' ChangeTime': time.time()})
            re = self.db.out_fields(table, '*', where)
        return re
    
    def updateLuckLog(self, row):
        '''更新鸿运抽奖记录'''
        table = 'tb_activity_lucky'
        row['ChangeTime'] = time.time()
        where = 'UserId=%s'%self.uid
        self.db.update(table, row, where)
    
    def getOnlineLottery(self):
        '''获取在线奖励记录'''
        table = 'tb_activity_online'
        where = 'UserId=%s'%self.uid
        re = self.db.out_fields(table, '*', where)
        if not re:
            re={'UserId':self.uid,'LastChangeTime':0,'AwardId':0,'LotteryCount':0,'DayOnlineTime':0,'AwardType':3,'GoodsId':1,'GoodsNum':200,'LotteryInfo':'1,1,1'}
            self.db.insert(table, re)
        return re
    
    def updateOnlineLottery(self, row):
        '''更新在线奖励记录'''
        table = 'tb_activity_online'
        where = 'UserId=%s'%self.uid
        self.db.update(table, row, where)
        
    def refreashTime(self):
        '''更新操作时间和当日在线时间（玩家登出时要调用）'''
        now = Gcore.common.nowtime()
        #today=datetime.date.today()
        #t0=time.mktime(today.timetuple())
        
        lastLottery = self.getOnlineLottery()
        lastChangeTime = lastLottery['LastChangeTime']
        
        modPlayer = Gcore.getMod('Player', self.uid)
        lastLoginTime = modPlayer.getUserBaseInfo(['LastLoginTime'])['LastLoginTime']
        
        tt = max(lastChangeTime, lastLoginTime)
        addTime = now - tt
        
        #if lastChangeTime<t0:
        if time.localtime(lastChangeTime)[2] != time.localtime(now)[2]:
            lastLottery['DayOnlineTime'] = 0
            lastLottery['LotteryCount'] = 0
                  
        #timeCfg = Gcore.getCfg('tb_cfg_act_online_limit')
        timeCfg = Gcore.loadCfg(CFG_ACT_ONLINE_LIMIT)
        maxt = 0
        for t in timeCfg.values():
            #maxt += t['NeedTime']#获取最大次数所需要时间
            maxt += t
        lastLottery['DayOnlineTime'] = min(lastLottery['DayOnlineTime'] + addTime, maxt)#最大时间不能超过上限
        lastLottery['LastChangeTime'] = now#更新操作时间
        where = 'UserId=%s'%self.uid
        self.db.update('tb_activity_online', lastLottery, where)
         
    
    def addActiveScore(self, addScore):
        date = Gcore.common.today()
        table = 'tb_activity_active_score'
        where = "UserId=%s AND Date='%s'"%(self.uid, date)
        re = self.db.out_fields(table, ['*'], where)
        if not re:
            re={'UserId': self.uid, 'Score': 0, 'Date': date}
        score = re['Score']
        re['Score'] += addScore
        activeAwards = Gcore.getCfg('tb_cfg_act_active_award').values()
        activeAwards = filter(lambda dic:dic['Score']>score and dic['Score']<=re['Score'], activeAwards)
        for activeAward in activeAwards:
            self.insertGifts(4, activeAward['AwardId'])
        self.db.insert_update(table, re, {'UserId': self.uid})
    
    def actionTrigger(self, optId, data={'ValType':0,'Val':0}):
        '''活跃度触发器'''
        activityStatus = Gcore.getCfg('tb_cfg_act',4,'Status')
        val = data.get('Val')
        if activityStatus==0 and val<1:#活动没开启
            return
            
        #匹配相关活跃度活动
        actions = self.actionFilter(optId, data)
       
        if not actions:
            return
        date = Gcore.common.today()
        addScore = 0

        #更新活跃度
        for action in actions:
            table = 'tb_activity_active'
            where = "UserId=%s AND ActionId=%s AND Date='%s'"%(self.uid, action['ActionId'], date)
            actionLog = self.db.out_fields(table, ['*'], where)
            if not actionLog:
                actionLog={'UserId': self.uid,
                           'ActionId': action['ActionId'],
                           'DayTimes': 0,
                           'Date': date}
                
            if actionLog['DayTimes'] >= action['TimesLimit']:
                continue
                
            actionLog['DayTimes'] += 1
            actionLog['Date'] = date
            row_check = {'UserId': self.uid, 'ActionId': action['ActionId']}
            self.db.insert_update(table, actionLog, row_check)
            addScore += action['RewardValue']
        self.addActiveScore(addScore)
        
    def actionFilter(self, optId, data):
        '''
        :活跃活动过滤
        @param action:活动
        @param data:数据
        '''
        actionCfg = Gcore.getCfg('tb_cfg_act_active_action').values()
        actions = []
        for ac in actionCfg:
            optIds = ac.get('OptId','')
            if optIds is None:
                continue
            optIds = optIds.strip().split(',')
            if (str(optId) in optIds) and (ac['ParamA']==0 or ac['ParamA']==data['ValType']):
                flag = True
                mt = ac.get('MissionType')
                
                if mt==92:#扫荡
                    if data.get('BattleType')==1 and data.get('FromType')==1:
                        flag = True
                    else:
                        flag = False
                        
                elif mt==96:#掠夺
                    if data.get('BattleType')==2 and data.get('FromType')==1:
                        flag = True
                    else:
                        flag = False
                    
                if flag:
                    actions.append(ac)
                    
        return actions
    
    def getActiveLog(self, fields=['*']):
        date = Gcore.common.today()
        table = 'tb_activity_active'
        where = "UserId=%s AND Date='%s' AND DayTimes>0 Order By ActionId"%(self.uid, date)
        return self.db.out_rows(table, fields, where)
    
    def getActiveScore(self):
        date = Gcore.common.today()
        table = 'tb_activity_active_score'
        where = "UserId=%s AND Date='%s'"%(self.uid, date)
        return self.db.out_field(table,'Score', where)
    
    def growUpAward(self, nlevel, olevel):
        '''成长奖励（主角升级时调用）'''
        growUpAwards = Gcore.getCfg('tb_cfg_act_grow_award').values()
        growUpAwards = filter(lambda dic:dic['PlayerLevel'] <= nlevel and dic['PlayerLevel'] > olevel, growUpAwards)
        for award in growUpAwards:
            awardId = award['AwardId']
            self.insertGifts(3, awardId)
    
#     def insertGrowReward(self):
#         '''添加成长奖励（玩家升级时候调用） 已弃用'''   
#         growAwardCfg=Gcore.getCfg('tb_cfg_act_grow_award').values()
#         growAward=filter(lambda dic:dic['PlayerLevel'] ==self.uid, growAwardCfg)
#         self.insertGifts(3, growAward['AwardId'])
    
#------------------------------------------------------------------------------ 
# add by zhanggh 6.9

    def getGift(self, actId, awId, fields=['*']):
        '''通过活动Id，奖励ID查询礼包'''
        table = 'tb_activity_gift'
        where = 'UserId=%s AND ActivityId=%s AND AwardId=%s'%(self.uid, actId, awId)
        return self.db.out_fields(table, fields, where)

#------------------------------------------------------------------------------
    
    def pushGiftNum(self):
        activitys = Gcore.getCfg('tb_cfg_act').values()
        activityId = [activity['ActivityId'] for activity in activitys if activity['GeneralShow'] == 1]
        #print activityId
        now = time.time()
        fields = ['GiftId','ActivityId','AwardId','CreateTime','LimiteTime','Perm']
        giftList = self.giftList(activityId, fields, get = 1, TimeStamp = now)
        return len(giftList)


def test():
    uid = 43537
    a = ActivityMod(uid)
    for i in range(1, 29):
        a.insertGifts(2, i)
        
def test2():
    uid = 43537
    a = ActivityMod(uid)
    print a.getGiftMember(2,3)

def test3():
    uid = 43306
    a = ActivityMod(uid)
    print a.OpenInThisMonth()
    
if __name__ == '__main__':
    '''测试'''
    test3()
    uid=43522
    f=ActivityMod(uid)
    #f.insertGifts(3, 15)
    #res = f.getSigninLog()
    #print '================='
    #print res
    #print '================='
#    print f.countGift()
    f.signin(1,'')
#     print f.signin(1,'test')
#    print f.growUpAward(11111)
    #f.maxFavorss()
    #now=datetime.date.today() 
    #f.signin(optId=0,classMethod='sdsd')
    #f.actionTrigger(15021,{'ValType':1,'Val':1})
    #Gcore.runtime()
#    print f.getActiveLog()
#    f.insertGifts(2,2001)
#    for i in range(3001,3013):
#        print i
#        print f.insertGifts(2,i)
    
    #f.countDeleteFriend()
    #print s
#    print f.refreashTime()
#    print Gcore.getCfg('tb_cfg_act',4,'Status')

