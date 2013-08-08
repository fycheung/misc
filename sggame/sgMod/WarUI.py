# -*- coding:utf-8 -*-
# author: Lizr
# date:2013-2-27
# 游戏外部接口 战役

import gevent
from sgLib.core import Gcore,inspector

class WarUI(object):
    """战役 ModId:91"""
    def __init__(self, uid):
        '''注释'''
        self.uid = uid
        self.mod = Gcore.getMod('War',uid)
        #print self.mod
        
    def test(self,para={}):
        '''测试方法'''
        print 'test'
    
    @inspector(91001,['StoryId'])
    def WarInfo(self,para={}):
        '''战斗选择界面
        @param StoryId: 章节ID 
        '''
        optId = 91001
        StoryId = para['StoryId']
        
        body = self.mod.getWarDetail(StoryId)
        Gcore.push(999, self.uid) #测试推送
        return Gcore.out(optId, body)
    
    @inspector(91002,['WarIdList'])
    def WarSweep(self,para={}):
        '''扫荡
        @param WarIdList: 战役ID列表
        '''
        optId = 91002
        WarIdList = para['WarIdList']
        assert isinstance(WarIdList, (tuple,list))
        if not self.mod._checkGeneralSoldier():
            return Gcore.error(optId, -91002001)
        result,RestPoint = self.mod.warSweep( WarIdList )
        return Gcore.out(optId, {'result':result,'restPoint':RestPoint})
    

    
    def WarInfoAll(self,para={}):
        '''战役主界面(新) by Lizr'''
        optId = 91003
        body = self.mod.getWarInfoAll()
        RestPoint,MaxPoint = self.mod.getActPoint()
        body['RestPoint'] = RestPoint
        body['MaxPoint'] = MaxPoint
        body['PerBuyAddPoint'] = Gcore.loadCfg(9101).get('PerBuyAddPoint')
        body['BuyTimesPrice'] = Gcore.loadCfg(9101).get('BuyTimesPrice')
        MaxBuyActTimes = Gcore.loadCfg(9101).get('MaxBuyActTimes')
        TodayBuyTimes = self.mod.getTodayBuyTimes()
        body['CanBuy'] = 1 if TodayBuyTimes < MaxBuyActTimes else 0
        body['AlreadyBuyTimes'] = TodayBuyTimes
        body['MaxBuyActTimes'] = MaxBuyActTimes
        return Gcore.out(optId, body)
    
    def BuyActPoint(self,para={}):
        '''购买行动点数'''
        optId = 91004
        MaxBuyActTimes = Gcore.loadCfg(9101).get('MaxBuyActTimes')
        TodayBuyTimes = self.mod.getTodayBuyTimes()
        print 'TodayBuyTimes',TodayBuyTimes
        if MaxBuyActTimes <= TodayBuyTimes:
            Gcore.out(optId, -91004001) #已达可购买上限
        else:
            TodayBuyTimes += 1
            CostValue = Gcore.loadCfg(9101).get('BuyTimesPrice').get( str(TodayBuyTimes) )
            if CostValue is None:
                CostValue = max( Gcore.loadCfg(9101).get('BuyTimesPrice').values() )
            #开始支付
            modCoin = Gcore.getMod('Coin', self.uid)
            pay = modCoin.PayCoin(optId, 1, CostValue, 'WarUI.BuyActTimes', para)
            if pay < 0:
                return Gcore.error(optId, -91004995) #支付失败
            else:            
                result = self.mod.buyActPoint()
                if not result:
                    return Gcore.error(optId, -91004002) #系统错误
        
        body = {}
        body['CanBuy'] = 1 if TodayBuyTimes < MaxBuyActTimes else 0
        RestPoint,MaxPoint = self.mod.getActPoint()
        body['RestPoint'] = RestPoint
        body['MaxPoint'] = MaxPoint
        return Gcore.out(optId, body)
    
    @inspector(91005,['WarId','SweepTimes'])
    def WarSweepNew(self,para={}):
        '''新扫荡'''
        optId = 91005
        if not self.mod._checkGeneralSoldier():
            return Gcore.error(optId, -91005001)
        if para['SweepTimes']<=0:
            return Gcore.error(optId, -91005997)
        re = self.mod.warSweepNew( para['WarId'], para['SweepTimes'] )
        if not re:
            return Gcore.error(optId,-91005002)
        gevent.sleep(0.5)
        body ={}
        RestPoint,MaxPoint = self.mod.getActPoint()
        body['RestPoint'] = RestPoint
        
        return Gcore.out(optId,body)
    
    @inspector(91006)
    def StopSweep(self,para={}):
        '''停止 扫荡'''
        optId = 91006
        Gcore.setUserData(self.uid, {'Sweeping':False} )
        return Gcore.out(optId)
    
    def GetPointNum(self,para={}):
        '''获取行动力点数'''
        optId = 91007
        RestPoint,MaxPoint = self.mod.getActPoint()
        body={}
        body['RestPoint'] = RestPoint
        body['MaxPoint'] = MaxPoint
        return Gcore.out(optId,body)
        
    #下一协议号 由91007开始
        ''
if __name__ == '__main__':
    uid = 1001
    c = WarUI(uid)
    #c.WarInfo({"StoryId":1})
    #c.WarInfoAll()
    #c.WarSweep({"WarIdList":[101,102]}) #,103,104
    c.BuyActPoint()
    #c.WarSweepNew({'WarId':101,'SweepTimes':2})
