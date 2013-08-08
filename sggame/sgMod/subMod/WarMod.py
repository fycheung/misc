# -*- coding:utf-8 -*-
# author:
# date:2013-1-
# 游戏内部接口,模型模板
from __future__ import division
from sgLib.core import Gcore
from sgLib.base import Base
import math
import random
import gevent

testPerIncrTime = 60
class WarMod(Base):
    """docstring for ClassName模板"""
    def __init__(self, uid):
        '''注释'''
        Base.__init__(self,uid)
        self.uid = uid
        #print self.db #数据库连接类
        
    def test(self):
        '''测试方法'''
        
    def findPvcTarget(self):
        '''查找攻城对象  @note:硬凑在这里'''
        CrossServer = int(Gcore.loadCoreCfg('CrossServer')) #是否跨服的配置
        print ' -- ps findPvcTarget CrossServer:%s'%CrossServer
        
        N=200 #匹配参考值
        Num = 20 #每次拿10个
        if Gcore.TEST:
            Num = 100
        rowUser = self.getUserInfo(['UserCamp','UserLevel'])
        UserLevel = rowUser['UserLevel']
        UserCamp = rowUser['UserCamp']
        UserLevelFrom = UserLevel-30;
        UserLevelTo = UserLevel+30;
        ServerId = Gcore.getServerId()
        homeList1 = []
        homeList2 = []
        if(UserCamp==1):
            query = " (UserCamp=2 OR UserCamp=3)"
        elif(UserCamp==2):
            query = " (UserCamp=1 OR UserCamp=3)"
        elif(UserCamp==3):
            query = " (UserCamp=1 OR UserCamp=2)"
        
        query+= " AND UserLevel>=%s"%Gcore.loadCfg(9301).get('FightLevel')
        query+= " AND UserId!=%s"%self.uid
        query+= " AND Online=0 AND ProtectEndTime <= UNIX_TIMESTAMP()";
        where = query+' AND UserLevel>=%s AND UserLevel<=%s'%(UserLevelFrom,UserLevelTo)
        M = self.db.count('tb_user',where)
        
        UserLevelFrom2 = UserLevel-5;
        UserLevelTo2 = UserLevel+5;
        where = query+' AND UserLevel>=%s AND UserLevel<=%s'%(UserLevelFrom2,UserLevelTo2)
        for unit in  self.db.out_rand('tb_user','UserId',where,Num):
            homeList1.append([ServerId,unit['UserId']])
            
        print 'findPvcTarget local +-5 > ',self.db.sql
        
        where = query+' AND (UserLevel>=%s AND UserLevel<%s) OR (UserLevel>%s AND UserLevel<=%s)'\
        %(UserLevelFrom,UserLevelFrom2,UserLevelTo2,UserLevelTo)
        for unit in  self.db.out_rand('tb_user','UserId',where,Num):
            homeList2.append([ServerId,unit['UserId']])
            
        print 'findPvcTarget local +-30 > ',self.db.sql
        #print 'homeList1',homeList1
        #print 'homeList2',homeList2
        random.shuffle(homeList1)
        random.shuffle(homeList2)
        
        if M>=N:#不跨服
            crossPercent = 0 #跨服比例
        elif M<=20:
            crossPercent = 100
        elif M>=0.75*N: 
            crossPercent = 25
        elif M>=0.5*N: 
            crossPercent = 50
        elif M>=0.25*N: 
            crossPercent = 75
        else:
            crossPercent = 100

        #print 'crossPercent',crossPercent
        targetList = []
        randPercent = random.randint(1,100)
        #print 'randPercent',randPercent
        
        if randPercent<=crossPercent and CrossServer: #中比例
            y=math.ceil(M/N*Num)
            getNum = Num-y
#            print 'M',M
#            print 'N',N
#            print 'getNum',getNum
            targetList =  Gcore.getMod('Request', self.uid).findOutFighter(getNum,rowUser)
            print 'Request targetList',targetList
        
        #print targetList
        for i in xrange(Num-len(targetList)):
            if len(homeList1)>i:
                targetList.append(homeList1[i])
                if len(targetList)>=Num:
                    break;
            if len(homeList2)>i:
                targetList.append(homeList2[i])
                if len(targetList)>=Num:
                    break;
        #print 'targetList',targetList
        return targetList
    
    
    def getWarInfoAll(self):
        '''获取战役信息(新)'''
        
        ProcessWarId = self.getUserInfo('ProcessWarId')
        if ProcessWarId==0:
            ProcessWarId=101
        
        rows = Gcore.getCfg('tb_cfg_pve')
        
        fields = []
        for row in rows.values():
            
            fields.append('War%s'%row.get('WarId'))
            
        GradeInfo = self.db.out_fields('tb_war_star',fields,"UserId=%s"%self.uid)
        if not GradeInfo:
            self.db.insert('tb_war_star',{"UserId":self.uid})
            GradeInfo = self.db.out_fields('tb_war_star',fields,"UserId=%s"%self.uid)
        
        warInfo = {}
        showDict = self._getDropShowList()
        for row in rows.values():
            WarId = row['WarId']
            DropId = Gcore.getCfg('tb_cfg_pve',WarId,'DropId')
            StoryId = row['StoryId']
            
            
            WarCell = {
                        'warId':WarId,
                        'star':GradeInfo.get('War%s'%WarId),
                        'fight': 1 if WarId<=ProcessWarId else 0,
                        'rewards':showDict.get(DropId,{}),
                        'needAct':1,
                        }
            if StoryId not in warInfo:
                warInfo[ StoryId ] = []
            warInfo[ StoryId ].append( WarCell )
            
        data = {}  
        data['curWarId'] = ProcessWarId
        data['warInfo'] = warInfo
        
        return data
    
    
    def getWarDetail(self,StoryId):
        '''获取战役信息'''
        assert isinstance(StoryId, (int,long))
        
        ProcessWarId = self.getUserInfo('ProcessWarId')
        if ProcessWarId==0:
            ProcessWarId=101
        #curStoryId = self.db.out_field('tb_cfg_pve','StoryId',"WarId='%s'"%ProcessWarId)
        
        rows = self.db.out_rows('tb_cfg_pve',['WarId','StoryId'],"StoryId='%s'"%StoryId)
        
        
        StoryWar = {}
        fields = []
        for row in rows:
            fields.append('War%s'%row.get('WarId'))
            StoryWar[ row.get('WarId') ] = row.get('StoryId')
            
        sql = "SELECT count(1) AS count,WarId FROM tb_war_log WHERE UserId=%s AND RecordDate=CURDATE() Group by WarId"%self.uid
        rows = self.db.fetchall(sql)
        warlogDict = {}
        for row in rows:
            warlogDict[row['WarId']] = row['count']
            
        GradeInfo = self.db.out_fields('tb_war_star',fields,"UserId=%s"%self.uid)
        if not GradeInfo:
            self.db.insert('tb_war_star',{"UserId":self.uid})
            GradeInfo = self.db.out_fields('tb_war_star',fields,"UserId=%s"%self.uid)
        #print GradeInfo
        
        warInfo = []
        for WarId,StoryId in StoryWar.iteritems():
            WarCell = {
                        'warId':WarId,
                        'count':warlogDict.get(WarId,0),
                        'star':GradeInfo.get('War%s'%WarId),
                        'storyId':StoryId,
                        'fight': 1 if WarId<=ProcessWarId else 0,
                        #'open': 0 if WarId>ProcessWarId else 1,
                        #'current': 1 if WarId == ProcessWarId else 0,
                        }
            warInfo.append(WarCell)
            
        data = {}  
        data['maxCount'] = self.getUserInfo('WarTimes')
        #data['curStoryId'] = curStoryId
        data['curWarId'] = ProcessWarId
        data['warInfo'] = warInfo
        sweepedTimes = self._getSweepTimes()
        data['sweepRestTime'] = Gcore.loadCfg(9001).get('sweepTimesLimit') - sweepedTimes
        return data
    
    def _getSweepTimes(self):
        '''获取当天已扫荡次数'''
        sweepedTimes = self.db.count('tb_war_log',"UserId=%s AND RecordDate=CURDATE() AND IsWarSweep=1"%self.uid) 
        return sweepedTimes
    
    def warSweep(self,WarIdList):
        '''扫荡'''
        result = {}
        UserData = self.getUserInfo(['ProcessWarId'])
        ProcessWarId = UserData['ProcessWarId']
        
        rowStar = self.db.out_fields('tb_war_star','*','UserId=%s'%self.uid)
        RestPoint,MaxPoint = self.getActPoint()
        for warId in WarIdList:
            print '扫荡战役:',warId
            print '剩余行动力',RestPoint
            if not RestPoint: 
                print '剩余行动力为0'
                break
            
            if warId>ProcessWarId:
                print '战役未开启不可扫荡'
            
            if not rowStar.get('War%s'%warId):
                print '未打过通过的战役不可扫荡'
                
            #@todo 自动补兵
            modBattle = Gcore.getMod('Battle',self.uid,True)
            initWarResult = modBattle.initWar(warId,1) #定义为扫荡战役
            if not initWarResult:
                print '初始化战斗失败'
                break
            modBattle.getWarInfo()
            re = modBattle.endBattle({"resultType":5})
            print '战斗结果',re
            result[warId] = re #结构不能更改 需要和前台一样
            self.warlog(WarId=warId,IsWarSweep=1,Result=re.get('Result',0)) #@todo 添加更完整战役结果
            if not re.get('Result'):
                break
            else:
                RestPoint-=1

        #result返回结果需要跟正常战斗一样，不然会出错
        return result,RestPoint
    
    def warSweepNew(self,warId,SweepTimes):
        '''扫荡'''
        result = {}
        UserData = self.getUserInfo(['ProcessWarId'])
        ProcessWarId = UserData['ProcessWarId']
        
        rowStar = self.db.out_fields('tb_war_star','*','UserId=%s'%self.uid)
        RestPoint,MaxPoint = self.getActPoint()
        if warId>ProcessWarId or not rowStar.get('War%s'%warId):
            return False
              
        if RestPoint< Gcore.getCfg('tb_cfg_pve',warId,'ActPointNeed')*SweepTimes:
            return False
        else:
            Gcore.setUserData(self.uid, {'Sweeping':True} )
            
            #@todo 自动补兵
            for i in xrange(SweepTimes):
                restTimes = SweepTimes-i-1
                if not Gcore.getUserData(self.uid, 'Sweeping'): #用户落线也会停止
                    break
                else:
                    gevent.sleep( Gcore.loadCfg(9101).get('SweepSleep') ) #每场间隔3秒 读配置
                    
                modBattle = Gcore.getMod('Battle',self.uid,True)
                initWarResult = modBattle.initWar(warId,1) #定义为扫荡战役
                if not initWarResult:
                    print '初始化战斗失败'
                    break
                modBattle.getWarInfo()
                re = modBattle.endBattle({"resultType":5})
                #print '战斗结果',re
                result[warId] = re #结构不能更改 需要和前台一样
                self.warlog(WarId=warId,IsWarSweep=1,Result=re.get('Result',0)) #@todo 添加更完整战役结果
                
                Gcore.push(111,self.uid,{'result':result,'restPoint':RestPoint,'restTimes':restTimes})
                if not re.get('Result'):
                    break
                else:
                    RestPoint-=1

            return True  
                

        #result返回结果需要跟正常战斗一样，不然会出错
        #return result,RestPoint
    
    def warlog(self,**kw):
        '''战役日志'''
        kw['UserId'] = self.uid
        kw['RecordDate'] = Gcore.common.today()
        kw['CreateTime'] = Gcore.common.nowtime()
        self.db.insert('tb_war_log',kw)
        #print self.db.sql
    
    def _checkGeneralSoldier(self):
        '''检查是否有上阵且带兵的武将'''
        result = bool( self.db.count(self.tb_general(),"UserId=%s AND PosId>0 AND TakeNum>0"%self.uid) )
        return result
    
    #-------------------------------------战役行动力----------------------------------
    def buyActPoint(self,point=0):
        '''增加行动点数 
        @param point: 增加的点数'''
        print 'ps buyActPoint'
        if not point:
            point = Gcore.loadCfg(9101).get('PerBuyAddPoint')
        row = self.recoverActPoint(point,1)
#        if row:
#            todaytime = Gcore.common.today0time()
#            sql = "UPDATE tb_war_action SET ActPoint=ActPoint+%s WHERE UserId=%s AND LastWarTime>=%s" \
#            %(point,self.uid,todaytime)
#            self.db.execute(sql) #如果今日有打过 就修正累计记录
#            print 'buyActPoint',sql
            
        sql = "UPDATE tb_user SET BuyActPoint=BuyActPoint+%s WHERE UserId=%s"%(point,self.uid)
        AddResult = self.db.execute(sql)
        
        try: #可购买上限
            sql ="UPDATE tb_log_buy_act SET Times = Times+1 WHERE UserId=%s AND BuyDate = CURDATE()"%self.uid
            result = self.db.execute(sql)
            if not result: #无影响行数
                sql = "INSERT INTO tb_log_buy_act (UserId,Times,BuyDate) VALUES(%s,1,CURDATE())"%self.uid
                result = self.db.execute(sql)
        except:
            pass
        finally:
            return AddResult    
    
    def useActPoint(self,point=1):
        '''战役成功，使用一点行动力'''
        BuyActPoint = self.getUserInfo('BuyActPoint')
        if BuyActPoint: 
            if  BuyActPoint>=point:
                cutPoint = point 
                BuyActPoint -= point
            else: #剩余购买行动力已不够扣减
                cutPoint = BuyActPoint
                #point -= BuyActPoint #剩余部分需在未购买处扣
                BuyActPoint =0
                print '剩余购买行动力已不够扣减,point:',point
            sql = 'UPDATE tb_user SET BuyActPoint=BuyActPoint-%s WHERE UserId=%s'%(cutPoint,self.uid)
            self.db.execute(sql)
            #print '已购买的行动力扣1,剩余',BuyActPoint
    
        MaxPoint = Gcore.getCfg('tb_cfg_action_point',self.getUserLevel(),'ActPoint')
        row = self.recoverActPoint(point,0)
        if row: #今天有打过
            pass
        else: #今天未打过
            #print '今天未打过'
            row = {}
            row['ActPoint'] = MaxPoint + BuyActPoint 
            row['LastWarTime'] = Gcore.common.nowtime()
            res = self.db.update('tb_war_action',row,'UserId=%s'%self.uid)
            if not res: #从来没有记录
                row['UserId'] = self.uid
                self.db.insert('tb_war_action',row)
            
    def getActPoint(self):
        '''获得 剩余行动点数/最大行动点数'''
        BuyActPoint = self.getUserInfo('BuyActPoint')
        row = self._lastActRecord()
        MaxPoint = Gcore.getCfg('tb_cfg_action_point',self.getUserLevel(),'ActPoint')
        if not row:
            RestPoint = MaxPoint + BuyActPoint
        else:
            nowtime = Gcore.common.nowtime()
            PerIncrTime = Gcore.loadCfg(9101).get('ActPointRecoverTime',1200)
            if Gcore.TEST and self.uid in [1001,43953]:
                PerIncrTime = testPerIncrTime
            if row['ActPoint']>=MaxPoint: #已满,不恢复
                RestPoint = row['ActPoint']
            else:
                AccuTime = row['AccuTime'] + ( nowtime - row['LastWarTime'] )
                incrTimes = AccuTime//PerIncrTime #回复一点需要多长时间 20分钟
                #print 'incrTimes',incrTimes
                print 'getActPoint.上次剩余',row['ActPoint']
                print 'getActPoint.至已经恢复了',incrTimes
                ActPoint = row['ActPoint'] + incrTimes
                if ActPoint > MaxPoint:
                    ActPoint = MaxPoint
                    print 'getActPoint.剩余+累计越出上限,设为上限',ActPoint
                    
                #查看的时候 不更新累计时间 tb_war_action.AccuTime    
                RestPoint = ActPoint
            
        #print '剩余次数    最大次数',RestPoint,MaxPoint， 前台显示的是: 剩余次数/最大次数
        return (RestPoint,MaxPoint)
    

    def recoverActPoint(self, changePoint = 0, flag = 1):
        '''恢复行动力
        changePoint:要增加或减少的数 
        flag: 1增加 0减少
        '''
        row = self._lastActRecord() #没记录就是 {}
        if row:
            MaxPoint = Gcore.getCfg('tb_cfg_action_point',self.getUserLevel(),'ActPoint')
            nowtime = Gcore.common.nowtime()
            if row['ActPoint']>=MaxPoint:#剩余点数超过最大值  不开始累积时间 !
                AccuTime = 0
                ActPoint = row['ActPoint']
                print '购买+剩余点数超过最大值  不开始累积时间 !'
            else:
                PerIncrTime = Gcore.loadCfg(9101).get('ActPointRecoverTime',1200)
                if Gcore.TEST and self.uid in [1001,43953]:
                    PerIncrTime = testPerIncrTime
                AccuTime = row['AccuTime'] + ( nowtime - row['LastWarTime'] )
                incrTimes = AccuTime//PerIncrTime #回复一点需要多长时间 20分钟
                if incrTimes:
                    AccuTime = AccuTime%PerIncrTime
                print 'recoverActPoint.上次剩余',row['ActPoint']
                print 'recoverActPoint.至已经恢复了',incrTimes
                ActPoint = row['ActPoint'] + incrTimes
                if ActPoint >= MaxPoint:
                    ActPoint = MaxPoint
                    AccuTime = 0
            if flag:
                ActPoint += changePoint
            else:
                ActPoint -= changePoint
            d = {
                 'ActPoint':ActPoint,
                 'LastWarTime':nowtime,
                 'AccuTime':AccuTime
                 }
            self.db.update('tb_war_action',d,'UserId=%s'%self.uid)
            row['ActPoint'] = ActPoint
            row['LastWarTime'] = nowtime
            row['AccuTime'] = AccuTime
        
        return row #返回新的记录
            
    def _lastActRecord(self):
        '''获取今天最新的行动记录'''
        todaytime = Gcore.common.today0time()
        row = self.db.out_fields('tb_war_action','*','LastWarTime>%s AND UserId=%s'%(todaytime,self.uid))
        return row
    
    def getTodayBuyTimes(self):
        '''获得今天购买次数'''
        where = 'UserId=%s AND BuyDate=CURDATE()'%self.uid
        Times = self.db.out_field('tb_log_buy_act','Times',where)
        print self.db.sql
        if not Times:
            Times = 0
        return Times
    
    def touchActPoint(self,oldLevel,newLevel):
        '''更新行动力,升级时调用'''
        newLevelPoint = Gcore.getCfg('tb_cfg_action_point',newLevel,'ActPoint')
        oldLevelPoint = Gcore.getCfg('tb_cfg_action_point',oldLevel,'ActPoint')
        diffPoint = newLevelPoint - oldLevelPoint
        if diffPoint:
            row = self._lastActRecord()
            if row:
                todaytime = Gcore.common.today0time()
                sql = "UPDATE tb_war_action SET ActPoint=ActPoint+%s WHERE UserId=%s AND LastWarTime>=%s" \
                %(diffPoint,self.uid,todaytime)
                self.db.execute(sql) #如果今日有打过 就修正累计记录
        
    def _getDropShowList(self):
        '''获得高级掉落物品列表,在打战役前显示'''
        showDict = {}
        for k,rows in Gcore.getCfg('tb_cfg_pve_drop').iteritems():
            DropId,Star = k
            
            if DropId not in showDict:
                showDict[DropId] = []
            for row in rows:
                if row['Ratio'] == 0:
                    continue
                row['RewardType'] = int(row['RewardType'])
                if row['RewardType'] in (1,2,4,5,6):
                    cell = {'RewardType':row['RewardType'],'GoodsId':row['GoodsId']}
                    if row['RewardType'] == 1: #装备
                        Quality = Gcore.getCfg('tb_cfg_equip',row['GoodsId'],'Quality')
                        if Quality>=2: #紫装以上
                            if cell not in showDict[DropId]:
                                showDict[DropId].append(cell)
                    elif row['RewardType'] == 2: #道具
                        Quality = Gcore.getCfg('tb_cfg_item',row['GoodsId'],'ItemQuality')
                        if Quality>0: #全掉 
                            if cell not in showDict[DropId]:
                                showDict[DropId].append(cell)
                    else:
                        if cell not in showDict[DropId]:
                                showDict[DropId].append(cell)
                    
            #break
        for DropId in showDict:
            showDict[DropId] =  Gcore.common.list2dict(showDict[DropId])  
        
        return showDict
    
    
if __name__ == '__main__':
    uid = 1001
    c = WarMod(uid)
    #Gcore.printd( c._getDropShowList() )
    #d = c.getWarInfoAll()
    #d = c.warSweep([101,102,103])
    #Gcore.printd(d)
    #@todo 战役待详细测试
    #c.useActPoint(1)
    #c.buyActPoint(5)
    #print c.getActPoint()
    
    c.useActPoint()
    print c.getActPoint()
    
    '''
    import time
    for i in xrange(10):
        c.useActPoint()
        time.sleep(2)
    '''
    #c.getNowActPoint()
    
    
    #c.getNowActPoint()
    #Gcore.printd( c.getWarDetail(1) )
    #Gcore.printd(  c.warSweep([103]) ) #1021007  "WarIdList":    [101, 102, 103, 104, 105]
    #c.findPvcTarget()
    #Gcore.runtime()
