# -*- coding:utf-8 -*-
# author:Yew
# date:2013-4-23
# 拜访系统UI

from sgLib.core import Gcore, inspector
from sgLib import common
import random
import time
import sys
import datetime
class VisitUI(object):
    def __init__(self,uid):
        self.uid=uid
        self.mod=Gcore.getMod('Interact', uid)
        
    @inspector(21001,['FriendUserId'])    
    def Visit(self, param = {}):
        '''访问好友'''
        optId = 21001
        recordData = {}#成就记录
        friendUserId = param['FriendUserId']
        modFriend = Gcore.getMod('Friend', self.uid)
        if not modFriend.validateUser(friendUserId):
            return Gcore.error(optId, -21001001)#用户不存在
        
        #获取地图信息
        modMap = Gcore.getMod('Map', friendUserId)
        modBuilding = Gcore.getMod('Building', friendUserId)
        BuyMapInfo = modMap.getMyBuyMap() #已购买地皮，待优化
        BuildingInfo = modBuilding.getAllBuildingCoord()
        
        #获取武将信息
        generalMod = Gcore.getMod('General', friendUserId)
        Generalss = generalMod.getLatestGeneralInfo()
        Generals = [] 
        for g in Generalss:
            gg = {}
            gg['GeneralId'] = g['GeneralId']
            gg['GeneralType'] = g['GeneralType']
            gg['Location'] = g['Location']
            Generals.append(gg)
        generalId = 0
            
        #获取受访者基本信息
        modPlay = Gcore.getMod('Player', friendUserId)
        friendInfo = modPlay.getUserBaseInfo(['UserId', 'NickName', 'UserLevel', 'VipLevel', 'UserHonour', 'UserIcon'])
        
        #获取拜访者鲜花数量
        modBag = Gcore.getMod('Bag', self.uid)
        flowerNum = modBag.countGoodsNum(1501)
        
        #判断双方是否为好友
        isFriend = modFriend.validateFriend(friendUserId)
        ftv = 0
        existBox = 0
        if not isFriend:
            data={'FriendInfo': friendInfo,
                  'FlowerNum': flowerNum,
                  'IsFriend': isFriend,
                  'ExistBox': existBox,
                  'FriendList': {},
                  'isFTV': ftv,
                  'GeneralId': generalId,
                  'GainAward': {},
                  'BuildingInfo': BuildingInfo,
                  'BuyMapInfo': BuyMapInfo,
                  'Generals': Generals}
        else:
            #获取拜访者的好友列表
            friendList = modFriend.getFriendList(fields = ['UserId', 'NickName', 'UserIcon', 'UserLevel', 'Favor'])
            #获取上一次访问时间    
            visitTime = modFriend.getVisitTime(friendUserId)
            now = Gcore.common.nowtime()
            if (now - visitTime) < 1800:#判断距离上次访问时间是否小于30分钟
                generalId = 0
            else:
                rnd = random.randint(1, 10)
                if rnd <= 1:
                    existBox = 1#宝箱
                if self.mod.getInteractTime(3) < 10:#判断武将交流互动是否少于次数限制
                    if Generals: #玩家有武将
                        generalId = random.choice(Generals)['GeneralId']#随即出可交流武将
                        
            interactRes = self.mod.InteractAward(friendUserId, 1, optId, param)
            gainAward = interactRes['GainAward']
            if interactRes['Judge']:
                ftv = 1
                self.mod.insertVisitInteract(friendUserId, gainAward['GainMcoin'])
            
            data = {'FriendInfo':friendInfo,
                  'FlowerNum':flowerNum,
                  'IsFriend':isFriend,
                  'ExistBox':existBox,
                  'FriendList':friendList,
                  'GeneralId':generalId,
                  'isFTV':ftv,
                  'GainAward':{'GainFavor': gainAward.get('GainFavor', 0), 'GainMcoin': gainAward.get('GainMcoin', 0)},
                  'BuildingInfo':BuildingInfo,
                  'BuyMapInfo':BuyMapInfo,
                  'Generals':Generals
            }
            modFriend.updateVisitTime(friendUserId,now)#更新访问时间  
            recordData = {'uid': self.uid, 'ValType': 0, 'Val': 1, 'ExistBox': existBox}#成就记录
            
        #获取拜访者美酒数量
        modCoin=Gcore.getMod('Coin',self.uid)
        mcoinNum=modCoin.getCoinNum(4)
        #获取好感度
        if isFriend:
            favor = modFriend.getFavor(friendUserId)
        else:
            favor = 0
        data['Favor'] = favor
        data['McoinNum'] = mcoinNum
            
        return Gcore.out(optId, data, achieve = recordData, mission = recordData) 
            
            
    def OpenBox(self,param={}):
        '''开宝箱'''
        optId=21002
        boxs=Gcore.getCfg('tb_cfg_visit_box').values()
        box=common.Choice(boxs)
        #给宝箱物品给玩家

        modReward=Gcore.getMod('Reward',self.uid)
        modReward.reward(optId,param,box['RewardType'],box['GoodsId'],box['GoodsNum'])
        return Gcore.out(optId,{'RewardType':box['RewardType'],
                'GoodsId':box['GoodsId'],
                'GoodsNum':box['GoodsNum']})
    
    #@inspector(21003,['FriendUserId','GerneralId'])    
    def GeneralInteract(self, param = {}):
        '''武将交流'''
        optId = 21003
        generalId = param['GeneralId']
        friendUserId = param['FriendUserId']
        interactRes = self.mod.InteractAward(friendUserId, 3, optId, param, True)
        gainAward = interactRes['GainAward']
        if interactRes['Judge']:
            self.mod.insertGeneralInteract(friendUserId, generalId, gainAward['GainMcoin'])#奖励存进日志
        
        body = {'GainAward': gainAward}
        recordData = {'uid': self.uid, 'ValType': 0, 'Val': 1, 'MCoin': gainAward.get('GainMcoin', 0)}#成就,任务记录
        return Gcore.out(optId, body, mission = recordData)
    
    @inspector(21004,['FriendUserId'])   
    def SendFlowers(self,param={}):
        '''
                    送花
        @result:Result为是否使用，Favor为实际增加了多少好感度
        '''
        optId=21004
        itemId=1501#鲜花道具ID
        friendUserId=param['FriendUserId']
        itemMod=Gcore.getMod('Item',self.uid)
        classMethod = '%s,%s'%(self.__class__.__name__,sys._getframe().f_code.co_name)
        re=itemMod.useItem(optId,classMethod,param,itemId,1,None,friendUserId)
        if re==-1:
            #弹出错误
            return Gcore.error(optId,-21004001)#鲜花不足
        else:
            data={'GainFavor':re}
        
        recordData = {'uid':self.uid,'ValType':0,'Val':1}#成就,任务记录
        return Gcore.out(optId,data,mission=recordData)
    
    @inspector(21005,['GeneralId']) 
    def GetGeInteractLog(self,param={}):
        '''获取武将交流记录(受访者用)'''
        optId=21005
        generalId=param['GeneralId']
        re=self.mod.getGeInteractLog(generalId)
        getMcoin=0
        for award in re:
            getMcoin+=award['McoinNum']
        if getMcoin==0:
            gainMcoin=getMcoin
        else:
            modCoin=Gcore.getMod('Coin',self.uid)
            classMethod = '%s,%s'%(self.__class__.__name__,sys._getframe().f_code.co_name)
            gainMcoin=modCoin.GainCoin(optId,4,getMcoin,classMethod,param)
        self.mod.setGeInteractGet(generalId)
        interactLog=common.list2dict(re)
        return Gcore.out(optId,{'InteractLog':interactLog,'GainMcoin':gainMcoin})
    
    def GetGeInteractAward(self,param={}):
        '''获取武将交流美酒(受访者用)'''
        optId=21006
#        generalId=param['GeneralId']
#        awards=self.mod.getGeInteractLog(generalId)
#        getMcoin=0
#        for award in awards:
#            getMcoin+=award['McoinNum']
#        modCoin=Gcore.getMod('Coin',self.uid)
#        classMethod = '%s,%s'%(self.__class__.__name__,sys._getframe().f_code.co_name)
#        re=modCoin.GainCoin(optId,4,getMcoin,classMethod,param)
        interactGids=self.mod.getHaveMcoinGeneralIds()#获取有交流记录的武将ID
        return Gcore.out(optId,{'GainMcoin':interactGids})
        
        
            
if __name__ == '__main__':
    v=VisitUI(43438)
#    v.GeneralInteract(param)
    #print Gcore.getCfg('tb_cfg_quote')
#    for j in range(1000,1060):
#        v=VisitUI(j)
#        for i in range(1000,1060):
#            print j,i
#            v.Visit({'FriendUserId':i})
    v.Visit({'FriendUserId':43413})
#    Gcore.runtime()
    #v.GetGeInteractLog({'GeneralId':8})
    #v.OpenBox()
    #v.GeneralInteract({'FriendUserId':43280,'GeneralId':15108})
    #v.GetGeInteractLog({'GeneralId':1005})
    #v.GetGeInteractAward()
    #v.SendFlowers({'FriendUserId':1011})    