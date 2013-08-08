# -*- coding:utf-8 -*-
# author:Yew
# date:2013-2-5
#模块说明

import sys
import random
import datetime

from sgLib import common
from sgLib.core import Gcore, inspector
from sgLib.defined import CFG_ACT_LUCKY
from sgLib.defined import CFG_ACT_SIGNIN
from sgLib.defined import CFG_ACT_ONLINE_LIMIT


class ActivityUI(object):
    def __init__(self, uid):
        self.mod = Gcore.getMod('Activity', uid)
        self.uid = uid

    def GetActivitiesUI(self, param={}):
        '''返回参数1首次充值2签到3成长奖励4活跃度礼包5鸿运当头6在线奖励'''
        optId = 23001
        activities = Gcore.getCfg('tb_cfg_act')
        data = {}
        acts = []
        for act in activities:
            if activities[act]['Status'] == 1:
                actId = activities[act]['ActivityId']
                if actId == 1:#首冲活动
                    playerMod = Gcore.getMod('Player',self.uid)
                    vipTotalPay = playerMod.getUserBaseInfo(['VipTotalPay']).get('VipTotalPay')
                    if vipTotalPay:
                        giftState = self.mod.getGift(1, 0, ['isGet']).get('isGet')
                        data['Recharged'] = 1 if giftState == 0 else 0
                    else:
                        data['Recharged'] = 1 #新号要显示首冲活动
                        
                    if not data['Recharged']: #1表示可以领首冲礼包或者新号显示首冲活动,0表示不显示
                        continue
                elif actId == 5:
                    luckyLog = self.mod.getLuckLog()
                    luckyLog['AwardId'] += 1
                    goodLuckCfg = Gcore.getCfg('tb_cfg_act_lucky_award', luckyLog['AwardId'])
                    if not goodLuckCfg:
                        continue
                acts.append(actId)
        data['Activities'] = acts
        return Gcore.out(optId, data)
        
    @inspector(23002,)
    def GiftList(self, param={}):
        '''获取通用礼包记录 by zhanggh 6.9
        @param GT:2签到3成长4活跃    不传：所有
        '''
        optId = 23002
        TimeStamp = param.get('ClientTime')
        gt = param.get('GT')
        fields = ['GiftId', 'ActivityId', 'AwardId', 'CreateTime', 'LimiteTime', 'Perm']
        if gt:
            gtList = [gt]
            giftList = self.mod.giftList(gtList, fields, 0, TimeStamp)
        else:#通用礼包列表
            gtList = [act['ActivityId'] for act in Gcore.getCfg('tb_cfg_act').values() if act['Status']==1 and act['GeneralShow']==1]
            giftList = self.mod.giftList(gtList, fields, 1, TimeStamp)
            
        giftList = common.list2dict(giftList)
        return Gcore.out(optId, {'GL': giftList})
    
    @inspector(23003,['GiftId'])    
    def GetGift(self, param={}):
        '''领取通用礼包奖励'''
        optId = 23003
        giftId = param['GiftId']
        
        row = {"isGet": 1}
        where = "GiftId=%s AND UserId=%s AND isGet=0"%(giftId, self.uid)
        affectedrows = self.mod.db.update('tb_activity_gift', row, where)
        if not affectedrows:
            return Gcore.error(optId, -23003002)#礼包已经领取
        
        giftInfo = self.mod.getGiftInfo(giftId)
        if not giftInfo:
            return Gcore.error(optId, -23003001)#礼包领取条件不符
        elif not giftInfo.get('Valid', 0):
            return Gcore.error(optId, -23003003)#礼包已过期
        
        activityId = giftInfo['ActivityId']
        awardId = giftInfo['AwardId']
        if activityId == 2:
            table = 'tb_cfg_act_signin_award'
        elif activityId == 3:
            table = 'tb_cfg_act_grow_award'
        elif activityId == 4:
            table = 'tb_cfg_act_active_award'
        else:
            return  Gcore.error(optId, -23003999)
        
        award = Gcore.getCfg(table, awardId)
        modReward = Gcore.getMod('Reward', self.uid)
        gain = []
        emailed = 0
        for i in xrange(1, 4):
            g = {}
            g['ActivityId'] = activityId
            g['AwardType'] = award['AwardType%s'%i]
            g['GoodsId'] = award['GoodsId%s'%i]
            g['Gain'] = modReward.reward(optId, param, award['AwardType%s'%i], award['GoodsId%s'%i], award['GoodsNum%s'%i])
            if award['AwardType%s'%i] == 1 and (g['Gain'] == 0 or len(g['Gain']) != award['GoodsNum%s'%i]):
                emailed = 1
            elif award['AwardType%s'%i] == 2 and (g['Gain'] == 0 or g['Gain'][0] != award['GoodsNum%s'%i]):
                emailed = 1
            if award['AwardType%s'%i] != 3 and g['Gain'] != 0:
                g['Gain'] = g['Gain'][0]
            gain.append(g)
        #self.mod.updateGifts(activityId, awardId)
        return Gcore.out(optId, {'Awards': gain, 'GiftId': giftId, 'Emailed': emailed})
        
        
    
    def GetRechargeUI(self, param={}):
        '''获取首冲奖励信息（待定）'''
        optId = 23004
        awards = Gcore.getCfg('tb_cfg_act_recharge_award').values()
        return Gcore.out(optId, {'Awards': awards})
    
    def GetRechargeReward(self, param={}):
        '''领取首冲奖励'''
        optId = 23005
        #先设置礼包为已领取状态，再给予物品，防止并发
        affectedrows = self.mod.updateGifts(1, 0)
        if not affectedrows:
            return Gcore.error(optId, -23005001)#不能领取
        
        modReward = Gcore.getMod('Reward', self.uid)
        awards = Gcore.getCfg('tb_cfg_act_recharge_award').values()
        eIds = []
        for award in awards:
            awt = award['AwardType']   
            reInfo = modReward.reward(optId, param, awt, award['GoodsId'], award['GoodsNum'])
#             reInfo = 23
            if awt and isinstance(reInfo, list or tuple):
                eIds += reInfo
        return Gcore.out(optId, {'Awards': awards, 'EIDS': eIds})
           
    def GetSignInLog(self, param={}):
        '''获取签到日志'''
        optId = 23006
        data = self.mod.getSigninLog()
        a = list(data['SignInDate'])
        data['SignInDate'] = ','.join(a)
        #获取全勤奖励信息
        awards = Gcore.getCfg('tb_cfg_act_signin_award').values()
        fullWorkAwards = filter(lambda dic:dic['AwardId']>=3000 and dic['AwardId']<4000, awards)
        now = datetime.datetime.now()
        data['FullWorkAwardId'] = fullWorkAwards[now.month-1]['AwardId']
        #获取周期奖励信息
        finalAwards = Gcore.loadCfg(CFG_ACT_SIGNIN)['FinalAwardId']
        #awards = finalAwards.split(',')
        awards = finalAwards
        signCount = data['SignInCount']
        n = signCount / 30 % len(awards)
        if signCount % 30 == 0:
            n -= 1
        awardId = int(awards[n])
        data['FinalAwardId'] = awardId
        signCount = signCount % 30
        data['SignInDays'] = signCount if signCount else 30 #用于前台显示当前周期内的天数，30天一周期
        data['Refill'] = 5 - data['Refill']
        return Gcore.out(optId, data)
    
    @inspector(23007,['Date']) 
    def SignIn(self, param={}):
        '''补签 操作'''
        optId = 23007
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        date = param['Date']
        re = self.mod.signin(optId, classMethod, date)
        if re == -1:
            return Gcore.error(optId, -23007001)#该日期已签
        if re == -2:
            return Gcore.error(optId, -23007002)#日期错误
        if re == -3:
            return Gcore.error(optId, -23007003)#没有重签次数
        if re == -4:
            return Gcore.error(optId, -23007004)#货币不足
        
        return Gcore.out(optId, {'Cost': re})
    
    
    def Lucky(self, param={}):
        '''鸿运当头活动抽奖'''
        optId = 23008
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        luckyLog = self.mod.getLuckLog()
        luckyLog['AwardId'] += 1
        
        goodLuckCfg = Gcore.getCfg('tb_cfg_act_lucky_award', luckyLog['AwardId'])
        if not goodLuckCfg:
            return Gcore.error(optId, -23008001)#抽奖次数已到最大
        modCoin = Gcore.getMod('Coin',self.uid)
        re = modCoin.PayCoin(optId, 1, goodLuckCfg['Pay'], classMethod, param)
        if re == -2:
            return Gcore.error(optId, -23008002)#不够黄金
        elif re<0:
            return Gcore.error(optId, -23008999)

        ratios = Gcore.loadCfg(CFG_ACT_LUCKY)
        ranges = []
        for i in range(1, 5):
            ranges.append({'Max':i, 'Ratio':ratios['Ratio%s'%i]})
            
        maxLevel = common.Choice(ranges)['Max']-1   #配置表不太一致
        maxCoin = goodLuckCfg['Max%s'%maxLevel]
        if maxLevel == 0:
            minCoin = goodLuckCfg['Pay']
        else:
            minCoin = goodLuckCfg['Max%s'%(maxLevel-1)]
#         minLevel = maxLevel-1
#         gainCoin = random.randint(goodLuckCfg['Max%s'%minLevel], goodLuckCfg['Max%s'%maxLevel])
        gainCoin = random.randint(minCoin, maxCoin)
        modCoin.GainCoin(optId, 1, gainCoin, classMethod, param)
        luckyLog['Gain'] = gainCoin
        self.mod.updateLuckLog(luckyLog)
        luckyLog = self._getLuckLog()
        myCoin = modCoin.getCoinNum(1)
        luckyLog['MyCoin'] = myCoin
        return Gcore.out(optId, luckyLog)
    
    def _getLuckLog(self):
        luckyLog = self.mod.getLuckLog()
        awardId = luckyLog['AwardId']
        awardCfg = Gcore.getCfg('tb_cfg_act_lucky_award')
        less = len(awardCfg) - awardId
        data = {}
        if less == 0:
            data['Max'] = 0
            data['Pay'] = 0
        else:
            awardCfg = awardCfg[awardId+1]
            data['Max'] = awardCfg['Max3']
            data['Pay'] = awardCfg['Pay']
        
        
        data['Less'] = less
        data['LastGain'] = luckyLog['Gain']
        return data
    
    def GetLuckyLog(self, param={}):
        '''获取鸿运当头活动抽奖记录'''
        optId = 23009
        data = self._getLuckLog()
        return Gcore.out(optId, data)
    
    def ShowLottory(self, param={}):
        '''显示在线奖励信息'''
        optId = 23010
        self.mod.refreashTime()#更新操作时间
        
        lastLottery = self.mod.getOnlineLottery()
        
        data = {}
        data['LotteryCount'] = lastLottery['LotteryCount']
        data['DayOnlineTime'] = lastLottery['DayOnlineTime']
        data['LotteryInfo'] = lastLottery['LotteryInfo']
        data['AwardType'] = lastLottery['AwardType']
        data['GoodsId'] = lastLottery['GoodsId']
        data['GoodsNum'] = lastLottery['GoodsNum']
        
        return Gcore.out(optId, data)
        
    
    def OnlineLottory(self, param={}):
        '''在线奖励抽奖'''
        optId = 23011
        self.mod.refreashTime()#更新操作时间
        lastLottery = self.mod.getOnlineLottery()
        #获取可抽奖次数（待）
        #timeCfg = Gcore.getCfg('tb_cfg_act_online_limit')
        timeCfg = Gcore.loadCfg(CFG_ACT_ONLINE_LIMIT)
        dt = lastLottery['DayOnlineTime']
        less = 0
        lottoryNum = len(timeCfg.keys())
#         for i in range(1, len(timeCfg.values())+1):
#             if dt >= timeCfg[i]['NeedTime']:
#                 less += 1
#                 dt -= timeCfg[i]['NeedTime']
        for i in xrange(1, lottoryNum + 1):
            if dt >= timeCfg[str(i)]:
                less += 1
                dt -= timeCfg[str(i)]
        less -= lastLottery['LotteryCount']
        if less <= 0:
            return  Gcore.error(optId, -23011001)#可抽奖次数不足
        
        #获取抽到的奖励类型和等级
        typeCfg = Gcore.getCfg('tb_cfg_act_online_type').values()
        typeCfg = filter(lambda dic:dic['Ratio']!=0, typeCfg)#暂时不随机到宝物和兵书
        types = []
        level = 3
        typeValue = random.randint(2, 3)#如果等级是3则在铜钱和军资中随即一个
        for i in range(0, 3):
            theType = common.Choice(typeCfg)
            for j in range(0, len(types)):
                if theType['TypeId'] == types[j]:
                    level -= 1
                    typeValue = theType['TypeId']
                    break
            types.append(theType['TypeId'])
        
        #进行奖励
        awards = Gcore.getCfg('tb_cfg_act_online_award', (typeValue, level))
        
        award = random.choice(awards)
        modReward = Gcore.getMod('Reward', self.uid)
        award['Gain'] = modReward.reward(optId, param, award['AwardType'], award['GoodsId'], award['GoodsNum'])
        
        #更新在线奖励记录
        lastLottery['AwardId'] = award['AwardId']
        lastLottery['LotteryCount'] += 1
        lastLottery['AwardType'] = award['AwardType']
        lastLottery['GoodsId'] = award['GoodsId']
        lastLottery['GoodsNum'] = award['GoodsNum']
        types = [str(t) for t in types]
        lastLottery['LotteryInfo'] = str.join(',',types)
        self.mod.updateOnlineLottery(lastLottery)
        return Gcore.out(optId, {'LotteryInfo': lastLottery['LotteryInfo'], 'Award': award})
    
    def GetActiveLog(self, param={}):
        '''显示活跃度UI'''
        optId = 23012
        data = {}
        activeLog = self.mod.getActiveLog(['DayTimes', 'ActionId'])
        activeLog = list(activeLog)
        actions = Gcore.getCfg('tb_cfg_act_active_action').keys()
        aa = [ac['ActionId'] for ac in activeLog]
        for ak in actions:
            if ak in aa:
                continue
            else:
                activeLog.append({'ActionId': ak, 'DayTimes': 0})
        score = self.mod.getActiveScore()
        activeLog.sort(cmp=lambda x,y:cmp(x['ActionId'],y['ActionId']))
        data['ActiveLog'] = common.list2dict(activeLog)
        if not score:
            data['Score'] = 0
        else:
            data['Score'] = score
        return Gcore.out(optId, data)
    
    #@2013/06/19 by qiudx
    def GetValidGift(self, param = {}):
        optId = 23013
        #activityId = [2, 3, 4] #签到、活跃、成长
        num = self.mod.pushGiftNum()
        return Gcore.out(optId, {'GiftNum': num})
        #return Gcore.push(109, self.uid, {'GiftNum': num})

if __name__ == '__main__':
    uid=44513
    f=ActivityUI(uid)
#    f.GetValidGift()
#     print Gcore.getCfg('tb_cfg_act_online_award')
    print f.GetActivitiesUI()
#    print f.GetGift({'GiftId':2523})
    #print f.GiftList({})
    #for i in range(766,781):
    #    print 'Gift',i
    #    f.GetGift({'GiftId':i})
#    print f.GetRechargeReward()
#     print f.GetRechargeReward()
#     print f.GetRechargeUI()
#    f.GetSignInLog()
#    f.SignIn({'Date':12})
#     f.Lucky()
#    f.GetLuckyLog()
#     f.ShowLottory()
#    f.GetActiveLog()

    
    
    


    #print f.CountApply()
    
