# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-5-9
# 游戏内部接口,模型层(被*UI调用)

from sgLib.core import Gcore
from sgLib.base import Base
import time

#print 'in ExmapleMod,Gcore',Gcore,id(Gcore),Gcore.started
class MissionMod(Base):
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
        
    def initMission(self,mIds,userId=None,pushMsg=True):
        '''
        :给玩家添加一个或者多个任务
        @param mId:任务Id,一个或者多个
        @param userId:用户ID
        '''
        if userId is None:
            userId = self.uid
        if not isinstance(mIds, (list, tuple)):
            mIds = [mIds]
        tb_m = 'tb_mission'
        mCfgs = Gcore.getCfg('tb_cfg_mission')
        
        now = time.time()
        insertdata = []
        missionCaches = {}
        pushMids = []
        
        for mid in mIds:
            data = {'MissionId':mid,'UserId':userId,
                    'GetValue':0,'Status':1,
                    'CreateTime':now,'CompleteTime':0}
            missionCache = {}
            #处理需要特需处理的任务
            getVal = self.getMissionUpdateVal(mid)
            if getVal:
                data['GetValue'] = getVal
                paramB = mCfgs[mid]['ParamB']
                if getVal>=paramB:#任务完成
                    data['GetValue'] = paramB
                    data['Status'] = 3
                    data['CompleteTime'] = now
                else:
                    missionCache = {'MissionId':mid,'GetValue':getVal}
            else:
                missionCache = {'MissionId':mid,'GetValue':0}
                
            if self.db.insert(tb_m,data):
                insertdata.append(data)
                pushMids.append(mid)
                if missionCache:#增加缓存
                    missionCaches[mid] = missionCache
        
        # 更新任务缓存
        if missionCaches:
            activeMission = self._getMissionCache('initMision')
            activeMission.update(missionCaches)
            Gcore.setUserData(self.uid, {'ActiveMission':activeMission})
        # 推送新任务
        if pushMsg and pushMids:
            Gcore.push(102,self.uid,{'MT':1,'MIDS':pushMids})
        return insertdata
        
    def getMissionFinishNum(self):
        '''任务完成数量'''
        return self.db.out_field('tb_mission','COUNT(1)','UserId=%s AND Status=3'%self.uid)
    
    def getMyMissions(self):
        '''
        :获取我的任务列表
        '''
        tb_m = 'tb_mission'
        fields =['MissionId AS MID','Status AS MST',
                 'GetValue AS VAL'
                 ]
        return self.db.out_rows(tb_m,fields,'UserId=%s AND Status<4 ORDER BY CreateTime DESC,MissionId'%self.uid)
    
    def actionMyMission(self,mid):
        '''设置我的任务为进行中'''
        tb_m = 'tb_mission'
        return self.db.update(tb_m,{'Status':2},'UserId=%s AND MissionId=%s AND Status=1'%(self.uid,mid))
    
#     def updateMission(self,mId,data):
#         '''更新任务'''
#         tb_m = 'tb_mission'
#         st = data.get('Status',0)
#         if st==3:
#             print '任务已完成:',mId
#             #todo 任务完成推送消息
#             Gcore.push(102,self.uid,{'MT':2,'MIDS':[mId]})
#         return self.db.update(tb_m,data,'UserId=%s AND MissionId=%s'%(self.uid,mId))
    
    def updateMissions(self,mData):
        '''更新多个任务（更新相应的任务缓存数据）
        @param mData: {MId:updateData} MId:任务ID,updateData:更新内容
        @return: 更新数目
        '''
        tb_m = 'tb_mission'
        mCfg = Gcore.getCfg('tb_cfg_mission')
        activeMission = Gcore.getUserData(self.uid, 'ActiveMission')
        
#         print '更新任务信息=>',mData
#         print '任务缓存信息=>',activeMission
        
        pusMId = []
        updateNum = 0
        for mId in mData:
            data = mData[mId]
            getVal = data.get('GetValue',0)
            paramB = mCfg[mId]['ParamB']
            
            #如果任务完成推送消息
            if getVal>=paramB:
                data['GetValue']=paramB
                data['Status']=3
                data['CompleteTime'] = time.time()
                pusMId.append(mId)
                activeMission.pop(mId,None)#任务完成删除缓存任务
                
            elif getVal:
                activeMission[mId]['GetValue'] = getVal#更新缓存任务信息
            
            if self.db.update(tb_m,data,'UserId=%s AND MissionId=%s'%(self.uid,mId)):
                updateNum +=1
       
        #更新任务缓存
        Gcore.setUserData(self.uid, {'ActiveMission':activeMission})
        #推送通知任务完成
        if pusMId:
            print '任务完成',str(pusMId)
            Gcore.push(102,self.uid,{'MT':2,'MIDS':pusMId})
        return updateNum
    
    def updateMissionByWhere(self,data,where):
        '''
        :更新任务（和缓存无关，直接更新数据库）
        @param data:更新数据
        @param where:where条件
        '''
        return self.db.update('tb_mission',data,where)
             
    def getMissionInfo(self,mId,fields=['*']):
        '''
        :查看任务信息
        @param mId:
        @param fields:
        '''
        tb_m = 'tb_mission'
        return self.db.out_fields(tb_m,fields,'UserId=%s AND MissionId=%s'%(self.uid,mId))
    
    def getNewMission(self,mId=None,userLevel=None):
        '''
        :任务完成领取奖励后或主角升级，领取新任务
        @param mId:任务ID
        @param level:主角等级
        @return: 领取到得新任务
        '''
        pushMsg = True #是否推送新任务（主角升级时候推）
        tb_m = 'tb_mission'
        if userLevel is None:
            userLevel = self.getUserLevel()
            pushMsg = False
            
        dMids = []#已领取奖励(前置任务)
        newMids = []    
        ms = self.db.out_rows(tb_m,['MissionId','Status'],'UserId=%s'%self.uid)
        gMids = [m.get('MissionId') for m in ms]#已接任务
        if mId is None:
            dMids = [m.get('MissionId') for m in ms if m.get('Status')==4]
        else:
            dMids.append(mId)
        
        #判断是否有新任务
        mCfg = Gcore.getCfg('tb_cfg_mission')
        for mc in mCfg.values():
            levelReq = mc.get('UserLevel')
            preMid = mc.get('PreMissionId')
            cMid = mc.get('MissionId')
            if userLevel>=levelReq and ((preMid in dMids) or preMid==0) and (cMid not in gMids):
                newMids.append(cMid) 
                
                
        if newMids:
            return self.initMission(newMids,pushMsg=pushMsg)
        else:
            return []  
            
    def missionTrigger(self,optId,data={'ValType':0,'Val':0}):
        '''
        :任务触发
        @param optId:功能号（触发点）
        @param data:更新值 （可添加除额外更多值）
                -ValType（必须有）：值类型（匹配配置中的ParamA）
                -Val（必须有）：值
        '''
        valType = data.get('ValType')
        val = data.get('Val')
        
        ms = self._getMissionCache(optId)#缓存查询
        ms = ms.values()

        mCfgs = Gcore.getCfg('tb_cfg_mission')
        updateMission = {}
        for m in ms:
            mId = m['MissionId']
            mCfg = mCfgs[mId]
            mOptId = mCfg.get('OptId','')
            if mOptId is None:
                continue

            mOptId = mOptId.strip().split(',')
            paramA = mCfg.get('ParamA',0)
            paramB = mCfg.get('ParamB',0)
            #print mOptId
            
            #更新任务记录
            #valType=0触发所有相关任务，paramA==0，忽略valType类型，
            if str(optId) in mOptId and (paramA==0 or valType==paramA or valType==0):
                curVal = m.get('GetValue')
                #处理更新数据
                updateVal = self.getMissionUpdateVal(mId,data,curVal)
                if updateVal:
                    updateMission[mId] = {'GetValue':updateVal}#添加到字典批量更新
                    
        #一次更新多个任务
        #print updateMission
        if updateMission:
            self.updateMissions(updateMission)
            
    def _getMissionCache(self,action=''):
        '''获取任务缓存'''
        activeMission = Gcore.getUserData(self.uid,'ActiveMission')#缓存查询
        if (activeMission is None) or (not isinstance(activeMission,dict)):
            myLog = Gcore.getLogger('zhanggh','mission')
            myLog.error("任务缓存有异常，UserId:%s,动作:%s，用户缓存内容："%(self.uid,action))
            myLog.error( Gcore.StorageUser.get(self.uid))
            
            activeMission = self.db.out_rows('tb_mission',['MissionId','GetValue'],'UserId=%s AND Status in (1,2)'%self.uid)
            activeMission = {k['MissionId']:k for k in activeMission}
            Gcore.setUserData(self.uid,{'ActiveMission':activeMission})
        return activeMission
        
    def updateAllMissions(self):
        '''更新所有任务的状态'''
        
        ms = self._getMissionCache('updateAllMissions')#缓存查询
        ms = ms.values()

        updateMission = {}
        for m in ms:
            mId = m.get('MissionId')
            getValue = m.get('GetValue')
            updateVal = self.getMissionUpdateVal(mId,curVal=getValue)
            if updateVal:
                updateMission[mId] = {'GetValue':updateVal}#添加到字典批量更新
        
        #一次更新多个任务
        if updateMission:
            self.updateMissions(updateMission)
                 
    def getMissionUpdateVal(self,mId,data={'ValType':0,'Val':0},curVal=0):
        '''
        :处理任务更新数据
        @param mId:任务ID
        @param data:更新数据
        @param curVal:
        '''
        mCfg = Gcore.getCfg('tb_cfg_mission',mId)
        mt = mCfg.get('MissionType',0)#任务功能类型编号
        paramA = mCfg.get('ParamA',0)
        paramB = mCfg.get('ParamB',0)
        valType = data.get('ValType')
        val = data.get('Val')
        getVal = 0
        if mt==3:#当前拥有A建筑B个
            buildingMod = Gcore.getMod('Building',self.uid)
            getVal = buildingMod.countBuildingType(paramA)
        
        elif mt==4:#当前拥有A建筑B级
            tb_b = self.tb_building()
            now = time.time()+1
            field = 'MAX(IF(CompleteTime>%s,BuildingLevel-1,BuildingLevel))'%now
            getVal = self.db.out_field(tb_b,field,'BuildingType=%s AND UserId=%s'%(paramA,self.uid))
        
        elif mt==5:# 当前拥有A个B级建筑
            tb_b = self.tb_building()
            now = time.time()+1
            field = 'SUM(IF(IF(CompleteTime>%s,BuildingLevel,BuildingLevel-1)>=%s,1,0))'%(now,paramA)
            getVal = self.db.out_field(tb_b,field,'UserId=%s'%(self.uid))
            
        elif mt==6 or mt==7:#加速建造
            buildingLevel = data.get('BuildingLevel')
            if buildingLevel==1:
                getVal = curVal+val
        
        elif mt==8 or mt==9:#加速升级
            buildingLevel = data.get('BuildingLevel')
            if buildingLevel>1:
                getVal = curVal+val
                
        elif mt==11:#工匠数量
            if val>0:
                getVal = curVal+1
            else:
                getVal = self.db.out_field('tb_user','WorkerNumber','UserId=%s'%self.uid)
        
        
        elif mt==14:#兵营加速次数
            sf = Gcore.getCfg('tb_cfg_soldier',valType,'SpawnBuildingType')
            if sf==6:#兵营
                getVal = curVal+1
                
        elif mt==19:#工坊加速次数
            sf = Gcore.getCfg('tb_cfg_soldier',valType,'SpawnBuildingType')
            if sf==8:#工坊
                getVal = curVal+1
                
        elif mt==22:#资源上限达到B
            getVal = Gcore.getMod('Building',self.uid).cacStorageSpace(paramA)
                
        elif mt==23:#当前已存资源
            nowCoin = data.get('NowCoin')
            if nowCoin>curVal:
                getVal = nowCoin
        
        elif mt==27:#天坛金色，地坛紫色以上
            awardQuality = data.get('Award',{}).get('AwardQuality',0)
            if valType==1 and awardQuality==5:
                getVal = curVal+1
            
            elif valType==2 and awardQuality>=4:
                getVal = curVal+1 

        elif mt==29:#祭坛装备
            if valType==1:#天坛
                if data.get('SkyAwardType') in (1,2):
                    getVal = curVal+1
            elif valType==2:#地坛
                if data.get('LandAwardType') in (1,2):
                    getVal = curVal+1
            
        elif mt==30:#祭坛道具
            if valType==1:#天坛
                if data.get('SkyAwardType')==6:
                    getVal = curVal+1
            elif valType==2:#地坛
                if data.get('LandAwardType')==6:
                    getVal = curVal+1
                    
        elif mt==35:#内政a效果b
            interEffect = int(Gcore.getMod('Inter',self.uid).getInter().get(paramA,0)*100)
            if interEffect>curVal:
                getVal = interEffect
        
        elif mt==36:#当前已完成成就B个
            if val:
                getVal = curVal+val
            else:
                getVal = self.db.out_field('tb_achieve','COUNT(1)','UserId=%s AND Finished=1'%self.uid)
        
        elif mt==37:#拥有藩国数量
            getVal = Gcore.getMod('Building_hold',self.uid).getHoldNum()
        
        elif mt==40:#收集A次
            if val:
                getVal = curVal+1
                
        elif mt==41:#计算产量
            buildingType = 2 if paramA==2 else 5
            bCfg = Gcore.getCfg('tb_cfg_building_up')
            t2 = Gcore.getMod('Building',self.uid).getBuildingByType(buildingType)
            levelSum = 0
            for t in t2:
                bLevel = t.get('BuildingRealLevel')
                levelSum += bCfg.get((buildingType,bLevel),{}).get('HourValue',0)
            if levelSum>curVal:
                getVal = levelSum
        
        elif mt==45 or mt==47:#A兵种达到B级
            now = time.time()+1
            field = 'IF(LastEndTime<=%s,TechLevel,TechLevel-1)'%now
            where = 'UserId=%s AND TechCategory=1 AND TechType=%s'%(self.uid,paramA)
            level = self.db.out_field('tb_book_tech',field,where)
            if level>curVal:
                getVal = level
        
        elif mt==46:#A内政达到B级
            now = time.time()+1
            field = 'IF(LastEndTime<=%s,TechLevel,TechLevel-1)'%now
            where = 'UserId=%s AND TechCategory=2 AND TechType=%s'%(self.uid,paramA)
            level = self.db.out_field('tb_book_tech',field,where)
            if level>curVal:
                getVal = level
                
        elif mt==48:#A级兵种B个
            now = time.time()+1
            field = 'SUM(IF(IF(LastEndTime<=%s,TechLevel,TechLevel-1)>=%s,1,0))'%(now,paramA)
            where = 'UserId=%s AND TechCategory=1 AND TechType<=100'%(self.uid)
            num = self.db.out_field('tb_book_tech',field,where)
            if num>curVal:
                getVal = num
        
        elif mt==49:#A级内政B个
            now = time.time()+1
            field = 'SUM(IF(IF(LastEndTime<=%s,TechLevel,TechLevel-1)>=%s,1,0))'%(now,paramA)
            where = 'UserId=%s AND TechCategory=2'%(self.uid)
            num = self.db.out_field('tb_book_tech',field,where)
            if num>curVal:
                getVal = num
        
        elif mt==50:#A级器械B个
            now = time.time()+1
            field = 'SUM(IF(IF(LastEndTime<=%s,TechLevel,TechLevel-1)>=%s,1,0))'%(now,paramA)
            where = 'UserId=%s AND TechCategory=1 AND (TechType BETWEEN 100 AND 199)'%(self.uid)
            num = self.db.out_field('tb_book_tech',field,where)
            if num>curVal:
                getVal = num
                
        elif mt==51:#书院升级科技立即完成B次
            bt = data.get('BuildingType')
            if bt==12:
                getVal=curVal+val
        
        elif mt==53:#铁匠铺购买装备B次
            if val:
                getVal = curVal+1
            
        elif mt==55:#拥有B级装备a件
            equipLevel = data.get('EquipLevel')
            if equipLevel>=paramA:
                getVal = curVal+1
            else:
                equipT = self.tb_equip()
                getVal= self.db.out_field(equipT,'COUNT(1)','UserId=%s AND EquipStatus in (1,2) AND StrengthenLevel>=%s'%(self.uid,paramA))

                
        elif mt==56:#铁匠铺出售n次
            if val:
                getVal = curVal+1
        
        elif mt==57:#拥有军团
            num = self.db.out_field('tb_club_member','COUNT(1)','UserId=%s AND MemberState=1'%self.uid)
            if num>=1:
                getVal=1
                
        elif mt==58:#科技A达到B级
            k = 'TechLevelType%s'%paramA
            techs = Gcore.getMod('Building_club',self.uid).calClubTechs()
            getVal = techs.get(k)
        
        elif mt==59:#A个科技等级达到B
            techs = Gcore.getMod('Building_club',self.uid).calClubTechs().values()
            getVal = len([t for t in techs if t>=paramA])

        elif mt==61:#军团贡献B次
            if val:
                getVal = curVal+1
        
        elif mt==62:#军团总贡献
            dvo = Gcore.getMod('Building_club',self.uid).getMemberInfoByUID(self.uid,['DevoteTotal']).get('DevoteTotal',0)
            if dvo>curVal:
                getVal = dvo
        
        elif mt==66:#当前拥有A兵种B个
            soldiers = data.get('Soldiers')
            getVal = soldiers.get('Soldier%s'%paramA,0)
        
        elif mt==67:#当前拥有兵种B个
            soldiers = data.get('Soldiers')
            getVal = len([s for s in soldiers.values() if s>0])
        
        elif mt==68:#当前拥有兵数量
            soldiers = data.get('Soldiers')
            getVal = sum(soldiers.values())
                   
        elif mt==69:#屯兵上限,校场BuildingType：7
            t7 = Gcore.getMod('Building',self.uid).getBuildingByType(7)
            getVal = Gcore.getMod('Building_camp',self.uid).getMaxSoldierNum(t7)
            
        elif mt==71:#当前上阵
            GNum = data.get('GNum',0)
            if GNum>curVal:
                getVal = GNum
                
        elif mt==73:#雇佣兵数量
            sSide = Gcore.getCfg('tb_cfg_soldier',valType,'SoldierSide')
            if sSide==4:
                getVal = val+curVal
                
        elif mt==74:#可雇佣兵种类
            tb_b = self.tb_building()
            now = time.time()+1
            field = 'MAX(IF(CompleteTime<=%s,BuildingLevel,BuildingLevel-1))'%now
            level = self.db.out_field(tb_b,field,'BuildingType=9 AND UserId=%s'%(self.uid))
            soldierCfgs = Gcore.getCfg('tb_cfg_soldier').values()
            getVal = len([s for s in soldierCfgs if s.get('SoldierSide')==4 and s.get('OpenLevel')<=level])
                
#         elif mt==75:#招募普通将
#             gt = Gcore.getCfg('tb_cfg_general',valType,'GeneralSort')
#             if gt==0:
#                 getVal=val+curVal
                
        elif mt==76:#招募一名名将
            gt = Gcore.getCfg('tb_cfg_general',valType,'GeneralSort')
            if gt==1:
                getVal=val+curVal
        
        elif mt==80:#使用A道具多少次
            if data.get('ItemId')==paramA and val:
                getVal = curVal+1
                
        elif mt==81:#成功购买A道具B次
            goodsType = data.get('GoodsType')
            if goodsType==2 and valType==paramA:
                getVal = curVal+1
                
        elif mt==84:#当前拥有最高好感度
            maxFav = self.db.out_field('tb_friend','Max(Favor)','UserId=%s AND FriendStatus=2'%self.uid)
            if maxFav:
                fCfg = Gcore.getCfg('tb_cfg_friend_grade')
                curFav = 0
                for fc in fCfg.values():
                    if maxFav>=fc['Favor']:
                        curFav = fc['FriendGrade']
                if curFav>curVal:
                    getVal = curFav
        
        elif mt==85:#拜访获得宝箱
            existBox = data.get('ExistBox')
            if existBox:
                getVal = curVal+1
        
        elif mt==87:#对话收获美酒B次
            MCoin = data.get('MCoin')
            if MCoin>0:
                getVal = curVal+1
        
        elif mt==88:#当前拥有好友数量
            num = self.db.out_field('tb_friend','COUNT(1)','UserId=%s AND FriendStatus=2'%self.uid)
            if num>curVal:
                getVal = num
        
        elif mt==91:#通关A战役
            battleType = data.get('BattleType')
            if battleType==1 and data.get('WarId')==paramA and data.get('Result',{}).get('Star')>=1:
                getVal = curVal+1
            elif battleType is None:
                field = 'War%s'%paramA
                battleStar = self.db.out_field('tb_war_star',field,'UserId=%s'%self.uid)
                getVal = 1 if battleStar>=1 else 0

        elif mt==92:#PVE扫荡b次
            if data.get('BattleType')==1 and data.get('FromType')==1:
                getVal = curVal+1
                
        elif mt==93:#PVE立即结束b次
            if data.get('BattleType')==1 and data.get('EndType')==1:
                getVal = curVal+1
                
        elif mt==94:#PVE累计获得3星b次
            if data.get('BattleType')==1 and data.get('Result',{}).get('Star')==1:
                getVal = curVal+1
        
        elif mt==96:#PVP搜索攻城b次
            if data.get('BattleType')==2 and data.get('FromType')==1:
                getVal = curVal+1
        
        elif mt==99:#布防多少工事
            dLevel = data.get('Level')
            if dLevel>=paramA:
                getVal = curVal+val
        
        elif mt==102:#PVP报仇b次
            if data.get('BattleType')==2 and data.get('FromType')==2:
                getVal = curVal+1
                
        elif mt==38:#PVP反抗b次
            if data.get('BattleType')==2 and data.get('FromType')==3:
                getVal = curVal+1
        
        elif mt==103:#PVP攻城获得b军资
            if data.get('BattleType')==2:
                Jcoin = data.get('Result',{}).get('Coin',{}).get('Jcoin',0)
                getVal = curVal+Jcoin
        
        elif mt==105:#PVP攻城获得b荣誉
            if data.get('BattleType')==2:
                honour = data.get('Result',{}).get('Honour',0)
                getVal = curVal+honour
        
        elif mt==106:#PVP立即结束攻城b次
            if data.get('BattleType')==2 and data.get('EndType')==1:
                getVal = curVal+1
                
        elif mt==109:#打扫获得宝箱
            willGet = data.get('WillGet')
            if willGet==1:
                getVal = curVal+1
        
        elif mt==122:#扩充背包
            bagSize = data.get('BagSize')
            if bagSize:
                getVal = bagSize
            else:
                getVal = Gcore.getMod('Bag',self.uid).getBagSize()
                
        elif mt==124:#首冲
            totalPay = self.db.out_field('tb_user','VipTotalPay','UserId=%s'%self.uid)
            if totalPay>0:
                getVal = 1
                
        elif mt==125:#累积获得多少黄金
            totalPay = self.db.out_field('tb_user','VipTotalPay','UserId=%s'%self.uid)
            if totalPay>curVal:
                getVal = totalPay
                
        elif mt==126:#累积获得美酒
            curMC = Gcore.getMod('Coin',self.uid).getCoinNum(4)
            if curMC>curVal:
                getVal = curMC
        
        elif mt==127:#累积荣誉
            if val:
                getVal = curVal+val
            else:
                getVal = self.db.out_field('tb_user','UserHonour','UserId=%s'%self.uid)
        
        elif mt==129:#武将武力达到A
            generals = Gcore.getMod('General',self.uid).getLatestGeneralInfo()
            if generals:
                getVal = max(generals,key=lambda g:g['ForceValue']).get('ForceValue')

        elif mt==130:#武将智力达到A
            generals = Gcore.getMod('General',self.uid).getLatestGeneralInfo()
            if generals:
                getVal = max(generals,key=lambda g:g['WitValue']).get('WitValue')

        elif mt==131:#武将统帅达到A
            generals = Gcore.getMod('General',self.uid).getLatestGeneralInfo()
            if generals:
                getVal = max(generals,key=lambda g:g['LeaderValue']).get('LeaderValue')
            
        elif mt==132:#武将速度达到A
            generals = Gcore.getMod('General',self.uid).getLatestGeneralInfo()
            if generals:
                getVal = max(generals,key=lambda g:g['SpeedValue']).get('SpeedValue')
            
        elif mt==134:#使用A类道具
            if data.get('ItemId')and data.get('ItemId')/100==paramA/100:
                getVal = curVal+1
        
        elif mt==135:#绑定账号
            isBind = self.db.out_field('tb_user','BindAccount','UserId=%s'%self.uid)
            if isBind==1:
                getVal=1
        
        elif mt==136:#PVE带战鼓101通关“黄巾之乱-血战巨鹿”104
            if data.get('BattleType')==1 \
            and data.get('WarId')==104 \
            and (101 in data.get('Troops',{}).keys()) \
            and data.get('Result',{}).get('Star')>=1:
                getVal = curVal+1
        
        elif mt==137:#PVE带藤甲兵5通关“黄巾之乱-黄巾覆灭”105
            if data.get('BattleType')==1 \
            and data.get('WarId')==105 \
            and (5 in data.get('Troops',{}).keys()) \
            and data.get('Result',{}).get('Star')>=1:
                getVal = curVal+1
        
        elif mt==138:#PVE带突骑兵11通关“讨伐董卓-兴师讨逆”201
            if data.get('BattleType')==1 \
            and data.get('WarId')==201 \
            and (11 in data.get('Troops',{}).keys()) \
            and data.get('Result',{}).get('Star')>=1:
                getVal = curVal+1
        
        elif mt==139:#商城购买道具B次
            if val and data.get('GoodsType')==2:
                getVal = curVal+1
        
        elif mt==140:#商城购买装备B次
            if val and data.get('GoodsType')==1:
                getVal = curVal+1
                
        #@todo: 这里添加更多更新处理
        
        
        else:#默认处理，简单相加
            getVal=val+curVal
        
        
        #值不为0且大于当前，才执行更新
        if getVal and getVal>curVal:
            return getVal
        else:
            return 0
    
    def test(self):
        return self.db.update('tb_mission',{'GetValue':1},'UserId=44123 and missionid=1001')
               
def _test():
    '''测试'''
#     uid = 43415#
    uid = 44448
    m = MissionMod(uid)
    print m.initMission([1040])
#     print m.updateMissions({1001:{'GetValue':1}})
#     print m.getNewMission(userLevel=4)
#     print m.missionTrigger(22004,{'ValType':1101,'Val':1})
#     print m.getUserLevel()
#     print m.getMissionUpdateVal(1058)
#     print m.missionTrigger(1013)
#     print Gcore.setUserData(10011, {'ClubId':99})
#     print Gcore.getUserData(10011, 'ClubId')
#     print m.updateAllMissions()
#     print Gcore.getUserData(uid,'UserType')
#     print m.getMissionFinishNum()


    
if __name__=='__main__':
    _test()

