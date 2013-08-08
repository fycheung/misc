# -*- coding:utf-8 -*-
# author:Lijs
# date:2013-4-8
# 游戏内部接口,道具系统

from __future__ import division
import math
import time
from sgLib.defined import CFG_PLAYER_BAG, CFG_BUILDING_HOLD
from sgLib.core import Gcore
from sgLib.base import Base

class ItemMod(Base):
    def __init__(self, uid):
        '''注释'''
        Base.__init__(self,uid)
        self.uid = uid
        
    def useItem(self, optId, classMethod, param, itemId, itemNum = 1, position = None, friendUserId = None):
        '''
                        使用道具
        @result res:>=0,使用后实际作用的效果值
                    -1,背包没有道具
                    -2,使用等级不够
                    -3,道具不存在
                    -101,添加数量超过可添加空间不能使用
                    -111，没有空闲武将台
                    -112，已拥有改类型武将已经
                    -121，没有铁匠铺
                    -122，强化次数已是最大值
                    -131，没有点将台
                    -132，培养次数已是最大值
                    -141，目前没有支配者
                    -151，用户不存在
                    -152，不是好友
                    -161, 超过背包格数上限
        '''
        modBag = Gcore.getMod('Bag', self.uid)
        if modBag.countGoodsNum(itemId) < itemNum:
            return -1#道具数量不足
       
        itemCfg = Gcore.getCfg('tb_cfg_item', itemId)
        if itemCfg is None:
            return -3#没有该道具
        if self.getUserLevel() < itemCfg['UseLevel']:
            return -2#使用等级不够
        
        functionId = int(round(itemId/100))
        featureValue = itemCfg['FeatureValue']
        if functionId != 10 and functionId != 18:
            featureValue = int(float(featureValue))
        if functionId not in(10,11):
            featureValue = featureValue*itemNum
        res=0
        if functionId in[1,2,3,4]:
            #获取资源类功能值（超过资源上限暂定为加至上限最大值）---当前值达上限时不让使用
            modCoin = Gcore.getMod('Coin', self.uid)
            res = modCoin.GainCoin(optId, functionId, featureValue, classMethod, param)
            if res == 0:
                return -162
        elif functionId == 5:
            #添加主角经验
            modPlay = Gcore.getMod('Player', self.uid)
            res = modPlay.addUserExp(0, featureValue, optId)
        elif functionId == 6:
            #添加主角荣誉值
            modPlay = Gcore.getMod('Player', self.uid)
            modPlay.gainHonour(featureValue, optId)
            res = featureValue
        elif functionId == 7:
            res = 1#强化传承卡
        elif functionId == 8:
            res = 1#喇叭
        elif functionId == 9:
            #停战卡
            playMod = Gcore.getMod('Player', self.uid)
            playMod.addProtectTime(60*featureValue)
            res = 60 * featureValue
        elif functionId == 10:
            #增加兵种数量(超过数量上限暂定为添加失败)
            modCamp = Gcore.getMod('Building_camp', self.uid)
            fVal = featureValue.split(',')
            soldierType = int(fVal[0]) #兵种类型
            soldierNum = int(fVal[1])*itemNum  #士兵数量
            valid = modCamp.isSameCamp(soldierType, True)
            if not valid:
                return -102
            res = modCamp.changeSoldierNum({soldierType: soldierNum})
            if res == -1:
                return -101#添加数量超过可添加空间不能使用
            #res = fVal[1]
            res = {'SoldierType': soldierType, 'SoldierNum': soldierNum}
        elif functionId == 11:
            #获得武将
            modPub = Gcore.getMod('Building_pub', self.uid)
            freeGeneralHomes = modPub.getFreeGeneralHomes()
            if freeGeneralHomes == []:
                return -111#没有空闲的武将台
            modGeneral = Gcore.getMod('General', self.uid)
            #By Zhanggh 2013-6-4
            res = modGeneral.addNewGeneral(featureValue, freeGeneralHomes[0], time.time(), flag=True, getWay=2)
            if not res:
                return -112#该武将已经存在
        elif functionId == 12:
            #增加强化次数
            modEquip = Gcore.getMod('Equip', self.uid)
            res = modEquip.changeStrengthNum(featureValue)
            if res < 0:
                return -121#没有铁匠铺
            if res == 0:
                return -122#强化次数已是最大值
            
        elif functionId == 13:
            #增加培养次数
            modTrain = Gcore.getMod('Building_train', self.uid)
            res = modTrain.superAddTrainNum(featureValue)
            if not res:
                return -131#没有点将台
#             elif res == -2:
#                 return -132#培养次数已是最大值
            else:
                res = 1
        elif functionId == 14:
            #调停卡
            modHold = Gcore.getMod('Building_hold', self.uid)
            holder = modHold.getMyHolder()
            if holder[0] == 0 or holder[1] == 0:
                return -141#你目前没有支配者
            res = modHold.freed(holder[1], holder[0])
            #添加潘国保护时间
            pMod = Gcore.getMod('Player', self.uid)
            protectTime = Gcore.loadCfg(CFG_BUILDING_HOLD)['ProtectHoldSecond']
            pMod.addProtectHoldTime(protectTime)

        elif functionId == 15:
            #增加好感度道具
            if friendUserId is None:
                return -151#用户不存在
            modFriend = Gcore.getMod('Friend', self.uid)
            res = modFriend.addFavor(friendUserId, featureValue)
            if res == -1:
                return -152#不是好友
        elif functionId == 16:
            #背包扩展箱
            bagCfg = Gcore.loadCfg(CFG_PLAYER_BAG)
            expbn = bagCfg['PerExpandNum']*featureValue
            modBag = Gcore.getMod('Bag', self.uid)
            curbn = modBag.getBagSize()
            if curbn + expbn > bagCfg['MaxNum']:
                return -161#超过背包格数上限
            modBag.expandBag(curbn, expbn)
            res = expbn + curbn
            if res == bagCfg['MaxNum']:
                full = 1
            else:
                full = 0
            res = {'CurNum': res, 'Full': full}
        elif functionId == 18:#物品包
            fVal = featureValue.split(',')
            fNum = int(fVal[0])
            fBoxType = int(fVal[1])
            itemBoxCfg = Gcore.getCfg('tb_cfg_item_box', fBoxType)
            rewardMod = Gcore.getMod('Reward', self.uid)
            bagMod = Gcore.getMod('Bag', self.uid)
            resBox = {}
            for _ in range(fNum):
                tmpRes = {}
                itemBox = Gcore.common.Choice(itemBoxCfg)
                tmpRes['GoodsType'] = itemBox['ItemType']
                tmpRes['GoodsId'] = itemBox['ItemId']
                tmpRes['GoodsNum'] = itemBox['ItemNum']
                keys = (tmpRes['GoodsType'], tmpRes['GoodsId'])
                if keys not in resBox:
                    resBox[keys] = tmpRes
                else:
                    resBox[keys]['GoodsNum'] += tmpRes['GoodsNum']
            res = resBox.values()
            #判断背包是否有足够的格子 
            if not bagMod.canAddInBag(res):
                return -163 #背包空间不足
            for goods in res:
                rewardMod.reward(optId, param, goods['GoodsType'], goods['GoodsId'], goods['GoodsNum'])
        else:
            res = 1
        if res >= 0:
            modBag.useItems(itemId, itemNum, position)
        self.insertItemLog(optId, itemId, itemNum, 2)
        return res
    
    
    def insertItemLog(self, optId, itemId, itemNum, action):
        '''
        @param optId:
        @param itemId:
        @param itemNum:
        @param action:1为产出，2为消耗
        '''
        now = Gcore.common.nowtime()
        row = {'UserId': self.uid,
             'UserType': Gcore.getUserData(self.uid,'UserType'),
             'Action': action,
             'ItemId': itemId,
             'Num': itemNum,
             'OptId': optId,
             'CreateTime': now
        }
        self.db.insert('tb_log_item', row, isdelay = False)
    


def _test():
    uid = 1003
    c = ItemMod(uid)
    print c.useItem(20004,'ItemUI.UseItem',{'ItemId':1601},1601,1)
#    c.addItemToBag(103,10)
#    c.addNewItem(ItemId=101,ItemNum=101)

if __name__ == '__main__':
    _test()