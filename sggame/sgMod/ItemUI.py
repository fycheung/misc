# -*- coding:utf-8 -*-
# author:Lijs
# date:2013-4-8
# 游戏外部接口 道具
from __future__ import division
import math
import sys
from sgLib.core import Gcore, inspector


class ItemUI(object):
    """测试 ModId:99 """
    def __init__(self, uid):
        '''注释'''
        self.uid = uid
        self.mod = Gcore.getMod('Item', uid)
    
    @inspector(20001,['CoinType', 'CoinValue'])
    def Exchange(self, para={}):
        '''货币兑换  by Lizr'''
        optId = 20001
        CoinType =  para['CoinType']
        CoinValue = para['CoinValue']
        if CoinType not in (2, 3):
            return Gcore.error(optId, -20001998) #非法操作
        if type(CoinValue) not in (int, long) or CoinValue <= 0:
            return Gcore.error(optId, -20001998) #非法操作
        
        storageSpace = Gcore.getMod('Building', self.uid).cacStorageSpace(CoinType)
        addPercent = CoinValue / storageSpace
        rateInfos = Gcore.getCfg('tb_cfg_shop_res_sale')
        rateInfoList = filter(lambda dic:dic['AddPercent'] <= addPercent and dic['CoinType'] == CoinType, rateInfos.values())
        rateInfo = max(rateInfoList, key=lambda sale:sale['AddPercent'])

        rate = rateInfo['kPrice1'] * (storageSpace ** rateInfo['kPrice2'])
        GoldValue = int(math.ceil(CoinValue * rate))
#         rate = Gcore.loadCfg(2001).get('exchange').get(str(CoinType))
#         GoldValue = math.ceil(CoinValue/rate)
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        pay = modCoin.PayCoin(optId, 1, GoldValue, classMethod, para)
        if pay < 0:
            return Gcore.error(optId, -20001995) #支付失败
        else:
            #GainValue = GoldValue*rate
            #GainValue = int(math.ceil(GoldValue / rate))
            #result = modCoin.GainCoin(optId, CoinType, GainValue, classMethod, para)
            result = modCoin.GainCoin(optId, CoinType, CoinValue, classMethod, para)
            body = {"CoinType": CoinType, "CoinValue": CoinValue, "GoldUsed": pay}
            return Gcore.out(optId, body)    
            
    @inspector(20002, ['ResSaleId'])
    def BuyResource(self, param={}):
        '''商城购买资源'''
        optId=20002

        classMethod = '%s,%s'%(self.__class__.__name__,sys._getframe().f_code.co_name)
        
        resSaleId = param['ResSaleId']
        resSaleCfg = Gcore.getCfg('tb_cfg_shop_res_sale', resSaleId)

        coinType = resSaleCfg['CoinType']
        percent = resSaleCfg['AddPercent']

        buildingMod = Gcore.getMod('Building', self.uid)
        maxCoin = buildingMod.cacStorageSpace(coinType)

        modCoin = Gcore.getMod('Coin', self.uid)
        currCoinNum = modCoin.getCoinNum(coinType)

        if percent < 1:
            coinValue = maxCoin*percent#增加货币
            
        elif percent == 1:
            coinValue = maxCoin - currCoinNum#增加货币
            percent = coinValue / maxCoin
            #print 'percent', percent
            resSaleList = Gcore.getCfg('tb_cfg_shop_res_sale')
            resSaleList = filter(lambda dic:dic['AddPercent'] <= percent and dic['CoinType'] == coinType, resSaleList.values())
            resSaleCfg = max(resSaleList, key=lambda sale:sale['AddPercent'])
#             print resSaleList
#             resSaleList.sort(key=lambda sale:sale['AddPercent'])
#             if resSaleList:
#                 resSaleCfg=resSaleList.pop()
                    
        else:
            return Gcore.error(optId, -20002001)#percent错误,大于1
        
        if currCoinNum + coinValue > maxCoin:
            return Gcore.error(optId, -20002002)#超过资源上限

        kPrice1 = resSaleCfg['kPrice1']
        kPrice2 = resSaleCfg['kPrice2']
        #支付黄金
        useCoinValue = int(math.ceil(coinValue*kPrice1*maxCoin**kPrice2))
        re = modCoin.PayCoin(optId, 1, useCoinValue, classMethod, param)
        
        if re > 0:
            re = modCoin.GainCoin(optId, coinType, coinValue, classMethod, param)
            if re:
                return Gcore.out(optId, {'Result':re})
            else:
                return Gcore.error(optId, -20002997)#非法操作
        else:
            return Gcore.error(optId, -20002995)#支付失败
        
        
            
    @inspector(20004,['ItemId', 'ItemNum'])    
    def UseItem(self, param={}):
        '''使用道具'''
        optId = 20004
        itemId = param['ItemId']
        itemNum = param['ItemNum']
        if itemId in(801, 1501, 1701):
            return Gcore.error(optId, -20004015)#不可直接使用
        position = param.get('Position')
        friendUserId = param.get('FriendUserId')
        classMethod = '%s,%s'%(self.__class__.__name__,sys._getframe().f_code.co_name)
        res = self.mod.useItem(optId, classMethod, param, itemId, itemNum, position, friendUserId)
        '''
                    -101,没有可添加空间
                    -102,不能装备不同阵营的士兵
                    -111，没有空闲武将台
                    -112，已拥有改类型武将已经
                    -121，没有铁匠铺
                    -122，强化次数已是最大值
                    -131，没有点将台
                    -132，培养次数已是最大值
                    -141，目前没有支配者
                    -151，用户不存在
                    -152，不是好友
                    -161, 超过背包格子数上限
        '''
        if res == -1:
            return Gcore.error(optId, -20004001)#背包没有该道具
        elif res == -2:
            return Gcore.error(optId, -20004002)#使用等级不足
        elif res == -3:
            return Gcore.error(optId, -20004003)#道具不存在
        elif res == -101:
            return Gcore.error(optId, -20004004)#没有可添加空间
        elif res == -102:
            return Gcore.error(optId, -20004017)#不能装备不同阵营的士兵
        elif res == -111:
            return Gcore.error(optId, -20004005)#没有空闲武将台
        elif res == -112:
            return Gcore.error(optId, -20004006)#已拥有改类型武将
        elif res == -121:
            return Gcore.error(optId, -20004007)#没有铁匠铺
        elif res == -122:
            return Gcore.error(optId, -20004008)#强化次数已是最大值
        elif res == -131:
            return Gcore.error(optId, -20004009)#没有点将台
        elif res == -132:
            return Gcore.error(optId, -20004010)#培养次数已是最大值
        elif res == -133:
            return Gcore.error(optId, -20004997)#系统错误
        elif res == -141:
            return Gcore.error(optId, -20004011)#目前没有支配者
        elif res == -151:
            return Gcore.error(optId, -20004912)#用户不存在
        elif res == -152:
            return Gcore.error(optId, -20004013)#不是好友
        elif res == -161:
            return Gcore.error(optId, -20004014)#超过背包格子数上限
        elif res == -162:
            return Gcore.error(optId, -20004016)#当前资源已达上限
        elif res == -163:
            return Gcore.error(optId, -20004018)#背包空间不足
        else:
            #使用资源卡需返回资源类型给前台
            functionId = int(round(itemId / 100))
            GeneralInfo = {}
            if functionId in [1, 2, 3, 4, 6]:
                rt = functionId
            elif functionId == 9:
                rt = 7
            elif functionId == 11:
                rt = 8
                tb_general = self.mod.tb_general()
                fields = ['Location', 'GeneralType']    #建筑ID和武将类型
                GeneralInfo = self.mod.db.out_fields(tb_general, fields, 'GeneralId=%s and UserId=%s'%(res, self.uid))
            elif functionId == 10:
                rt = 9
                GeneralInfo = res   #待优化，此处存放士兵的类型和数量
                res = res['SoldierNum']
            elif functionId == 16:
                rt = 10
                GeneralInfo = res   #包含当前格子数和是否达最大格子数
                res = GeneralInfo['CurNum']
            elif functionId == 18:
                rt = 11
            else:
                rt = 0

            recordData = {'uid': self.uid, 'ValType':0, 'Val': itemNum,'ItemId':itemId}#成就、任务记录 
            return Gcore.out(optId,{'Result': res, 'RT': rt, 'GeneralInfo': GeneralInfo}, mission = recordData)
    
    
    @inspector(20006, ['IeSaleId'])
    def BuyItemEquip(self, param={}):
        '''商城购买装备或道具'''
        optId = 20006
        
        ieSaleId = param['IeSaleId']
        ieSaleCfg = Gcore.getCfg('tb_cfg_shop_ie_sale', ieSaleId)
        if ieSaleCfg is None:
            return Gcore.error(optId, -20006001)#商品不存在
        modCoin = Gcore.getMod('Coin', self.uid)
        modBag = Gcore.getMod('Bag', self.uid)
        if not modBag.inclueOrNot(ieSaleCfg['SaleType'], ieSaleCfg['GoodsId'], ieSaleCfg['OnceNum']):
            return Gcore.error(optId, -20006002)#背包空间不足
        
        classMethod = '%s,%s'%(self.__class__.__name__,sys._getframe().f_code.co_name)
        res = modCoin.PayCoin(optId, 1, ieSaleCfg['Price'], classMethod, param)

        if res == -2:
            return Gcore.error(optId, -20006994)#货币不足
        if res < 0:
            return Gcore.error(optId, -20006995)#支付失败或者非法操作

        modBag = Gcore.getMod('Bag', self.uid)
        buyId = modBag.addGoods(ieSaleCfg['SaleType'], ieSaleCfg['GoodsId'], ieSaleCfg['OnceNum'], addLog=optId)
        
        recordData = {'uid': self.uid, 'ValType': ieSaleCfg['GoodsId'], 'Val': ieSaleCfg['OnceNum'], 'GoodsType': ieSaleCfg['SaleType']}#成就、任务记录 
        return Gcore.out(optId, {'Result': buyId}, mission = recordData)
        
        
    

    
    

        
def _test():
    uid = 43522
    c = ItemUI(uid)
#    print c.Exchange({"CoinType":2,"CoinValue":11115000})
    #Gcore.printd(d)
#    print c.BuyResource({'ResSaleId':11})
#    c.BuyResource({'CoinType':3,'AddPercent':0.1})
    #print c.SaleItem({'ItemId':101,'GoodsNum':1})

    print c.UseItem({"ItemId": 1804, "ItemNum": 1})
#     print c.BuyItemEquip({'IeSaleId':1})
#    c.ResourceList()
#    c.ItemEquipList()
#    c.BuyFullResource({'CoinType':2})

if __name__ == '__main__':
    _test()

