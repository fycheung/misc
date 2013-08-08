# -*- coding:utf-8 -*-
# author:Yew
# date:2013-3-28
# 游戏外部接口,控制层 (以游戏逻辑为主,尽量不要数据库的查询)

from sgLib.core import Gcore, inspector
from sgLib import common
import time
import datetime


class FriendUI(object):
    def __init__(self, uid):
        self.uid = uid
        self.mod = Gcore.getMod('Friend', uid)

    def FriendList(self, param = {}):
        '''获得好友列表'''
        optId = 19001
        lists = self.mod.getFriendList()
        friendList = common.list2dict(lists)

        data = {'FriendList': friendList}
        data['FriendNum'] = self.mod.countFriend(2)
        uLimitNum = Gcore.getCfg('tb_cfg_friend_limit', self.mod.getUserLevel(), 'FriendNumLimit')
        #data['FriendOnlineNum']=self.mod.countFriend(2,True)
        data['FriendMaxNum'] = uLimitNum
        return Gcore.out(optId, data)
    
    def ApplyList(self, param = {}):
        '''获得好友申请列表'''
        optId = 19002
        lists = self.mod.getApplyList()
        applyList = common.list2dict(lists)
        data = {'ApplyList': applyList}
        data['FriendNum'] = self.mod.countFriend(2)
        data['FriendOnlineNum'] = self.mod.countFriend(2, True)
        return Gcore.out(optId, data)

    @inspector(19003, ['FriendUserIds', 'HandleType'])
    def HandleApply(self, param = {}):
        '''处理好友申请'''
        optId = 19003
        timeStamp = param['ClientTime']
        friendUserIds = param['FriendUserIds']
        handleType = param['HandleType']
        recordData = {}#任务记录
        if not friendUserIds:
            return Gcore.error(optId, -19003999)#参数错误
        
        if handleType == 0:
            '''拒绝添加'''
            #self.mod.updateFriendShip(friendUserIds, self.uid, 0, timeStamp)
            self.mod.refuseApply(friendUserIds, self.uid, timeStamp)
            mailMod = Gcore.getMod('Mail', self.uid)
            nickName = self.mod.getUserInfo('NickName')
            #mailMod.sendMail(friendUserIds, '拒绝好友申请', nickName+'拒绝了你的好友申请', 1)#拒绝好友，调用邮件发送信息给对方
            for toUserId in friendUserIds:
                mailMod.sendSystemMail(toUserId, [], optId, other=[nickName,])
            
        elif handleType == 1:
            '''确认添加'''
            #判断玩家自己的好友数是否已达上限
            uLimitNum = Gcore.getCfg('tb_cfg_friend_limit', self.mod.getUserLevel(), 'FriendNumLimit')
            uNowNum = self.mod.countFriend(2)
            if uNowNum >= uLimitNum:
                return Gcore.error(optId, -19003001)#好友超过上限
            #如果对方好友已达上限，则拒绝本次添加请求
            validId = []
            for fid in friendUserIds:
                tmpMod = Gcore.getMod('Friend', fid)
                limitNum = Gcore.getCfg('tb_cfg_friend_limit', tmpMod.getUserLevel(), 'FriendNumLimit')
                nowNum = tmpMod.countFriend(2)
                if nowNum >= limitNum:
                    #self.mod.updateFriendShip(fid, self.uid, 0, timeStamp)
                    self.mod.refuseApply(fid, self.uid, timeStamp)
                else:
                    validId.append(fid)
            
            if len(validId) == 0:
                return Gcore.error(optId, -19003002)
            #如果玩家添加的好友数多于所能添加的个数，则失败
            if uNowNum + len(validId) > uLimitNum:
                return Gcore.error(optId, -19003001)
            
            for friendUserId in validId:
                self.mod.insFriendShip(self.uid, friendUserId, 2)
                self.mod.updateFriendShip(friendUserId, self.uid, 2, timeStamp)
                
                recordData = {'uid':self.uid,'ValType':0,'Val':1}
                Gcore.getMod('Mission',friendUserId).missionTrigger(optId)#触发被同意好友更新
                
        else:
            return Gcore.error(optId, -19003999)#参数错误
        
        return Gcore.out(optId, {},mission=recordData)
    

    def GetUserByRank(self,param={}):
        '''随机获取用户'''
        optId = 19005
        userCamp = self.mod.getUserCamp()
        result = self.mod.getUserByRand(userCamp)
        return Gcore.out(optId, {'RankList': result})

    @inspector(19006,['FriendUserId'])
    def DeleteFriend(self,param={}):
        '''删除好友'''
        optId=19006
        friendUserId=param['FriendUserId']
        self.mod.updateFriendShip(self.uid,friendUserId,3)
        self.mod.updateFriendShip(friendUserId,self.uid,3)          
        return Gcore.out(optId,{})

    @inspector(19007, ['FriendUserId'])
    def CheckFriend(self, param = {}):
        '''查看好友'''
        optId = 19007
        friendUserId = param['FriendUserId']
        if not self.mod.validateUser(friendUserId):
            return Gcore.error(optId, -19007001)#用户不存在
        
        player = Gcore.getMod('Player', friendUserId)
        fileds = ['UserId', 'NickName', 'UserLevel', 'VipLevel', 'UserIcon', 'UserHonour', 'UserCamp']
        result = player.getUserBaseInfo(fileds)       #获得基本信息
        result['Rank'] = player.getHonRankNum(result)
        
        buildingClub = Gcore.getMod('Building_club', friendUserId)
        cId = buildingClub.getUserClubId()
        clubInfo = buildingClub.getClubInfo(cId, 'ClubName')
        if clubInfo:
            result['ClubName'] = clubInfo['ClubName']     #获得军团名字
        else:
            result['ClubName'] = ''
        general = Gcore.getMod('General', friendUserId)
        generalNum = general.getMyGenerals('count(1) as gNum')
        result['GeneralNum'] = generalNum[0]['gNum'] #获得武将个数

        buildingNum = self.mod.getBuildingCount(friendUserId)
        result['BuildingNum'] = buildingNum #获得建筑数量

        return Gcore.out(optId, result)

    @inspector(19008,['FriendUserId'])
    def CheckGeneral(self,param={}):
        '''查看武将'''
        optId = 19008
        friendUserId = param['FriendUserId']
        if not self.mod.validateUser(friendUserId):
            return Gcore.error(optId, -19010001)#用户不存在
        
        general = Gcore.getMod('General', friendUserId)
            
        generals = general.getLatestGeneralInfo()
        generals = generals if generals else ()
        
        return Gcore.out(optId, {'GeneralList': generals})        
        
    
    @inspector(19010,['NickName'])
    def ApplyFriendByName(self, param={}):
        '''通过名字申请好友'''
        optId = 19010
        nickName = param['NickName'].strip()
        
        n = Gcore.getCfg('tb_cfg_friend_limit', self.mod.getUserLevel(), 'FriendNumLimit')
        if self.mod.countFriend(2) >= n:
            return Gcore.error(optId, -19010004)#当前好友已到达上限
        
        if not nickName:
            return Gcore.error(optId, -19010001)
        friendUserInfo = self.mod.getUserByNickName(nickName)
        if not friendUserInfo:
            return Gcore.error(optId, -19010001)#用户不存在 
        if self.uid == friendUserInfo['UserId']:
            return Gcore.error(optId, -19010002)#不能添加自己
        if self.mod.getUserCamp() != friendUserInfo['UserCamp']:
            return Gcore.error(optId, -19010005)#不可加不同阵营的玩家为好友
        
        tmpMod = Gcore.getMod('Friend', friendUserInfo['UserId'])
        limitNum = Gcore.getCfg('tb_cfg_friend_limit', tmpMod.getUserLevel(), 'FriendNumLimit')
        nowNum = tmpMod.countFriend(2)
        if nowNum >= limitNum:
            return Gcore.error(optId, -19010007)#对方好友已达上限
        
        friendShipInfo = self.mod.getFriendShipInfo(self.uid, friendUserInfo['UserId'])
        now = Gcore.common.nowtime()
        isPush = True
        if friendShipInfo:
            if friendShipInfo['FriendStatus'] == 2:
                return Gcore.error(optId, -19010003)#对方已经是好友
            if friendShipInfo['FriendStatus'] == 3 and now-friendShipInfo['LastChangeTime'] < 1800:              
                return Gcore.error(optId, -19010006)#好友删除30分钟内不能再次添加
            if friendShipInfo['FriendStatus'] == 1:
                isPush = False
        self.mod.insFriendShip(self.uid, friendUserInfo['UserId'], 1, isPush)
        return Gcore.out(optId, {})
    
    def CountApply(self,param={}):
        '''统计未处理好友申请个数'''
        optId=19011
        applyNum= self.mod.countApply()
        return Gcore.out(optId,{'ApplyNum':applyNum})
    
    @inspector(19012, ['FriendUserId'])
    def CountFriendGeneral(self, param = {}):
        '''用于获取好友的武将数量'''
        
        optId = 19012
        friendUid = param['FriendUserId']
        general = Gcore.getMod('General', friendUid)
        generalInfo = general.getMyGenerals('count(1) as gNum')
        generalNum = generalInfo[0]['gNum'] #获得武将个数
        
        return Gcore.out(optId, {'GeneralNum': generalNum})
    
    @inspector(19004,['FriendUserId'])
    def ApplyFriend(self,param={}):
        '''申请好友(暂无用)'''
        optId=19004
        return Gcore.out(optId,{})
                


def test():
    uid = 43357
    f = FriendUI(uid)
    f.ApplyList()
    
if __name__ == '__main__':
    '''调试'''
#     test()
    uid=1032
    f=FriendUI(uid)
    #Gcore.push(106,43385)
    #f.dropic()
    #f.ApplyFriend({'FriendUserId':1012})
    #f.ApplyFriendByName({'NickName':'屈契'})
    #f.ApplyList()
    #friendIds=[1032]
    #f.HandleApply({'FriendUserIds':friendIds,'HandleType':1})
#为ID43357添加好友申请
#     uid = 43357
#     f = FriendUI(uid)
#     for i in range(1007, 1040):
#         row={'UserId': i, 'FriendUserId': f.uid, 'Favor': 0, 'FriendStatus': 1
#               ,'VisitTime':0,'LastChangeTime':int(time.time())}
#         row_check={'UserId':i,'FriendUserId':f.uid}
#         f.mod.db.insert_update('tb_friend',row,row_check)
    #f.FriendList()
    #f.GetUserByRank()
    #f.DeleteFriend({'FriendUserId':43280})
#     f.CheckFriend({'FriendUserId':1013})
    #f.CheckGeneral({'FriendUserId':1003})
    #f.VisitFriend({'FriendUserId':1001})
    #print f.CountApply()
        

        

        
    

    

    
     
