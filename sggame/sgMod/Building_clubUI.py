# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-3-15
# 游戏外部接口 军团

import math
from sgLib.core import Gcore
from sgLib.core import inspector

import sgLib.common as com
import sgLib.defined as defined

class Building_clubUI(object):
    """测试 ModId:15060~15089 """
    def __init__(self, uid):
        '''注释'''
        self.uid = uid
        self.mod = Gcore.getMod('Building_club',uid)

    @inspector(15060,['LogoId','ClubName'])
    def CreateClub(self,p={}):
        '''创建军团
        @logoId :1-6
        '''
        optId = 15060
        CfgClub = Gcore.loadCfg(defined.CFG_BUILDING_CLUB)
        
        s_Name = p.get('ClubName')
        LogoId = p.get('LogoId')
        i_Min = CfgClub.get('ClubNameLimitMin')
        i_Max = CfgClub.get('ClubNameLimitMax')
    
        flag = com.filterInput(s_Name, i_Min, i_Max)
        if flag == -1:
            return Gcore.error(optId, -15060993) #长度不符合要求
        elif flag == -2:
            return Gcore.error(optId, -15060992) #不能含有敏感字符
        building = self.mod.getClubBuildingInfo()
        if building is None:
            return  Gcore.error(optId,-15060901)#外史院建筑不存在
        MyClubId = self.mod.getUserClubId()
        if MyClubId:
            return Gcore.error(optId, -15060001) #你已加入军团，不能创建
        
        if self.mod.hadSameName(s_Name):
            return Gcore.error(optId, -15060002) #该军团名称已存在
            

        #开始支付
        CoinType = CfgClub.get('ClubCreateCostType')
        CoinValue = CfgClub.get('ClubCreateCost')
        
        modCoin = Gcore.getMod('Coin',self.uid)
        classMethod = self.__class__.__name__+'.CreateClub'
        result = modCoin.PayCoin(optId, CoinType, CoinValue, classMethod, p)
        
        
        if result < 0:
            return Gcore.error(optId,-15060995) #支付失败
        else:
            ClubId = self.mod.createClub(LogoId,s_Name) #创建军团
            Gcore.setUserData(self.uid, {'ClubId':ClubId})#更新用户缓存
            body = {'ClubId':ClubId}
            recordData = {'uid':self.uid,'ValType':0,'Val':1}#任务
            return Gcore.out(optId,body,mission=recordData)
        
    
    @inspector(15061,['CoinType','CoinValue'])
    def Devote(self,p={}):
        '''贡献
        :todo我的贡献值未添加
        '''
        optId = 15061
        CoinType = int( p.get('CoinType') )
        CoinValue = p.get('CoinValue')
        if CoinType not in (2,3):
            return Gcore.error(optId,-15061998)
        building = self.mod.getClubBuildingInfo()
        if building is None:
            return  Gcore.error(optId,-15061901)#外史院建筑不存在
        ClubId = self.mod.getUserClubId()
        if not ClubId:
            return  Gcore.error(optId,-15061920)#军团不存在
        
        CfgClub = Gcore.loadCfg(defined.CFG_BUILDING_CLUB)
        ClubGiveBase = CfgClub.get('ClubGiveBase').get( str(CoinType) ) #货币与贡献点的转换基数 1000
        DevoteNum = CoinValue/ClubGiveBase
        
        TodayDevoteNum  = self.mod.getTodayDevote(ClubId,2) #获取当天贡献数量
        
        MyClubInfo = self.mod.getClubInfo(ClubId)
        
        ClubLevel = building.get('BuildingRealLevel')#todo外史院等级
        MemberDevoteMax = Gcore.getCfg('tb_cfg_building_up',(15,ClubLevel),'SaveValue')#每天贡献货币数量
        if TodayDevoteNum + CoinValue> MemberDevoteMax:
            return Gcore.error(optId,-15061001) #贡献越出今天最大限制
        
        #开始支付
        modCoin = Gcore.getMod('Coin',self.uid)
        classMethod = self.__class__.__name__+'.Devote'
        result = modCoin.PayCoin(optId, CoinType, CoinValue, classMethod, p)
        
        recordData = {'uid':self.uid,'ValType':CoinType,'Val':CoinValue}#成就记录
        if result < 0:
            return Gcore.error(optId,-15061995) #支付失败
        else:
            ClubInfo = self.mod.clubAddExp(MyClubInfo,DevoteNum) #增加军团经验
            #贡献记录和增加贡献值
            self.mod.gainDeveote(ClubId,1,coinType=CoinType,coinValue=CoinValue)
            recordData = {'uid':self.uid,'ValType':CoinType,'Val':CoinValue}#成就,任务记录
            
            return Gcore.out(optId,{'ClubInfo':ClubInfo,'DevLeft':MemberDevoteMax-(TodayDevoteNum+CoinValue)},achieve=recordData,mission=recordData )
    
    def GetMyClub(self,p={}):
        '''获取我的军团信息
        '''
        optId = 15062
        clubId = self.mod.getUserClubId()
        clubInfo = {'BaseInfo':0,'MemberNum':0,
                    'DevoteValue':0,'LeaderInfo':0,
                    'HasClub':0,'MyInfo':0}
        if not clubId:
            return Gcore.out(optId,clubInfo)#没有军团
        ClubInfo = self.mod.getClubInfo(clubId)#军团基础信息
        
        #by Lizr 前台没有这些值,,抽取
        del ClubInfo['ClubTotalExp']
        del ClubInfo['ClubLevelTotalExp']
        del ClubInfo['CreatDate']
        
        clubInfo['BaseInfo'] = ClubInfo
        clubInfo['MemberNum'] = self.mod.getClubMemberNum(clubId)#军团成员数量
        clubInfo['DevoteValue'] = self.mod.getTodayDevote(clubId,2)#当天贡献值
        clubInfo['LeaderInfo'] = self.mod.getClubLeader(clubId)#团长信息
        clubInfo['MyInfo'] = self.mod.getMemberInfo(clubId,self.uid,['DevoteCurrent','DevoteTotal'])
        clubInfo['HasClub'] = 1
        clubInfo['DevoteLogs'] = com.list2dict(self.mod.getDevoteLogs(clubId), 1)
        clubInfo['DevoteBase'] = Gcore.loadCfg(defined.CFG_BUILDING_CLUB).get('ClubGiveBase')
        
        return Gcore.out(optId,clubInfo)
        
    @inspector(15063,['PageNum'])   
    def GetClubList(self,p={}):
        '''
        :获取可加入军团列表
        '''
        optId = 15063
        pageNum = p.get('PageNum',0)
        pageSize = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_CLUB ).get('ClubPS')
        clubNum = self.mod.getClubNum()
        maxPage = int(math.ceil(float(clubNum)/pageSize))
        if pageNum<1:
            pageNum=1
        if 0<maxPage<pageNum:
            pageNum = maxPage
        offset = (pageNum-1)*pageSize
        if clubNum>0:
            clubList = self.mod.getClubList(offset,pageSize)
        else:
            clubList = []
        return Gcore.out(optId,{'Clubs':clubList,'PageNum':pageNum,'MaxPage':maxPage})
    
    @inspector(15064,['ClubId']) 
    def ApplyClub(self,p={}):
        '''
        :申请加入
        '''
        optId = 15064
        clubId = p['ClubId']
        building = self.mod.getClubBuildingInfo()
        if building is None:
            return  Gcore.error(optId,-15064901)#外史院建筑不存在
        clubInfo = self.mod.getClubInfo(clubId)
        if not clubInfo:
            return Gcore.error(optId,-15064920)#军团不存在
        if self.mod.getUserClubId():
            return Gcore.error(optId,-15064001)#只能加入一个军团
        
        if not self.mod.validApplyInterval():
            return Gcore.error(optId,-15064004)#离上次退出军团时间间隔不合法
        
        memberNum = self.mod.getClubMemberNum(clubId)
        if memberNum.get('CurNum')>=memberNum.get('MaxNum'):
            return Gcore.error(optId,-15064002)#军团成员已满
        allowState = clubInfo.get('AllowState')
        if allowState == 1:#需要审核
            self.mod.applyClub(clubId)
            return Gcore.out(optId,{'Passed':0,'ClubId':clubId})#申请成功，审核中
        elif allowState ==2:#不需审核
            self.mod.applyClub(clubId)
            self.mod.agreeApply(optId, clubId, self.uid)
            Gcore.setUserData(self.uid, {'ClubId':clubId})#更新用户缓存
            
            recordData = {'uid':self.uid,'ValType':0,'Val':1}#任务
            return Gcore.out(optId,{'Passed':1,'ClubId':clubId},mission=recordData)#成功加入军团
        else:
            return Gcore.out(optId,{'Passed':2})#不允许加入
        
    @inspector(15065,['LogoId','ClubNotice','AllowState'])     
    def ModifyClub(self,p={}):
        '''
        :修改军团信息（团长）
        '''
        optId = 15065
        logoId = p.get('LogoId')
        clubNotice = p.get('ClubNotice')
        allowState = p.get('AllowState')
        building = self.mod.getClubBuildingInfo()
        if building is None:
            return  Gcore.error(optId,-15065901)#外史院建筑不存在
        cfgClub = Gcore.loadCfg(defined.CFG_BUILDING_CLUB)
        noticeLimit = cfgClub.get('ClubNoticeLimit')
        flag = com.filterInput(clubNotice,0,noticeLimit)
        if flag == -1:
            return Gcore.error(optId, -15065993) #长度不符合要求
        elif flag == -2:
            return Gcore.error(optId, -15065992) #不能含有敏感字符
        if logoId not in range(1,7):
            return Gcore.error(optId,-15065999)#参数错误
        clubId = self.mod.getUserClubId()
        if not clubId:
            return Gcore.error(optId,-15065920)#军团不存在
        clubLeader = self.mod.getClubLeader(clubId)
        if self.uid != clubLeader.get('UserId'):
            return Gcore.error(optId,-15065998)#非法权限
        data = {'ClubLogoId':logoId,'ClubNotice':clubNotice,'AllowState':allowState}
        self.mod.modifyClub(clubId,data)
        return Gcore.out(optId,data)

 
     
    @inspector(15067,['UserId'])   
    def SetClubLeader(self,p={}):
        '''
        :任命团长（团长）
        '''
        optId = 15067
        userId = p.get('UserId')
        building = self.mod.getClubBuildingInfo()
        if building is None:
            return  Gcore.error(optId,-15067901)#外史院建筑不存在
        clubId = self.mod.getUserClubId()
        if not clubId:
            return Gcore.error(optId,-15067920)#军团不存在
        clubLeader = self.mod.getClubLeader(clubId)
        if self.uid != clubLeader.get('UserId') or self.uid ==userId:
            return Gcore.error(optId,-15067998)#非法权限
        userClubId = self.mod.getUserClubId(userId)
        if userClubId != clubId:
            return Gcore.error(optId,-15067998)#非法权限
        self.mod.setClubLeader(optId, clubId, userId)
        return Gcore.out(optId)
    
    @inspector(15068,['UserId'])
    def DismissMember(self,p={}):
        '''
        :开除成员（团长操作）
        '''
        optId = 15068
        userId = p.get('UserId')
        building = self.mod.getClubBuildingInfo()
        if building is None:
            return  Gcore.error(optId,-15068901)#外史院建筑不存在
        clubId = self.mod.getUserClubId()
        if not clubId:
            return Gcore.error(optId,-15068920)#军团不存在
        clubLeader = self.mod.getClubLeader(clubId)
        if self.uid != clubLeader.get('UserId') or self.uid == userId:
            return Gcore.error(optId,-15068998)#非法权限
        userClubId = self.mod.getUserClubId(userId)
        if userClubId != clubId:
            return Gcore.error(optId,-15068002)#该用户非军团成员
        self.mod.dismissMember(optId, clubId, userId)
        Gcore.setUserData(userId, {'ClubId':0})#更新被开除成员的军团信息
        Gcore.push(113,userId,{'ClubId':0})#推送军团ID
        return Gcore.out(optId)
    
    
    @inspector(15070,['UserId'])    
    def AgreeApply(self,p={}):
        '''
        :同意申请
        '''
        optId = 15070
        userId = p.get('UserId')
        building = self.mod.getClubBuildingInfo()
        if building is None:
            return  Gcore.error(optId,-15070901)#外史院建筑不存在
        clubId = self.mod.getUserClubId()
        if not clubId:
            return Gcore.error(optId,-15070920)#军团不存在
        
        memberNum = self.mod.getClubMemberNum(clubId)
        if memberNum.get('CurNum')>=memberNum.get('MaxNum'):
            return Gcore.error(optId,-15070001)#军团成员已满
        
        if self.uid == userId:
            return Gcore.error(optId, -15070998)#对自己操作，非法权限
        memberInfo = self.mod.getMemberInfo(clubId,userId)
        if not memberInfo:
            return Gcore.error(optId,-15070002)#没有申请记录
        elif memberInfo.get('MemberState') != 0 and memberInfo.get('MemberState')!=4:
            return Gcore.error(optId,-15070996)#操作失败
        self.mod.agreeApply(optId, clubId, userId)
        Gcore.setUserData(userId, {'ClubId':clubId})#成员被允许加入，更新的军团信息
        Gcore.push(113,userId,{'ClubId':clubId})#推送军团ID
        recordData = {'uid':userId,'ValType':0,'Val':1}
        return Gcore.out(optId,mission=recordData)
        
    @inspector(15071,['UserId'])    
    def RefuseApply(self,p={}):
        '''
        :拒绝申请
        '''
        optId = 15071
        userId = p.get('UserId')
        building = self.mod.getClubBuildingInfo()
        if building is None:
            return  Gcore.error(optId,-15071901)#外史院建筑不存在
        clubId = self.mod.getUserClubId()
        if not clubId:
            return Gcore.error(optId,-15071920)#军团不存在
        memberInfo = self.mod.getMemberInfo(clubId,userId)
        if not memberInfo:
            return Gcore.error(optId,-15070996)#成员不存在
        elif memberInfo.get('MemberState') != 0 and memberInfo.get('MemberState')!=4:
            return Gcore.error(optId,-15070996)#操作失败
        self.mod.refuseApply(optId, clubId, userId)
        return Gcore.out(optId)
    
    def ExitClub(self,p={}):
        '''退出军团'''
        optId = 15072
        building = self.mod.getClubBuildingInfo()
        if building is None:
            return  Gcore.error(optId,-15072901)#外史院建筑不存在
        clubId = self.mod.getUserClubId()
        if not clubId:
            return Gcore.error(optId,-15072920)#军团不存在
        userType = 3#普通成员
        clubLeader = self.mod.getClubLeader(clubId)
        if self.uid == clubLeader.get('UserId'):
            userType = 1#团长
        self.mod.dismissMember(optId, clubId, self.uid, way=3, userType=userType)
        Gcore.setUserData(self.uid, {'ClubId':0})#更新用户缓存
        return Gcore.out(optId,{})
          
    def GetClubTechs(self,p={}):
        '''
        :获取军团科技等级
        '''
        optId = 15075
        clubId = self.mod.getUserClubId()
        if not clubId:
            clubLevel = 0
            devote = 0
        else:
            clubInfo = self.mod.getClubInfo(clubId)
            clubLevel = clubInfo.get('ClubLevel')
            devote = self.mod.getMemberInfo(clubId,self.uid,['DevoteCurrent']).get('DevoteCurrent')
        levels = self.mod.calClubTechs(clubLevel)
        result = {'ClubTechs':levels,'ClubLevel':clubLevel,'DevoteCurrent':devote}
        return Gcore.out(optId,result)
#    
        
    @inspector(15076,['ClubTechType'])    
    def UpgradeClubTech(self,p={}):
        '''
        :升级军团科技
        #todo加一个升级完返回升级后的等级
        '''
        optId = 15076
        techType = p.get('ClubTechType')
        if techType not in range(1,11):
            return Gcore.error(optId,-15076999)#参数错误
        building = self.mod.getClubBuildingInfo()
        if building is None:
            return  Gcore.error(optId,-15076901)#外史院建筑不存在
        clubId = self.mod.getUserClubId()
        if not clubId:
            return Gcore.error(optId,-15076920)#军团不存在
        clubInfo = self.mod.getClubInfo(clubId)
        clubLevel = clubInfo.get('ClubLevel')
        techLevel = self.mod.getClubTechLevel(techType)
        openLevel = Gcore.getCfg('tb_cfg_club_up',clubLevel,'OpenLevelTech'+str(techType))
        if techLevel >= openLevel:
            return Gcore.error(optId,-15076001)#已达最大等级

        cost = Gcore.getCfg('tb_cfg_club_tech',(techType,techLevel+1),'LearnCost')
        
#         print '科技类型',techType
#         print '科技等级',techLevel
#         print '学习费用',cost
        
        flag = self.mod.payDevote(clubId,cost)#成功返回余额
        if flag<0:
            return Gcore.error(optId,-15076995)#支付失败
        newLevel = self.mod.upgradeClubTech(techType)
        recordData = {'uid':self.uid,'ValType':0,'Val':1,'TechType':techType,'TechLevel':newLevel}#成就记录
        return Gcore.out(optId,{'Left':flag,'ClubTechType':techType,'Level':newLevel},achieve=recordData,mission=recordData)
    
        
    @inspector(15073,['ListView','PageNum','SortField','SortWay'])
    def GetCrewList(self,p={}):
        '''查询军团成员列表/申请列表
        @param ListView: 1:成员列表2：申请列表 '''
        optId = 15073
        listView = p['ListView']
        pageNum = p['PageNum']
        sortWay = 'ASC' if p['SortWay']==0 else 'DESC'
        sortField = p['SortField']
        if sortField == 1:
            sortField = 'u.VipLevel '+sortWay
        elif sortField == 2:
            sortField = 'm.DevoteTotal '+sortWay
        else:
            sortField = 'u.UserHonour '+sortWay
        clubId = self.mod.getUserClubId()
        if not clubId:
            return Gcore.error(optId,-15066920)#军团不存在
        pageSize = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_CLUB ).get('MemPS')
        memberNum = self.mod.getCrewNum(listView,clubId)
        maxPage = int(math.ceil(float(memberNum)/pageSize))
        if 0<maxPage<pageNum:
            pageNum = maxPage
        if pageNum<1:
            pageNum = 1
        offset = (pageNum-1)*pageSize
#        end = offset+pageSize
        if memberNum>0:
            members = self.mod.getCrewList(listView,clubId,sortField,offset,pageSize)
        else:
            members = []
        clubLevel = self.mod.getClubInfo(clubId).get('ClubLevel')
        memberNum = self.mod.getClubMemberNum(clubId)
        return Gcore.out(optId,{'ClubLevel':clubLevel,'MemberNum':memberNum,'Members':members,'PageNum':pageNum,'MaxPage':maxPage})
    
    def CheckClubExist(self,p={}):
        '''检查军团是否存在'''
        optId = 15080
        clubId = self.mod.getUserClubId()
        if clubId:
            curDevote = self.mod.getMemberInfo(clubId,self.uid,['DevoteCurrent']).get('DevoteCurrent',0)
            return Gcore.out(optId,{'IsExisted':1,'DevoteCurrent':curDevote})
        else:
            return Gcore.out(optId,{'IsExisted':0})
    
    @inspector(15082,['BoxType'])
    def OpenBox(self,p={}):
        '''开宝箱'''
        optId = 15082
        boxType = p['BoxType']
        boxCfg = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_CLUB).get('BoxCost')
        boxTypes = [int(i) for i in boxCfg.keys()]
        if boxType not in boxTypes:
            return Gcore.error(optId, -15082999)#参数错误
        building = self.mod.getClubBuildingInfo()
        if building is None:
            return  Gcore.error(optId,-15082901)#外史院建筑不存在
        clubId = self.mod.getUserClubId()
        if not clubId:
            return Gcore.error(optId,-15082920)#军团不存在
        
        #支付贡献
        cost = boxCfg.get(str(boxType))
        left = self.mod.payDevote(clubId,cost)
#         left = 1
        
        #支付成功，开始抽奖
        if left>=0:
            goodsCfg = Gcore.getCfg('tb_cfg_club_box',boxType)
            lucky = com.Choice(goodsCfg)
            rType = lucky.get('RewardType')
            goodsId = lucky['GoodsId']
            goodsNum = lucky['GoodsNum']
            body ={'Left':left,'RewardType':rType,
                   'GoodsId':goodsId,
                   'GoodsNum':goodsNum}
            equipIds = []
#             if rType in [1,2,3]:#装备,道具，资源
            ids = Gcore.getMod('Reward',self.uid).reward(optId,p,rType,goodsId,goodsNum)
            if rType==1:
                if isinstance(ids,list):
                    equipIds = ids
                    
            body['EIDS'] = equipIds
            self.mod.insertBoxLog(clubId,boxType,lucky)
            
            body['Logs'] = self.mod.getBoxLogList(1,clubId,offset=0,pageSize=2,timeLimit=False)
            recordData = {'uid':self.uid,'ValType':0,'Val':1}#成就,任务记录
            
            return Gcore.out(optId,body,mission=recordData)
        else:
            return Gcore.error(optId,-15082002)# 支付失败
        
    
    @inspector(15083,['ListView','PageNum'])
    def GetBoxLogs(self,p={}):
        '''查询获奖记录
        @param ListView: 显示列表 1：军团所有成员 2：玩家自己3:军团内两条记录
        '''
        optId = 15083
        listView = p['ListView']
        pageNum = p['PageNum']
        clubId = self.mod.getUserClubId()
        if not clubId:
            return Gcore.error(optId,-15083920)#军团不存在
        pageSize = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_CLUB ).get('BoxPS')
        logNum = self.mod.getBoxLogNum(listView,clubId)
        
        maxPage = int(math.ceil(float(logNum)/pageSize))
        if 0<maxPage<pageNum:
            pageNum = maxPage
        if pageNum<1:
            pageNum = 1
        offset = (pageNum-1)*pageSize
        myLog = []
        if logNum>0:
            if listView==1:
                logs = self.mod.getBoxLogList(listView,clubId,offset,pageSize)
                if pageNum==1:#第二页不需显示
                    myLog = self.mod.getBoxLogList(2,clubId,0,1)
                    
            elif listView==2:
                logs = self.mod.getBoxLogList(listView,clubId,offset,pageSize)
                myLog = [logs[0]]
                
            elif listView==3:
                logs = self.mod.getBoxLogList(1,clubId,0,2)
                
            else:
                logs = []
        else:
            logs = []

        return Gcore.out(optId,{'BoxLogs':logs,'PageNum':pageNum,'MaxPage':maxPage,'MyLog':myLog})
    
    def GetDevoteLogs(self,p={}):
        '''获取捐赠记录(已合并到军团信息，将弃用)'''
        optId = 15084
        clubId = self.mod.getUserClubId()
        if clubId:
            result = self.mod.getDevoteLogs(clubId)
        else:
            result = []
        result = com.list2dict(result, 1)
        return Gcore.out(optId,{'Logs':result})

    def test(self,p={}):
        '''测试方法'''
        
        

def _test():
    uid = 43371#1005，clubid2
    c = Building_clubUI(uid)
    d = 'xx'
#     d = c.CreateClub({"LogoId":1,"ClubName":'yoyoyo'})
#    d = c.Devote({"CoinType":2,"CoinValue":1000})
    d = c.GetMyClub()
#     d = c.GetClubList({'PageNum':1})
#    d = c.GetMemberList({'PageNum':10,'SortField':2,'SortWay':1})
#    d = c.GetApplyMembers()
#    d = c.ModifyClub({'LogoId':2,'ClubNotice':"sdhfhewrherhe",'AllowState':1})
#     d = c.ApplyClub({'ClubId':3})
#    d = c.SetClubLeader({'UserId':1003})
#     d = c.AgreeApply({'UserId':43419})
#     d = c.DismissMember({'UserId':1003})
#    d = c.RefuseApply({'UserId':1003})
#     d = c.GetClubTechs()
#     d = c.UpgradeClubTech({'ClubTechType':1})
#    d = Gcore.getCfg('tb_cfg_club_up',1,'OpenLevelTech'+str(1))
#    d = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_CLUB ).get('BoxPS')
#     d = c.ExitClub()
#     c.GetCrewList({'ListView':1,'PageNum':1,'SortField':1,'SortWay':1})
#     c.OpenBox({'BoxType':2})
    
#     d = c.GetBoxLogs({'ListView':1,'PageNum':1})
#     Gcore.printd(d)
#     print Gcore.loadCfg(Gcore.defined.CFG_BUILDING_CLUB).get('BoxCost')
#     print c.GetDevoteLogs()
    
if __name__ == '__main__':
    _test()
    Gcore.runtime()
