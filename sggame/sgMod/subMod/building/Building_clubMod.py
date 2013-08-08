# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-3-15
# 游戏内部接口,军团模型

import time
import sgLib.common as com
from sgLib.core import Gcore
from sgLib.base import Base
from sgLib.common import datetime
import sgLib.defined as defined

class Building_clubMod(Base):
    """军团模型"""
    def __init__(self, uid):
        '''注释'''
        Base.__init__(self,uid)
        self.uid = uid
        #print self.db #数据库连接类
    
    #-------------------------------- START 内部接口 供其他模块调用 ------------------------------------
    def getClubTechAdd(self):
        '''获取军团科技加成'''
        ups = {}
        levels = self.getClubTechs()
        techCfg = Gcore.getCfg('tb_cfg_club_tech')
        for l in levels:
            techType = int(l[13:])
            techLevel = levels.get(l,0)
            up = techCfg.get((techType,techLevel),{}).get('TechEffect',0)
            ups[techType] = up if techType<5 else up+1
        return ups
        
    def getClubTechs(self):
        '''
        :获取我的军团科技信息列表
        :实际军团科技等级,没有军团所有军团科技等级为0
        :同时返回军团等级{'TechLevelType10': 0, 'TechLevelType8': 0, ...}
        '''
        clubInfo = self.getClubInfo(self.getUserClubId())
        clubLevel = 0 if clubInfo is None else clubInfo.get('ClubLevel')
        levels = self.calClubTechs(clubLevel)
        return levels
    
    def getClubMembers(self):
        '''获得同军团其他成员列表 by Lijs'''
        clubMembers = []
        clubId = self.getUserClubId()
        if clubId:
            fields = ["u.UserId","u.NickName","UserIcon","DevoteTotal",'u.UserLevel',
                      "VipLevel","IF(u.LastLoginTime>u.LastLogoutTime,1,0) AS Online",
                "(UNIX_TIMESTAMP()-u.LastLogoutTime)/86400 AS Offlinedays"]
            where = "m.ClubId=%s and m.UserId<>%s and m.UserId=u.UserId and MemberState=1"%(clubId,self.uid)
            clubMembers = self.db.out_rows('tb_club_member m,tb_user u',fields,where)
            return clubMembers
        else:
            return []  
#        return clubMembers if clubMembers else []
    
    def getUserClubId(self,UserId=None):
        '''获取玩家的军团ID'''
        if not UserId:
            UserId = self.uid
        where = "UserId='%s' AND MemberState=1"%UserId
        ClubId = self.db.out_field('tb_club_member','ClubId',where)
        return ClubId
    
    def getClubBuildingInfo(self):
        '''
        :获取外史院建筑信息
        '''
        buildingMod = Gcore.getMod('Building',self.uid)
        b = buildingMod.getBuildingByType(15)
        b = b[0] if len(b)>=1 else None 
        return b
    
  
    
    def getClubInfo(self,ClubId=None,fields='*'):
        '''获取军团信息'''
        if ClubId is None:
            return None
        ClubInfo = self.db.out_fields('tb_club',fields, "ClubId = '%s'"%ClubId)
        
        #如果军团信息中包含当前经验，当前等级累积经验，就计算下当前等级剩余经验，升级经验by zhanggh
        for fie in ['ClubTotalExp','ClubLevelTotalExp','ClubLevel']:
            if fie not in ClubInfo:
                return ClubInfo
        
        #by Lizr
        #当前等级剩余经验
        ClubInfo['ClubCurrentExp'] = ClubInfo['ClubTotalExp'] - ClubInfo['ClubLevelTotalExp'] 
        #当前等级升级经验
        cCfgs = Gcore.getCfg('tb_cfg_club_up')
        maxLevel = max(cCfgs.keys())
        clubLevel = ClubInfo['ClubLevel']
        if clubLevel<maxLevel:
            ClubInfo['ClubCurrentExp'] = ClubInfo['ClubTotalExp'] - ClubInfo['ClubLevelTotalExp']
            ClubInfo['ClubUpLevelExp'] = cCfgs[clubLevel+1]['LevelupExp']
        else:
            ClubInfo['ClubCurrentExp'] = cCfgs[maxLevel]['LevelupExp']
            ClubInfo['ClubUpLevelExp'] = cCfgs[maxLevel]['LevelupExp']
        return ClubInfo
    
    def clubAddExp(self,arrClub,DevoteNum):
        '''增加军团经验,捐献或祭坛抽到贡献点时调用'''
#         arrClub = self.getClubInfo(ClubId)
        print arrClub
        ClubId = arrClub.get('ClubId')
        ClubLevel = arrClub.get('ClubLevel')
        clubCfg = Gcore.getCfg('tb_cfg_club_up')
        maxLevel = max(clubCfg.keys())
        #军团达最大等级不增加经验
        if ClubLevel>=maxLevel:
            return

        DevoteNum = int(DevoteNum)
        sql = "UPDATE tb_club SET ClubTotalExp=ClubTotalExp+%s WHERE ClubId=%s"%(DevoteNum,ClubId)
        self.db.execute(sql)
        
        ClubLevelTotalExp = arrClub.get('ClubLevelTotalExp')
        ClubTotalExp = self.db.out_field('tb_club','ClubTotalExp',"ClubId=%s"%ClubId)
        nextClubLevel = ClubLevel+1
        LevelUpNeedExp = clubCfg.get(nextClubLevel).get('LevelupExp')
        
        RestExp = ClubTotalExp - ClubLevelTotalExp #剩余经验
        
        if RestExp >= LevelUpNeedExp:
            ClubLevel = nextClubLevel
            d = {
                 'ClubLevel':ClubLevel,
                 'ClubLevelTotalExp':ClubLevelTotalExp + LevelUpNeedExp,
                 }
            self.db.update('tb_club',d,"ClubId=%s"%ClubId)
            
            ClubInfo = {
                'ClubLevel':ClubLevel,
                'RestExp':RestExp,
                'LevelUpNeedExp':LevelUpNeedExp,
                }
        else:
            ClubInfo = {}
            
        return ClubInfo #如果军团已经升级返回新的信息，否则返回空

    def validApplyInterval(self):
        '''验证申请军团时间间隔'''
        applyInterval = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_CLUB).get('ApplyInterval')
        applyLimitTime = time.time()-applyInterval
        where = 'UserId=%s AND MemberState=3 AND TimeExit>%s'%(self.uid,applyLimitTime)
        flag = self.db.out_field('tb_club_member','UserId',where)
        if flag:
            return False
        else:
            return True

#-------------------------------------- END 内部接口----------------------------------------------
#     def devoteRecord(self,clubId,coinType,coinValue):
#         '''
#         :军团成员贡献记录
#         @param clubId:军团Id
#         @param coinType:货币类型
#         @param coinValue:货币值
#         '''
#         devoteBase = Gcore.loadCfg(defined.CFG_BUILDING_CLUB).get('ClubGiveBase').get( str(coinType))
#         devoteNum = coinValue/devoteBase
#         memberInfo = self.db.out_fields('tb_club_member',['DevoteCurrent','DevoteTotal'],'UserId=%s AND ClubId=%s'%(self.uid,clubId))
#         data = {'DevoteCurrent':memberInfo.get('DevoteCurrent')+devoteNum,
#                 'DevoteTotal':memberInfo.get('DevoteTotal')+devoteNum}
#         self.db.update('tb_club_member',data,'UserId=%s AND ClubId=%s'%(self.uid,clubId))
#         record = {'ClubId':clubId,'UserId':self.uid,
#                   'ActionType':1,'DevoteNum':devoteNum,
#                   'DevoteCoinType':coinType,'DevoteCoinValue':coinValue,
#                   'CreateTime':datetime()}
#         self.db.insert('tb_log_club_devote',record)
#         
    def _deleteApply(self,delWay,timeLimit=True,**delData):
        '''
        :删除申请超过xx小时的申请记录
        @param String delWay:1:删除Userid的申请2:删除ClubId的申请
        @param delData:{'UserId','ClubId'} 
        '''

        if delWay==1 and delData.get('UserId'):
            where = 'UserId=%s AND MemberState in (0,4) '%delData.get('UserId')
        elif delWay==2 and delData.get('ClubId'):
            where = 'ClubId=%s AND MemberState in (0,4) '%delData.get('ClubId')
        else:
            return
        
        if timeLimit==True:
            timeLimit = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_CLUB).get('ClubApplyLimit')
            calTime = int(time.time()-timeLimit)
            where = where+' AND TimeCreate<=%s'%calTime
        return self.db.delete('tb_club_member',where)#todo删除超时
    
#     def _deleteApplyX(self,where):
#         '''
#         :删除申请超过12小时的申请记录
#         @param String where:eg：UserId=xx or ClubId=xx
#         '''
#         timeLimit = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_CLUB).get('ClubApplyLimit')
#         calTime = int(time.time()-timeLimit)
#         sql = 'Delete FROM tb_club_member WHERE %s AND MemberState in (0,4) AND TimeCreate<=%s'%(where,calTime)
#         return self.db.execute(sql)#todo删除超时

        
    def hadSameName(self,ClubName):
        '''检查军团名称是否存在
        @return True存在    False不存在
        '''
        ClubId = self.db.out_field('tb_club', 'ClubId', "ClubName='%s'"%ClubName)
        return bool(ClubId)
    
    def createClub(self,LogoId,ClubName):
        '''创建军团
        :默认等级1
        '''
        d = {
             'ClubLogoId':LogoId,
             'ClubName':ClubName,
             'ClubCamp':self.getUserCamp(),
             'ClubLevel':1,
             'CreatDate':time.time()
             }
        ClubId = self.db.insert('tb_club',d)
        if ClubId:
            self._setMeLeader(ClubId)
            self._deleteApply(1,timeLimit=False,UserId=self.uid)
            return ClubId
            
        return False
    
    def _setMeLeader(self,ClubId):
        '''把军团创建者设为团长'''
#        import time
        nowtime = time.time()
        d = {
             'ClubId':ClubId,
             'UserId':self.uid,
             'MemberType':1, #团长
             'MemberState':1, #正常
             'TimeAffirm':nowtime,
             'TimeCreate':nowtime
             }
        self.db.insert('tb_club_member',d)
    
    def getTodayDevote(self,clubId,dType=1):
        '''获取对某个军团的当天贡献总值
        @param dType: 贡献的类型，1：贡献点 2：货币总量
        '''
        import datetime
        today = time.mktime(datetime.date.today().timetuple())
        now = today+86400
        
        field = "SUM(DevoteNum)" if dType==1 else "SUM(DevoteCoinValue)"
#         where = "DATE(CreateTime) = CURDATE() AND ActionType=1 AND UserId=%s AND ClubId=%s"%(self.uid,clubId)
        where = "UserId=%s AND ClubId=%s AND ActionType=1 AND (CreateTime BETWEEN %s AND %s)"%(self.uid,clubId,today,now)
        DeveoteNum = self.db.out_field('tb_log_club_devote',field,where)
        if not DeveoteNum:
            DeveoteNum = 0
        return int(DeveoteNum)
    
    #2013.2.25 added
    
    def getClubLeader(self,clubId):
        '''
        :查询军团团长信息
        @param clubId:军团ID 
        '''
        table = 'tb_club_member m,tb_user u'
        fields = ['u.UserId','u.UserCamp','u.UserHonour','u.NickName']
        where = ' m.ClubId=%s AND m.MemberType=1 AND u.UserId = m.UserId AND m.MemberState=1'%clubId
        leaderInfo = self.db.out_fields(table,fields,where)
        return leaderInfo
    
    def getClubMemberNum(self,clubId):
        '''
        :查询军团的当前成员数量/最大成员数量
        @param clubId:军团Id
        '''
        clubLevel = self.db.out_field('tb_club','ClubLevel','ClubId=%s'%clubId)
        maxNum = Gcore.getCfg('tb_cfg_club_up',clubLevel,'MemberMax')
        curNum = self.db.out_field('tb_club_member','COUNT(1)','ClubId=%s AND MemberState=1'%clubId)
        result = {'CurNum':curNum,'MaxNum':maxNum}
        return result
                
    def getClubList(self,offset=0,pageSize=100):
        '''
        :获取阵营相同的军团列表
        '''
        self._deleteApply(1,UserId=self.uid)#删除申请军团超24小时的记录
        fields = ['ClubId','ClubName','ClubLevel','ClubLogoId','ClubNotice',
                  'AllowState']
        where = 'ClubCamp=%s AND ClubState=1 ORDER BY CreatDate LIMIT %s,%s'%(self.getUserCamp(),offset,pageSize)
        clubs = self.db.out_rows('tb_club',fields,where)
        applys = self.db.out_rows('tb_club_member',['ClubId','1 AS Apply'],'UserId=%s AND MemberState in(0,4)'%self.uid)
        applyNum = {}
        for a in applys:
            applyNum[a['ClubId']] = a['Apply']
        for club in clubs:
            memberInfo = self.getClubMemberNum(club['ClubId'])
            leaderInfo = self.getClubLeader(club['ClubId'])
            print 'cc',club['ClubId'],leaderInfo
            
            club['CurrentMember'] = memberInfo['CurNum']
            club['MaxMember'] = memberInfo['MaxNum']
            club['LeaderId'] = leaderInfo['UserId']
            club['LeaderName'] = leaderInfo['NickName']
            club['Applied'] = applyNum.get(club['ClubId'],0)
            if club['ClubNotice'] is None:
                club['ClubNotice'] = ' '
        return clubs
    
    def getClubNum(self):
        '''
        :获取阵营相同的军团数量
        '''
        return self.db.out_field('tb_club','COUNT(ClubId)','ClubCamp=%s AND ClubState=1'%self.getUserCamp())
        
        
        
    def getMemberInfo(self,clubId,userId,fields=['*']):
        '''
        :获取军团成员信息（任何状态）
        @param clubId:
        @param userId:
        '''
        if clubId is None:
            return None
        return self.db.out_fields('tb_club_member',fields,'ClubId=%s AND UserId=%s'%(clubId,userId))
    
    def getMemberInfoByUID(self,userId,fields=['*']):
        '''
        :通过用户Id查找当前军团资料
        @param userId:
        @param fields:
        '''
        where = "UserId='%s' AND MemberState=1"%userId
        clubInfo = self.db.out_fields('tb_club_member',fields,where)
        return clubInfo
        
    def applyClub(self,clubId):
        '''
        :申请加入军团
        @param clubId:军团ID
        :0申请加入，4：重新申请加入
        '''
        now = time.time()
        memberInfo = self.db.out_fields('tb_club_member',['*'],'ClubId=%s AND UserId=%s'%(clubId,self.uid))
        if memberInfo:
            data = {}
            data['MemberState'] = 4
            data['TimeCreate'] = now
            data['MemberType'] = 3
            self.db.update('tb_club_member',data,'ClubMemberId=%s'%memberInfo['ClubMemberId'])
            
        else:
            data = {'ClubId':clubId,'UserId':self.uid,
                'MemberType':3,'MemberState':0,
                'DevoteCurrent':0,'DevoteTotal':0,
                'TimeAffirm':0,'TimeExit':0,
                'TimeCreate':now}
            self.db.insert('tb_club_member',data)
        
#    def getMemberList(self,clubId,sortField,sortWay,offset=0,end=1000):
#        '''
#        :查询成员信息列表
#        @param clubId:军团ID
#        @todo即将删除
#        '''
#        sortC = sortField+' '+sortWay
#        table = 'tb_user u,tb_club_member m'
#        fields = ['u.UserId','u.NickName','u.VipLevel','u.UserIcon','u.UserLevel',
#                  'm.DevoteCurrent','m.DevoteTotal','m.MemberType']
#        where = 'm.ClubId=%s AND m.UserId=u.UserId \
#                 ORDER BY m.MemberType,%s,u.UserId Limit %s,%s'%(clubId,sortC,offset,end)
#        ms = self.db.out_rows(table,fields,where)
#        ad = {'OnLined':1,'OffLineTime':0}#todo是否在线，在线时间
#        for m in ms:
#            m.update(ad)
#        return ms
    
    def setClubLeader(self, optId, clubId, userId):
        '''
        :设置军团的团长（团长操作）
        @param clubId:军团ID
        @param userId:用户ID
        '''
        self.db.update('tb_club_member',{'MemberType':1},'ClubId=%s AND UserId=%s'%(clubId,userId))
        self.db.update('tb_club_member',{'MemberType':3},'ClubId=%s AND UserId=%s'%(clubId,self.uid))
        #发系统邮件
        nickName = self.getUserInfo('NickName')
        clubName = self.getClubInfo(clubId, 'ClubName')['ClubName']
        mailMod = Gcore.getMod('Mail', self.uid)
        mailMod.sendSystemMail(userId, [], optId, other=[nickName, clubName,])
    
    def dismissMember(self, optId, clubId, userId, way=2, userType=1):
        '''
        :请离成员（团长操作）
        @param userId:用户ID
        @param way: 退团方式 2被开除3主动退出
        @param userType:1会长 2副会长 3普通成员 
        '''

        now = time.time()
        data = {'MemberState':way,'TimeExit':now,
                'DevoteCurrent':0,'DevoteTotal':0}
        flag = self.db.update('tb_club_member',data,'ClubId=%s AND UserId=%s'%(clubId,userId))
        
        if flag and userType==1:#团长退出
            memberNum = self.db.out_field('tb_club_member','COUNT(1)','ClubId=%s AND MemberState=1'%clubId)
            if memberNum>=1:#转移团长身份
                memberIdwhere = 'ClubId=%s AND MemberState=1 ORDER BY DevoteTotal DESC LIMIT 1'%clubId
#                 clubMemberId = self.db.out_field('tb_club_member','ClubMemberId',memberIdwhere)
                self.db.update('tb_club_member',{'MemberType':1},memberIdwhere)
                
            elif memberNum==0:#解散群
                self.db.delete('tb_club','ClubId=%s'%clubId)
        #被开除发送系统邮件
        if way == 2:
            mailMod = Gcore.getMod('Mail', self.uid)
            mailMod.sendSystemMail(userId, [], optId)

        
    def modifyClub(self,clubId,data):
        '''
        :修改军团信息（团长操作）
        @param clubId:用户ID
        @param data:更新的内容 
        '''
        return self.db.update('tb_club',data,'clubId=%s'%clubId)
    
    
#    def getApplyList(self,clubId,offset=0,end=100):
#        '''
#        :军团成员申请列表
#        @param clubId:军团ID
#        @todo即将删
#        '''
#        table = 'tb_user u,tb_club_member m'
#        fields = ['u.UserId','u.NickName','u.VipLevel','u.UserHonour','u.UserIcon','u.UserLevel']
#        where = 'm.ClubId=%s AND m.MemberState in (0,4) AND m.UserId=u.UserId'%clubId
#        return self.db.out_rows(table,fields,where)
    
#    def getApplyNum(self,clubId):
#        '''
#        :获取军团申请人数
#        @param clubId:军团ID
#        @todo即将删
#        '''
#        self._deleteApply('ClubId=%s'%clubId)#删除申请军团超24小时的记录
#        return self.db.out_field('tb_club_member','COUNT(ClubMemberId)','ClubId=%s AND MemberState in (0,4)'%clubId)
        
    
    def agreeApply(self, optId, clubId, userId):
        '''
        :同意成员申请（同意同时删除其他军团申请）
        @param clubId:军团ID
        @param userId:用户ID
        '''
        now = time.time()
        data = {'TimeAffirm':now,'MemberState':1}
        #同意某个人加入后，该成员其他申请信息删除
        self.db.update('tb_club_member',data,'ClubId=%s AND UserId=%s'%(clubId,userId))
        self._deleteApply(1,timeLimit=False,UserId=userId)
        #发送系统邮件
        mailMod = Gcore.getMod('Mail', self.uid)
        clubName = self.getClubInfo(clubId, 'ClubName')['ClubName']
        mailMod.sendSystemMail(userId, [], optId, other=[clubName,])
             
#         sql = 'DELETE FROM tb_club_member WHERE UserId=%s AND MemberState in (0,4)'%userId
#         self.db.execute(sql)
    
    def refuseApply(self, optId, clubId, userId):
        '''
        :拒绝成员申请
        @param clubId:军团ID
        @param userId:用户ID
        '''
        data = {'MemberState':5}
        #发送系统邮件
        mailMod = Gcore.getMod('Mail', self.uid)
        clubName = self.getClubInfo(clubId, 'ClubName')['ClubName']
        mailMod.sendSystemMail(userId, [], optId, other=[clubName,])
        
        return self.db.update('tb_club_member',data,'ClubId=%s AND UserId=%s'%(clubId,userId))
    
    
    
    def getClubTechLevel(self,techType):
        '''
        :获取军团科技已学习等级
        @param techType:科技类型
        '''
        field = 'TechLevelType'+str(techType)
        level = self.db.out_field('tb_club_tech',field,'UserId=%s'%self.uid)
        if level is None:
            if self.db.insert('tb_club_tech',{'UserId':self.uid,'TechLevelType':0}):
                return 0
        return level
    
    def calClubTechs(self,clubLevel=None):
        '''
        :通过军团等级计算我的的军团科技信等级
        :实际军团科技等级,没有军团所有军团科技等级为0
        '''
        fields = []
        for i in range(1,11):
            fields.append('TechLevelType'+str(i))
        levels = self.db.out_fields('tb_club_tech',fields,'UserId=%s'%self.uid)
        
        if not levels:#没有军团科技等级记录
            self.db.insert('tb_club_tech',{'UserId':self.uid})
            return self.db.out_fields('tb_club_tech',fields,'UserId=%s'%self.uid)

        #查询军团等级
        if clubLevel is None:
            clubId = self.getUserClubId()
            clubLevel = self.getClubInfo(clubId).get('ClubLevel') if clubId else None
            
        #科技等级不高于军团等级限制
        clubCfg = Gcore.getCfg('tb_cfg_club_up')
        for key in levels:
            techType = int(key[13:])
            if clubLevel == 0 or clubLevel is None:
                levels[key] = 0#没有军团科技等级为0
                continue
                
            openLevel = clubCfg.get(clubLevel,{}).get('OpenLevelTech%s'%techType)
            if levels.get(key)>openLevel:
                levels[key] = openLevel#已学习等级高于军团最高上限时等级为上限
        return levels
    
    def upgradeClubTech(self,techType):
        '''
        :升级军团科技
        @param techType:科技类型 
        '''
        field = 'TechLevelType'+str(techType)
        level = self.db.out_field('tb_club_tech',field,'UserId=%s'%self.uid)
        if self.db.update('tb_club_tech',{field:level+1},'UserId=%s'%self.uid):
            return level+1
        else:
            return 0
    
    
    def payDevote(self,clubId,num):
        '''
        :支付贡献点
        @param num:贡献点
        @return: 支付成功返回余额，-1：支付失败，-2：贡献点不足
        '''
        if clubId is None:
            return -1#支付失败
        current = self.db.out_field('tb_club_member','DevoteCurrent','UserId=%s AND ClubId=%s'%(self.uid,clubId))

        left = current-num
        if left<0:
            return -2#贡献点不足
        flag = self.db.update('tb_club_member',{'DevoteCurrent':left},'UserId=%s AND ClubId=%s'%(self.uid,clubId))
        if not flag:
            return -1#支付失败
        record = {'ClubId':clubId,'UserId':self.uid,
                  'UserType':Gcore.getUserData(self.uid,'UserType'),
                  'ActionType':2,'DevoteNum':num,
                  'CreateTime':time.time()}
        self.db.insert('tb_log_club_devote',record)
        return left
    
    def gainDeveote(self,clubId,gainWay,**p):
        '''
        :获得贡献
        @param clubId:
        @param gainWay:获得方式 1贡献 3抽奖
        @param p:if gainWay==1: p{coinValue,coinType}
                 elif gainWay==3: p{devoteNum}
        '''
        if not clubId:
            return 0
        
        devoteNum = p.get('devoteNum',0)
        record = {'ClubId':clubId,'UserId':self.uid,
                  'UserType':Gcore.getUserData(self.uid,'UserType'),
                  'ActionType':gainWay,'DevoteNum':devoteNum,
                  'CreateTime':time.time()}
        if gainWay==1:#贡献获得
            coinType = p['coinType']
            coinValue = p['coinValue']
            devoteBase = Gcore.loadCfg(defined.CFG_BUILDING_CLUB).get('ClubGiveBase').get( str(coinType))
            devoteNum = coinValue/devoteBase
            record['DevoteNum'] = devoteNum
            record['DevoteCoinType'] = coinType
            record['DevoteCoinValue'] = coinValue
        sql = 'UPDATE tb_club_member \
                SET  DevoteCurrent=DevoteCurrent+%s,\
                     DevoteTotal=DevoteTotal+%s \
                WHERE UserId=%s AND ClubId=%s'%(devoteNum,devoteNum,self.uid,clubId)
        if self.db.execute(sql):
            self.db.insert('tb_log_club_devote',record)
            return devoteNum
        else:
            0
    
    def getCrewNum(self,listView,clubId):
        if listView ==1:
            where = 'ClubId=%s AND MemberState = 1'%clubId
        else:
            where = 'ClubId=%s AND MemberState in (0,4)'%clubId
        return self.db.out_field('tb_club_member','COUNT(ClubMemberId)',where)
    
    def getCrewList(self,listView,clubId,sortField,offset=0,pageSize=100):
        '''获取军团成员或申请列表'''
        table = 'tb_user u,tb_club_member m'
        now = int(time.time())
        if listView == 1:#成员列表
            fields = ['u.UserId','u.NickName',
                      'u.VipLevel','u.UserIcon',
                      'u.Online AS Onlined',
                      'FLOOR((%s-u.LastLogoutTime)/86400) AS OffLineTime'%now,
                      'u.UserLevel','m.DevoteCurrent',
                      'm.DevoteTotal','m.MemberType',]
            
            where = 'm.ClubId=%s AND m.MemberState=1 \
                     AND m.UserId=u.UserId \
                     ORDER BY m.MemberType,%s,u.UserId \
                     LIMIT %s,%s'%(clubId,sortField,offset,pageSize)
        else:#申请列表
            fields = ['u.UserId','u.NickName',
                      'u.VipLevel','u.UserHonour',
                      'u.UserIcon','u.UserLevel',
                      'u.Online AS Onlined',
                      'FLOOR((%s-u.LastLogoutTime)/86400) AS OffLineTime'%now,]
            
            where = 'm.ClubId=%s AND m.MemberState in (0,4) \
                    AND m.UserId=u.UserId \
                    ORDER BY %s,u.UserId \
                    LIMIT %s,%s'%(clubId,sortField,offset,pageSize)
            
        ms = self.db.out_rows(table,fields,where)
#         ad = {'OnLined':1,'OffLineTime':0}#todo是否在线，在线时间
#         for m in ms:
#             m.update(ad)
        return ms
     
    def insertBoxLog(self,clubId,boxType,data):
        '''
         :插入宝箱开奖记录
         @param data:宝箱数据
        '''
        logData = {'ClubId':clubId,'UserId':self.uid,
                   'UserType':Gcore.getUserData(self.uid,'UserType'),
                   'BoxType':boxType,'RewardType':data['RewardType'],
                   'GoodsId':data['GoodsId'],'GoodsNum':data['GoodsNum'],
                   'CreateTime':time.time()}
        return self.db.insert('tb_log_club_box',logData)
    
    def getBoxLogNum(self,listView,clubId):
        '''
        :查询宝箱开奖记录数量
        @param ListView:
        '''
        import datetime
        today = time.mktime(datetime.date.today().timetuple())
        now = today+86400
        
#         where = "FROM_UNIXTIME(CreateTime,'%Y-%m-%d')=CURDATE()AND ClubId ="+str(clubId)
        where = " ClubId =%s AND (CreateTime BETWEEN %s AND %s) "%(clubId,today,now)
        
        if listView == 2:
            where = where+' AND UserId=%s'%self.uid
        num = self.db.out_field('tb_log_club_box','COUNT(BoxLogId)',where)
        print self.db.sql
        return num
    
    
    def getBoxLogList(self,listView,clubId,offset=0,pageSize=100,timeLimit=True):
        '''
        :查询宝箱开奖记录
        @param listView: 1：军团所有成员 2：玩家自己3:军团内两条记录
        @param clubId:
        @param offset:
        @param pageSize:
        '''
        table = 'tb_user u,tb_log_club_box b'
        fields = ['u.UserId','u.UserIcon','u.NickName',
                  'b.BoxType','b.RewardType','b.GoodsId',
                  'b.GoodsNum','b.CreateTime']
        
        
        
#         where = "u.UserId = b.UserId AND FROM_UNIXTIME(b.CreateTime,'%Y-%m-%d')=CURDATE() AND b.ClubId ="+str(clubId)
        where = "u.UserId = b.UserId  AND b.ClubId =%s "%(clubId)
        if timeLimit==True:
            import datetime
            today = time.mktime(datetime.date.today().timetuple())
            now = today+86400
            where = where+' AND (b.CreateTime BETWEEN %s AND %s) '%(today,now)
            
        if listView == 2:
            where = where+' AND u.UserId=%s ORDER BY b.CreateTime DESC LIMIT %s,%s'%(self.uid,offset,pageSize)

        else:
            where = where+' ORDER BY b.CreateTime DESC LIMIT %s,%s'%(offset,pageSize)
        
        return self.db.out_rows(table,fields,where)
    
    
    def getDevoteLogs(self,clubId):
        '''查询捐献记录'''
        limitNum = 20
        fields = ['u.NickName','d.DevoteCoinType','d.DevoteCoinValue','d.CreateTime']
        table = 'tb_user u,tb_log_club_devote d'
        where = 'u.UserId=d.UserId AND d.ClubId=%s AND ActionType=1 ORDER BY d.CreateTime DESC Limit %s'%(clubId,limitNum)
        return self.db.out_rows(table,fields,where)
    
    def test(self):
        '''测试方法'''

#        data = { 'UserId':self.uid,'PackageId':1,
#                'GoodsType':2,'GoodsId':113,'GoodsNum':111}
#        check = {'UserId':self.uid,'PackageId':1}
#        self.db.insert_update('tb_package',data,check)
        #Author:Modify by Zhanggh 2013-3-21S
#         return self.db.out_rand('tb_user',n=5)
#         data = {'DevoteCurrent':"'DevoteCurrent'+10"}
#         data = {'DevoteCurrent':10}
#         self.db.update('tb_club_member',data,'ClubMemberId=32')
        sql = '''SELECT COUNT(BoxLogId) FROM tb_log_club_box \
            WHERE FROM_UNIXTIME(CreateTime,%s)=CURDATE()AND ClubId =57'''
        return self.db.fetchone(sql,('%Y-%m-%d',))

def _test():
    uid = 4432250
    c = Building_clubMod(uid)
    #print c.getUserClubId()
#    c.clubAddExp(61100)
#    print c.getUserClubInfo()
#    print c.getMyClubTechs()
#    print c.getClubBuildingInfo()
#    print c.getClubLeader(2)
#    d =  c.test()
#    print c.getApplyNum(11)
#    print c._deleteApply('ClubId =11')
#    print c.getXNum(11,987)
#     print c.getClubTechs()
#    print c.getMemberInfo(None,uid,['DevoteCurrent'])
#    Gcore.printd(d)
#    print c.upgradeClubTech(2)

#    print c.getClubMembers()
    print c.getClubTechAdd()
#     print c.payDevote(12)
#     print c.gainDeveote(11,1,coinType=2,coinValue=4000)
#     print c.db.out_field('tb_user','Count(1)',"NickName='%s'"%'你妈逼')
#     print c.getMemberInfoByUID(10111,['ClubId','DevoteCurrent'])
#     print c.getTodayDevote(24,3)
#     print c.validApplyInterval()



if __name__ == '__main__':
    _test()
    Gcore.runtime()
    
    
    
    