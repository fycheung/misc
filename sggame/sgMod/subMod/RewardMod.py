# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-4-19
# 模块说明

from sgLib.core import *

from sgLib.base import Base

class RewardMod(Base):
    '''奖励模型'''
    def __init__(self,uid):
        Base.__init__(self,uid)
        self.uid = uid
    
    def rewardcell(self,rewardType,goodsId,goodsNum):
        '''构造单一奖励结构'''
        return {'RewardType':rewardType,'GoodsId':goodsId,'GoodsNum':goodsNum}
    
    def reward(self, optId, UIparam, rewardType, goodsId, goodsNum, emailed=True):
        '''
        :获取奖励
        @param optId：操作协议号
        @param subopt: 子操作（用于发送邮件）
        @param UIparam：调用UI的参数
        @param rewardType:奖励类别 1:装备,2:道具,3:资源,4:...6:武将碎片
        @param goodsId:奖励物品id（eg：当rewardType为1时装备类型，当rewardType为2时道具类型，当rewardType为3时货币类型）
        @param goodsNum:奖励数量
        @param emailed:是否发送邮件
        @param param 发送邮件的附加参数
        @return: 
                others：添加物品返回数组，如果是物品但背包没有位置返回空数组，资源返回成功添加值
                 0: 没有存放空间  #todo,改成空数组
                -1: 参数有误
                -2：操作失败
        '''
        
        #print 'RewardMod.reward rewardType=%s goodsId=%s goodsNum=%s'%(rewardType,goodsId,goodsNum),
        assert  isinstance(rewardType, (int,long))
        assert  isinstance(goodsId, (int,long))
        assert  isinstance(goodsNum, (int,long))
        
        flag = 0
        if rewardType in (1,4,5):#普通装备，兵书，宝物
            bagMod = Gcore.getMod('Bag',self.uid)
            flag = bagMod.addGoods(rewardType, goodsId, goodsNum, emailed, optId)#发邮件在BagMod实现
        elif rewardType==2:#道具
            bagMod = Gcore.getMod('Bag',self.uid)
            flag = bagMod.addGoods(2, goodsId, goodsNum, emailed, optId)#发邮件在BagMod实现
#             itemMod=Gcore.getMod('Item',self.uid)#已放到addGoods
#             itemMod.insertItemLog(optId,goodsId,goodsNum,1)
        elif rewardType==3:#资源
            if goodsId in [1,2,3,4]:
                coinMod = Gcore.getMod('Coin',self.uid)
    #            p = {'RewardType':rewardType,'goodsId':goodsId,'goodsNum':goodsNum}
                flag=coinMod.GainCoin(optId,goodsId,goodsNum,'RewardMod.reward',UIparam)
            
            elif goodsId==5:#奖励荣誉
                Gcore.getMod('Player',self.uid).gainHonour(goodsNum,optId)
            
            elif goodsId==6:#奖励军团贡献
                clubMod = Gcore.getMod('Building_club',self.uid)
                flag = clubMod.gainDeveote(clubMod.getUserClubId(),3,goodsNum)
        
        elif rewardType==6:#增加武将碎片
            flag = Gcore.getMod('Building_pub',self.uid).changePatchNum({goodsId:goodsNum})
            
        #@todo: 添加更多奖励类型
        #@todo: 添加日志记录
        return flag
    
    def rewardMany(self, optId, UIparam,rewardList, emailed=True):
        '''
        :一次奖励多个
        @param optId:
        @param UIparam:
        @param rewardList:  [{'RewardType':x,'GoodsId':x,'GoodsNum':x},...] 必须包含奖励类型,物品ID,物品数量...
        @param emailed:
        '''

        result = {'EquipIds':[],'WarBookIds':[],'TreasureIds':[]}
        equipType = {1:'EquipIds',4:'WarBookIds',5:'TreasureIds'}
        leftGoods = []
        for g in rewardList:
            rewardType = g['RewardType']
            goodsId = g['GoodsId']
            goodsNum = g['GoodsNum']
            leftNum = 0
            ids = self.reward(optId, UIparam, rewardType, goodsId, goodsNum, emailed=False)
            if rewardType in (1,2,4,5):
                if isinstance(ids,(list,tuple)) and rewardType in (1,4,5):
                    result[equipType[rewardType]].extend(ids)
                    leftNum = goodsNum-len(ids)
                elif isinstance(ids,(list,tuple)) and rewardType==2:
                    leftNum = goodsNum-ids[0]
                elif ids==0:
                    leftNum = goodsNum
                    
            if leftNum>0:
                leftGoods.append({'GoodsType':rewardType,'GoodsId':goodsId,'GoodsNum':leftNum})
        
        if emailed and leftGoods:
            Gcore.getMod('Mail',self.uid).sendSystemMail(self.uid,leftGoods,optId)
        return result



if __name__ == '__main__':
    uid = 1003
    c = RewardMod(uid)
    #RewardMod.reward rewardType=1 goodsId=1 goodsNum=1 return [] <type 'int'> <type 'int'> <type 'int'>
    #RewardMod.reward rewardType=1 goodsId=1 goodsNum=1 return [204L] <type 'int'> <type 'int'> <type 'int'>
    print c.rewardMany(91002, {"WarId":101},[{'GoodsType':1,'GoodsId':1,'GoodsNum':1},
                          {'GoodsType':2,'GoodsId':101,'GoodsNum':2},
                          {'GoodsType':4,'GoodsId':1,'GoodsNum':1},
                          {'GoodsType':5,'GoodsId':10,'GoodsNum':1},])

    
    
    
    