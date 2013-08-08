# -*- coding:utf-8 -*-
# author:Lizr
# date:2012-12-21
# 玩家相关接口

import math
from sgLib.core import Gcore
from sgLib.core import inspector
import sgLib.common as com


class PlayerUI(object):
    """玩家信息"""
    def __init__(self, uid=0):
        '''注释'''
        self.uid = uid 
        self.mod = Gcore.getMod('Player', uid)
#        self.accountMod = Gcore.getMod(AccountMod, uid)
    
    def WorkerExpand(self,p={}):
        '''添加一个工匠,成功添加后返回当前工匠信息'''
        optId = 13001
        # 获取当前工匠信息
        userInfo = self.mod.getUserBaseInfo()
        workerNum = userInfo.get('WorkerNumber')#当前工匠数
        workerCfg = Gcore.loadCfg(Gcore.defined.CFG_BUILDING)
        if workerCfg['MaxWorkerNum']<=workerNum:
            return Gcore.error(optId,-13001001)#工匠数量已达到最大
        
        #计算增加工匠金额并支付
        workerPrice = workerCfg['HireWorkerPrice'][str(workerNum+1)]
        coinMod = Gcore.getMod('Coin',self.uid)
        flag = coinMod.PayCoin(optId,1,workerPrice,'PlayerUI.WorkerExpand',p)
        if flag>0:
            self.mod.addWorker(workerNum)
#            workerInfo['WorkerFree'] = workerInfo['WorkerFree']+1
#            workerInfo['WorkerTotal'] = workerInfo['WorkerTotal']+1
            recordData = {'uid':self.uid,'ValType':0,'Val':1}#成就、任务记录 
            return Gcore.out(optId,{'WorkerTotal':workerNum+1},mission=recordData)
        elif flag==-2:
            return Gcore.error(optId,-13001994)#货币不足
        else:
            return Gcore.error(optId,-13001995)#支付失败
        
    @inspector(13002,['PageNum'])
    def GetHonRanking(self,p={}):
        '''荣誉值排名'''
        optId = 13002
        pageSize = Gcore.loadCfg(Gcore.defined.CFG_PLAYER).get('HonourRankPS')
        pageNum = p.get('PageNum',0)
        count = self.mod.getUserNum()
        maxPage = int(math.ceil(float(count)/pageSize))
        if pageNum<1:
            pageNum=1
        elif 0<maxPage<pageNum:
            pageNum = maxPage
        offset = (pageNum-1)*pageSize
        us = self.mod.getHonRanking(offset,pageSize)
        us = com.list2dict(us, offset+1)
        
        #我的名次
        if pageNum==1:
            myRank = self.mod.getHonRankNum()
        else:
            myRank = 0
        return Gcore.out(optId,{'HRank':us,'PageNum':pageNum,'MaxPage':maxPage,'MyRank':myRank})
        
    @inspector(13051,['RID','RVAL'])
    def PayForGold(self,p={}):
        '''充值黄金'''
        optId = 13051
        rId = p.get('RID')
        rVal = p.get('RVAL')
        vipCfg = Gcore.getCfg('tb_cfg_vip_recharge',rId)
        if vipCfg is None:
            return Gcore.error(optId,-13051999)#参数错误
        elif rVal!=vipCfg.get('RechargeVal'):
            return Gcore.error(optId,-13051001)#充值金额不对
        gainGold = vipCfg.get('GoldVal')
        coinMod = Gcore.getMod('Coin',self.uid)
        flag = coinMod.GainCoin(optId,1,gainGold,'PlayerUI.PayForGold',p)
        level = 0
        if flag:
            level = self.mod.vipAddTotal(optId, gainGold)
            
        recordData = {'uid':self.uid,'ValType':0,'Val':flag}#成就记录
        return Gcore.out(optId,{'VIP':level,'Gold':flag},achieve=recordData,mission=recordData)
    
    def GetVipInfo(self,p={}):
        '''获取VIP信息'''
        optId = 13052
        fields = ['VipLevel','VipTotalPay']
        vip = self.mod.getUserBaseInfo(fields)
        return Gcore.out(optId,vip)
    
    @inspector(13003,['UserId'])
    def GetBaseInfo(self,param={}):
        optId = 13003
        userId=param['UserId']
        modPlay=Gcore.getMod('Player',userId)
        
        fileds=['NickName','UserLevel','VipLevel','UserIcon','UserHonour','UserCamp','UserExp']
        result= modPlay.getUserBaseInfo(fileds)
        if result is None:
            return Gcore.error(optId,-13003001)#用户不存在
        
        result['Rank']=modPlay.getHonRankNum(result)
        
        buildingClub = Gcore.getMod('Building_club',userId)
        cId=buildingClub.getUserClubId()
        clubInfo=buildingClub.getClubInfo(cId,'ClubName')
        if clubInfo:
            result['ClubName']=clubInfo['ClubName']     #获得军团名字
        else:
            result['ClubName']=''
            
        general=Gcore.getMod('General', userId)
        generalNum=general.getMyGenerals('count(1) as gNum')
        result['GeneralNum']=generalNum[0]['gNum'] #获得武将个数
        
        modFriend=Gcore.getMod('Friend',userId)
        buildingNum=modFriend.getBuildingCount(userId)
        result['BuildingNum']=buildingNum 
        
        return Gcore.out(optId,result)
    
    def GetPlayerInfo(self,p={}):
        '''获取主角相关登录信息 (其他场景返回城市 不要走登录流程 用这个协议号取)'''
        optId = 13004
        playerInfo = self.mod.PlayerInfo()
        return Gcore.out(optId,playerInfo)
    
    @inspector(13005,['ArmyAdviserId'])
    def SetArmyAdviserId(self,p={}):
        '''记录玩家所选军师'''
        optId = 13005
        self.mod.setUserProfile({'ArmyAdviserId':p.get('ArmyAdviserId')})
        return Gcore.out(optId)
    
    @inspector(13006,['GuideProcessId'])
    def SetGuideProcessId(self,p={}):
        '''记录玩家指引进度'''
        optId = 13006
        self.mod.setUserProfile( {'GuideProcessId':p.get('GuideProcessId')} )
        self.mod.guideCompleteLog( p.get('GuideProcessId') ) #指引进度记录
        return Gcore.out(optId)
        
        
def _test():
    uid = 1001
    c = PlayerUI(uid)
#     print Gcore.loadCfg(Gcore.defined.CFG_PLAYER).get('HonourRankPS')
#     print c.PayForGold({'RID':1,'RVAL':'0.99'})
#    c.WorkerExpand2()
#     c.GetHonRanking({'PageNum':1})
#    c.GetBaseInfo({'UserId':1001})
#     print c.GetPlayerInfo()
#     print c.GetVipInfo()
#     c.SetArmyAdviserId({'ArmyAdviserId':1})
    c.SetGuideProcessId({'GuideProcessId':2})

    
if __name__ == '__main__':
    _test()
