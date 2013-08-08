# -*- coding:utf-8 -*-
# author:Lizr
# date:2013-8-1
# 排名争斗 演武场 比武 模型

from gevent import sleep
from sgLib.core import Gcore
from sgLib.base import Base

common = Gcore.common
class RankFightMod(Base):
    """排名争斗 演武场 比武  模型"""
    def __init__(self, uid):
        '''注释'''
        Base.__init__(self,uid)
        self.uid = uid
        self.cfgRank = Gcore.loadCfg(Gcore.defined.CFG_RANK_FIGHT)
        #print self.db #数据库连接类
        
    def test(self):
        '''测试方法'''
        
    def initRank(self):
        '''功能上传时，只运行一次
        @note:初始化排名榜,将等级超过排名等级,但又没在排名榜的玩家,按等级降序,ID升序插到排行表的外面
        @remark:也可检查补插记录
        '''
        openLevel = self.cfgRank.get('RankFightOpenLevel',20)
        where = 'UserLevel>=%s ORDER BY UserLevel DESC,UserId ASC'%openLevel
        for UserId in self.db.out_list('tb_user','UserId',where):
            if not self.db.out_field('tb_rank_fight','UserId','UserId=%s'%UserId):
                self.db.insert('tb_rank_fight', {'UserId':UserId})
                print self.db.sql
    
    def getRankFightInfo(self):
        '''获取比武界面数据'''
        row = self._getRank()
        info = {}
        info['RankId'] = row['RankId'] #我的排名
        info['SpeendCostValue'] = self.cfgRank.get('SpeendCostValue')
        info['RestTimes'] = self.cfgRank.get('EverydayTimes') - row['TodayFightTimes'] #剩余争夺次数
        info['RestFightTime'] = self.cfgRank.get('FightIntervalTime') - (common.nowtime()-row['LastFightTime'])
        if info['RestFightTime']<0:
            info['RestFightTime'] = 0  #争夺冷却时间
        
        info['LogRecord'] = self._getLogRecord()
        info['Opponent'] = self._getOpponentSample()
        return info
    
    def joinRankFight(self):
        '''加入排名,升到需求等级(默认20)时调用'''
        
        if not self.db.out_field('tb_rank_fight','UserId','UserId=%s'%self.uid):
            self.db.insert('tb_rank_fight', {'UserId':self.uid})
                
    
    def speedupRankFight(self):
        '''加速争夺冷却时间'''
        result = self.db.update('tb_rank_fight',{'LastFightTime':0},'UserId=%s'%self.uid)
        return 1 if result else 0
    
    def updateFightTimes(self,onlyTime=False):
        '''更新比武次数
        @param onlyTime: 是否只更新时间不更新次数
        '''
        row = self._getRank()
        if onlyTime:
            arr = {'LastFightTime':common.nowtime()} #从比武结束开始冷却
        else:
            TodayFightTimes = row['TodayFightTimes']+1
            arr = {'LastFightTime':common.nowtime(),'TodayFightTimes':TodayFightTimes} #顺便更新一下时间
        self.db.update('tb_rank_fight',arr,'UserId=%s'%self.uid)
        print 'sql',self.db.sql
        
#    def fightUpdate(self):
#        '''争夺排名后,更新时间,和次数'''
#        row = self._getRank()
#        TodayFightTimes = row['TodayFightTimes']+1
#        arr = {'LastFightTime':common.nowtime(),'TodayFightTimes':TodayFightTimes}
#        self.db.update('tb_rank_fight',arr,'UserId=%s'%self.uid)
    
    def exchangeRank(self,OpUserId):
        '''自己和对手交换排名,当比武胜利时调用
        @param OpUserId: 对手的用户ID
        @return False or List 
        @note 注意并发的情况(稍有麻烦 亦可考虑普通方法)
        '''
        for i in xrange(5): #重复5次
            sql = 'UPDATE tb_rank_fight SET LockUserId=%s WHERE LockUserId=0 AND UserId=%s'%(self.uid,self.uid)
            affected = self.db.execute(sql) #先自我锁定
            if not affected:
                sleep(1)
            else:
                row = self._getRank()
                MyRankId = row['RankId']
        
            sql = 'UPDATE tb_rank_fight SET LockUserId=%s WHERE LockUserId=0 AND UserId=%s' \
            %(self.uid,OpUserId)
            affected = self.db.execute(sql) #锁定对方
            if not affected:
                sleep(1)
            else:
                OpRankId = self.db.out_field('tb_rank_fight','RankId','UserId=%s AND LockUserId=%s'%(OpUserId,self.uid))
                if OpRankId < MyRankId: #我的排名比对手后
                    sql = 'UPDATE tb_rank_fight SET UserId=%s,LockUserId=0 WHERE RankId=%s'%(OpUserId,MyRankId) #将我的排名换给对手
                    result = self.db.execute(sql)
                    if result:
                        sql = 'UPDATE tb_rank_fight SET UserId=%s,LockUserId=0 WHERE LockUserId=%s'%(self.uid,self.uid)
                        result = self.db.execute(sql)
                        if result:
                            return True
            break
            
        sql = 'UPDATE tb_rank_fight SET LockUserId=0 WHERE LockUserId=%s'%self.uid
        self.db.execute(sql) #解死锁
        return False
    
    def getRankReward(self):
        '''获取排名奖励界面'''
        data = {}
        data['RewardTime'] = Gcore.loadCfg(Gcore.defined.CFG_RANK_FIGHT).get('RewardTime','22:00:00')
        RankId = self.db.out_field('tb_rank_fight_last','RankId','UserId=%s'%self.uid)
        data['RewardRankId'] = RankId if RankId else 0
        cfg_rank_reward = Gcore.getCfg('tb_cfg_rank_reward')
        data['RewardBoxList'] = {}
        
        MyRewardRankId = data['RewardRankId']
        for k,v in cfg_rank_reward.iteritems():
            data['RewardBoxList'][k] = {
                                        'RewardId':v['RewardId'],
                                        'RankFrom':v['RankFrom'],
                                        'RankTo':v['RankTo'],
                                        'Bright':1 if v['RankFrom']<=MyRewardRankId<=v['RankTo'] else 0
                                        }
            data['RewardBoxList'][k]['Rewards'] = []
            for i in xrange(1,6):
                field1 = 'RewardType%s'%i
                field2 = 'GoodsId%s'%i
                field3 = 'GoodsNum%s'%i
                if v[field1] and v[field2]:
                    cell = {'RewardType':v[field1], 'GoodsId':v[field2], 'GoodsNum':v[field3]}
                    data['RewardBoxList'][k]['Rewards'].append(cell)
        return data
    
    def gainRankReward(self,optId=0):
        '''领取排名奖励'''
        row = self.db.out_fields('tb_rank_fight_last','RankId,Rewarded','UserId=%s'%self.uid)
        MyRewardRankId = row['RankId']
        Rewarded = row['Rewarded']
        gainRewardList = []
        if Rewarded:
            return gainRewardList
            
        cfg_rank_reward = Gcore.getCfg('tb_cfg_rank_reward')
        affected = self.db.update('tb_rank_fight_last',{'Rewarded':1},'Rewarded=0 AND UserId=%s'%self.uid)
        if affected:
            for k,v in cfg_rank_reward.iteritems():
                if v['RankFrom']<=MyRewardRankId and MyRewardRankId<=v['RankTo']:
                    for i in xrange(1,6):
                        field1 = 'RewardType%s'%i
                        field2 = 'GoodsId%s'%i
                        field3 = 'GoodsNum%s'%i
                        if v[field1] and v[field2]:
                            Gcore.getMod('Reward',self.uid).reward(optId, {}, v[field1], v[field2], v[field3])
                            gainRewardList.append({'RewardType':v[field1], 'GoodsId':v[field2], 'GoodsNum':v[field3]})
                    break
        
        return gainRewardList
            
    def _getOpponentSample(self):
        '''根据规则获取 我的对手'''
        import random
        row = self._getRank()
        RankId = row['RankId']
        MaxRankId = self.db.out_field('tb_rank_fight','Max(RankId)')
        
        if RankId>1000:
            pop = 200
        elif 1000>=RankId>500:
            pop = 100
        elif 500>=RankId>200:
            pop = 50
        elif 200>=RankId>3:
            pop = 10
        elif 3>=RankId>0:
            pop = 3
        
        uplimit = RankId-pop if RankId-pop>1 else 1 #最前是第1名
        downlimit = MaxRankId if  MaxRankId < RankId + 10 else RankId + 10 
        downSelectNum = 5 if downlimit - RankId >= 5 else downlimit - RankId #正常是2 包尾除外
        upSelectNum = 5 if RankId - uplimit >= 5 else RankId - uplimit #正常是3 前列除外
        
        downSample = random.sample(xrange(RankId+1,downlimit+1),downSelectNum)
        upSample = random.sample(xrange(uplimit,RankId),upSelectNum)
        if 0:
            print '*'*40
            print '我的排名',RankId
            print '取多少名之内 pop',pop
            print '取名上限 uplimit',uplimit
            print '取名下限 downlimit',downlimit
            print '往下取 downSelectNum',downSelectNum
            print '往上取 upSelectNum',upSelectNum
            
            print '取出的后面人 downSample',downSample
            print '取出的前面人 upSample',upSample
        
        targetSample = []
        if len(upSample)<3:
            targetSample += upSample
            downSelectNum = min([downSelectNum, 5 - len(upSample)])
            targetSample += random.sample(downSample,downSelectNum)
        elif len(downSample)<2:
            targetSample += downSample
            upSelectNum = min([upSelectNum, 5 - len(downSample)])
            targetSample += random.sample(upSample,upSelectNum)
        else:
            targetSample += random.sample(downSample,2)
            targetSample += random.sample(upSample,3)
        
        OpponentSample = []
        if targetSample:
            targetSample.sort(reverse=True)
            where = 'UserId<>%s AND '%self.uid
            where += self.db.inWhere('RankId',targetSample)
            sql = 'SELECT tb_user.*,tb_rank_fight.RankId FROM tb_user INNER JOIN tb_rank_fight ON tb_user.UserId=tb_rank_fight.UserId WHERE %s ORDER BY RankId'%where
            rows = self.db.fetchall(sql)
            
            for row in rows:
                d = {
                     'UserId':row['UserId'],
                     'UserLevel':row['UserLevel'],
                     'NickName':row['NickName'],
                     'UserIcon':row['UserIcon'],
                     'RankId':row['RankId'],
                     'ServerId':Gcore.getServerId(),
                     }
                OpponentSample.append(d)
        OpponentSample = common.list2dict(OpponentSample)
        
        return OpponentSample
    
    def makeRankLog(self,OpUserId,FightResult,MyRankId):
        '''制造日志
        OpUserId: 对手用户ID
        FightResult : 战斗结果
        MyRankId: 我的排名
        OpRankId: 对方的排名
        '''
        if FightResult:
            ToRankId = self.db.out_field('tb_rank_fight','RankId','UserId=%s'%self.uid)
        else:
            ToRankId = MyRankId
        d = {
             'UserId':self.uid,
             'NickName':Gcore.getUserData(self.uid,'NickName'),
             'OpUserId':OpUserId,
             'OpNickName':Gcore.getUserData(OpUserId,'NickName'),
             'FightResult':FightResult,
             'FromRankId':MyRankId,
             'ToRankId':ToRankId,
             'CreateTime':Gcore.common.nowtime(),
             }
            
        self.db.insert('tb_rank_fight_log',d)
            
    def _getLogRecord(self):
        '''获取比武战报信息'''
        num = self.cfgRank.get('LogRecordNum')
        fields ='*,IF(UserId=%s,1,0) AS iFight,IF(UserId=%s,OpNickName,NickName) AS PeerName'%(self.uid,self.uid)
        
        where = 'UserId=%s OR OpUserId=%s ORDER BY RankLogId DESC LIMIT 0,%s'%(self.uid,self.uid,num)
        
        rows = self.db.out_rows('tb_rank_fight_log',fields,where)
        ls = []
        for row in rows:
            row.pop('OpNickName')
            row.pop('NickName')
            ls.append(row)
        return common.list2dict(ls)
    
    def _getRank(self,UserId=None):
        '''获取我的排名记录相关信息,一条'''
        if not UserId:
            UserId = self.uid
        row =  self.db.out_fields('tb_rank_fight','*','UserId=%s'%UserId)
        
        #-------------- 特殊情况处理:超过等级 但未入排名 -------------
        if not row:
            UserLevel = Gcore.getUserData(UserId,'UserLevel')
            OpenLevel = Gcore.loadCfg(2401).get('RankFightOpenLevel')
            if UserLevel >= OpenLevel:
                self.db.insert('tb_rank_fight',{'UserId':UserId})
            row =  self.db.out_fields('tb_rank_fight','*','UserId=%s'%UserId)
        #----------------------------------------------------------
             
        if row['LastFightTime'] < common.today0time(): #上一次是昨天
            row['TodayFightTimes'] = 0
        
        return row
    
    def checkGetReward(self):
        '''检查我是否可以领取排名奖励'''
        Rewarded = self.db.out_field('tb_rank_fight_last','Rewarded','UserId=%s'%self.uid)
        if Rewarded==1:
            return -1  #您今天已经领取过奖励
        elif Rewarded is None:
            return -2  #不符合领取奖励条件
        else:
            return 1 #可以
    
    def checkCanFight(self):
        '''检查我是否还可以比武  True可以比武, False已达比武上限'''
        row = self._getRank()
        print '%s,%s'%(self.cfgRank.get('EverydayTimes') , row['TodayFightTimes'])
        return self.cfgRank.get('EverydayTimes') > row['TodayFightTimes']
        
if __name__ == '__main__':
    printd = Gcore.printd
    uid = 1001 #44448
    c = RankFightMod(uid)
    #c.initRank()
    #c.joinRankFight()
    #c.fightUpdate()
    #c.speedupRankFight()
    printd( c._getLogRecord() )
    #c.fightUpdate()
    #printd ( c.getRankFightInfo() )
    #print c.getOpponentSample()
    #Gcore.printd( c.getRankReward() )
    #print c.gainRankReward()
    
    '''排名的并发占位
    no1 = 43301
    def test1():
        uid = 43553
        c = RankFightMod(uid)
        c.exchangeRank(no1)
    
    def test2():
        uid = 43306
        c = RankFightMod(uid)
        c.exchangeRank(no1)
        
    def test3():
        uid = 43416
        c = RankFightMod(uid)
        c.exchangeRank(no1)
        
    import gevent
    chs = []
    chs.append(gevent.spawn(test1))
    chs.append(gevent.spawn(test2))
    chs.append(gevent.spawn(test3))
    chs.append(gevent.spawn(test4))
    gevent.joinall(chs)
    '''
    
    