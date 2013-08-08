# -*- coding:utf-8 -*-
# author:
# date:2013-1-
# 游戏内部接口,货币模型

import time
import math
from sgLib.core import Gcore
from sgLib.base import Base
from sgLib.common import json_encode, datetime

class CoinMod(Base):
    """货币模型"""
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid

    def test(self):
        '''测试方法'''
    
    def getCurrency(self):
        '''获取我的货币情况'''
        row = self.db.out_fields('tb_currency', '*', 'UserId=%s' % self.uid)
        return row
    
    def getCoinNum(self, coinType):
        '''获取资源数量
        param:coinType -int -资源类型：1:黄金；2：军资，3：铜币，4：美酒。
        return value:  -False or None:获取资源数量失败；n -int -资源数量
        '''
        table = None
        field = None
        if coinType == 1:
            table = 'tb_user'
            field = 'GoldCoin'
        elif coinType == 2:
            table = 'tb_currency'
            field = 'Jcoin'
        elif coinType == 3:
            table = 'tb_currency'
            field = 'Gcoin'
        elif coinType == 4:
            table = 'tb_currency'
            field = 'Mcoin'
            
        value = self.db.out_field(table, field, 'UserId=%s' % self.uid)
        return value
    
    def PayCoin(self,optId,coinType,coinValue,classMethod,param=''):
        ''' 使用货币
        @param optId:协议号
        @param coinType:货币类型 1,2,3,4
        @param coinValue: 货币值
        @param classMethod: 类和方法 class.method
        @param param: 参数
        @return:
             1：成功
            -1：输入货币类型或货币值异常,非法操作 
            -2: 货币不足
            -3：支付失败
        '''
        if isinstance(param, (tuple,dict)):
            param = json_encode(param)
            
        coinType = int(coinType)
        if coinType==1:
            table = 'tb_user'
            field = 'GoldCoin'
            #Vip黄金消耗折扣  add by zhanggh 5.28
            
            vipLevel = Gcore.getUserData(self.uid, 'VipLevel')
            discount = Gcore.getCfg('tb_cfg_vip_up',vipLevel,'Discount')
            discount = discount if discount else 1
            print '未打折前', coinValue
            print 'vip折扣是', discount
            
            coinValue = math.ceil(coinValue*discount)
            
        elif coinType==2:    
            table = 'tb_currency'
            field = 'Jcoin'
        elif coinType==3:
            table = 'tb_currency'
            field = 'Gcoin'
        elif coinType==4:
            table = 'tb_currency'
            field = 'Mcoin'
        else:
            return -1

        if coinValue<=0:
            return -1
        
        MyCoin = self.getCoinNum(coinType)
        #print '当前货币数量', MyCoin
        if MyCoin<coinValue: #货币不足
            return -2 
        else:
            NowCoin = MyCoin-coinValue
            #sql = "UPDATE "+table+" SET "+field+"=%s WHERE UserId='%s'"%(NowCoin,self.uid) #并发有问题
            sql = "UPDATE "+table+" SET "+field+"="+field+"-"+str(coinValue)+" WHERE "+field+">="+str(coinValue)+" AND UserId='%s'"%self.uid
            print '支付货币:',sql
            
            result = self.db.execute(sql)
            if not result:
                return -3
            else:
                #记录日志 
                table = 'tb_log_coin_%s'%coinType
                d = {}
                d['OptId'] = optId
                d['UserId'] = self.uid
                d['UserType'] = Gcore.getUserData(self.uid,'UserType')
                d['UserLevel'] = Gcore.getUserData(self.uid, 'UserLevel')
                d['OldCoin'] = MyCoin
                d['CoinNumber'] = coinValue
                d['Action'] = 2 # 1获得 2消耗
                d['NowCoin'] = NowCoin
                d['Func'] = classMethod
                d['Param'] = str(param)
                d['CreateTime'] = int(time.time())
                print ' >>> Logging CoinMod.PayCoin',d
                self.db.insert(table,d,isdelay=False) #货币日志不采用延迟插入,怕丢
                Gcore.getMod('Event',self.uid).payCoinTrigger(optId,coinValue)
                return coinValue
    
        
    def GainCoin(self,optId,coinType,coinValue,classMethod,param=''):
        ''' 获取货币
        @param optId:协议号
        @param coinType:货币类型 1,2,3,4
        @param coinValue: 货币值
        @param classMethod: 类和方法 class.method
        @param param: 参数
        @return:
            False 获取货币失败
            int   获得的货币数量
        '''
        
        if isinstance(param,(tuple,dict)):
            param = json_encode(param)
            
        coinType = int(coinType)
        if coinType==1:
            table = 'tb_user'
            field = 'GoldCoin'
        elif coinType==2:    
            table = 'tb_currency'
            field = 'Jcoin'
        elif coinType==3:
            table = 'tb_currency'
            field = 'Gcoin'
        elif coinType==4:
            table = 'tb_currency'
            field = 'Mcoin'
        
        MyCoin = self.getCoinNum(coinType)
        NowCoin = MyCoin+coinValue
        isFull = False
        
        if coinType==2 or coinType==3:
            storageSpace = Gcore.getMod('Building', self.uid).cacStorageSpace(coinType)
            if NowCoin > storageSpace:#存满
                isFull = True
                NowCoin = storageSpace
                coinValue = storageSpace - MyCoin #增加的数值
        
        if MyCoin == NowCoin: #没有可增空间
            print ' >> CoinMod Coin full GainCoin fail coinType:%s %s'%(coinType,coinValue)
            return 0
        
        #sql = "UPDATE "+table+" SET "+field+"=%s WHERE UserId='%s'"%(NowCoin,self.uid)
        sql = "UPDATE "+table+" SET "+field+"="+field+"+"+str(coinValue)+" WHERE UserId='%s'"%self.uid
        result = self.db.execute(sql)
        if not result:
            return -2
        else:
            #记录日志 
            table = 'tb_log_coin_%s'%coinType
            d = {}
            d['OptId'] = optId
            d['UserId'] = self.uid
            d['UserType'] = Gcore.getUserData(self.uid,'UserType')
            d['UserLevel'] = Gcore.getUserData(self.uid, 'UserLevel')
            d['OldCoin'] = MyCoin
            d['CoinNumber'] = coinValue
            d['Action'] = 1 # 1获得 2消耗
            d['NowCoin'] = NowCoin
            d['Func'] = classMethod
            d['Param'] = str(param)
            d['CreateTime'] = int(time.time())
            print ' >>> Logging CoinMod.GainCoin',d
            self.db.insert(table,d,isdelay=False) #货币日志不采用延迟插入,怕丢
            Gcore.getMod('Event',self.uid).gainCoinTrigger(optId,coinType,coinValue,NowCoin,isFull)
            return coinValue #当前拥有大于容量时候会返回负值
        
        
CoinMod = CoinMod
if __name__ == '__main__':
    uid = 1001
    c = CoinMod(uid)
    #c.test()
    #print c.getCoinNum(2)
    #print c.db.execute('SELECT Jcoin FROM tb_currency WHERE UserId=1008')
#     print c.PayCoin(999,1,100,'test ,test',{'s':'b'})
    print c.PayCoin(999,1,0,'fuck.you',{'s':'b'})
    
    #----------------并发扣钱-----------------
#    import gevent
#    def test(i):
#        c.PayCoin(15001,2,3636750,'fuck.you',{'s':'b'})
#    chs = []
#    for i in xrange(2):
#        chs.append(gevent.spawn(test,i))
#    gevent.joinall(chs)
    #-----------------------------------------
    
#    print c.GainCoin(999,3,1,'fuck.you',{'s':'b'})
    