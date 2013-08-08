# -*- coding:utf-8 -*-
# author:Lizr
# date:2013-3-16
# 游戏内部接口,内政

from __future__ import division
from sgLib.core import Gcore
from sgLib.base import Base
import math
import time

class InterMod(Base):
    """内政模型"""
    def __init__(self, uid):
        Base.__init__(self,uid)
        self.uid = uid

    # 内政效果
    # + 1 丰登 增加军资产量
    # + 2 铸造 增加铸币产量
    # + 3 屯兵 提升校场容纳士兵数量
    # + 4 天工 缩短建筑建造时间
    # + 5 鲁班 缩短器械制造时间
    # + 6 募兵 缩短征兵消耗
    # + 7 巧匠 减少建造消耗
    # + 8 精炼 减少装备强化消耗
    # + 9 威严 减少武将训练
    # + 10 慧眼 减少武将培养消耗 

    def getInterEffect(self, interType, value, TimeStamp=None):
        '''
        :计算内政影响
        @param interType:内政类型
        @param value:参数值
        @return: -int
        '''
        effect = self.getInter().get(interType,0)
        if interType in (1,2,3):#增加
            value = value*(1+effect)
        elif interType in (4,5,6,7,8,9,10):#减少
            value = value*(1-effect)
        return int(math.ceil(value))

    def getInterEffects(self, origin_values, TimeStamp=None):
        '''origin_values-dict-key:内政类型，value:原始数值'''
        #written by zhoujingjiang
        inters = self.getInter(TimeStamp=TimeStamp)
        
        ret_dic ={}
        for typ in origin_values:
            effect = inters.get(typ, 0)
            value = origin_values[typ] * ((1 + effect) if typ in (1, 2, 3) \
                                            else (1 - effect))
            ret_dic[typ] = int(value)
        return ret_dic

    def getInter(self, UserIds=None, TimeStamp=None):
        '''获取内政加成信息'''
        # 修改 - 周井江
        # + 不提供参数，返回：字典 - 自己的内政信息 {1:0.01, ...}
        # + 参数是用户ID，返回：字典 - 该用户的内政信息 {1:0.01, ...}
        # + 参数是用户ID的序列，返回：字典组成的字典  {UserId1:DictInter1, ...}
        tag = True #用来确定返回类型
        if not UserIds:
            where = 'UserId="%s"' % self.uid
        elif not isinstance(UserIds, (list, tuple)):
            where = 'UserId=%d' % int(UserIds)
        else:
            tag = False
            where = 'UserId =' + ' OR UserId = '.join(map(str, UserIds))

        RetDic = {}
        curtime = time.time() if not TimeStamp else TimeStamp
        rows = self.db.out_rows('tb_inter', '*', where)
        for row in rows:
            Inter1 = row['InterVip1'] + row['InterGeneral1'] + row['InterTech1Up']
            Inter2 = row['InterVip1'] + row['InterGeneral2'] + row['InterTech2Up']
            Inter3 = row['InterVip1'] + row['InterGeneral3'] + row['InterTech3Up']
            Inter4 = row['InterVip1'] + row['InterGeneral4'] + row['InterTech4Up']
            Inter5 = row['InterVip1'] + row['InterGeneral5'] + row['InterTech5Up']
            Inter6 = row['InterVip1'] + row['InterGeneral6'] + row['InterTech6Up']
            Inter7 = row['InterVip1'] + row['InterGeneral7'] + row['InterTech7Up']
            Inter8 = row['InterVip1'] + row['InterGeneral8'] + row['InterTech8Up']
            Inter9 = row['InterVip1'] + row['InterGeneral9'] + row['InterTech9Up']
            Inter10 = row['InterVip1'] + row['InterGeneral10'] + row['InterTech10Up']
            
            #科技升级未完成
            if curtime < row['Inter1UpTime']:
                Inter1 = Inter1 - row['InterTech1Up'] + row['InterTech1']
            if curtime < row['Inter2UpTime']:
                Inter2 = Inter2 - row['InterTech2Up'] + row['InterTech2']
            if curtime < row['Inter3UpTime']:
                Inter3 = Inter3 - row['InterTech3Up'] + row['InterTech3']
            if curtime < row['Inter4UpTime']:
                Inter4 = Inter4 - row['InterTech4Up'] + row['InterTech4']
            if curtime < row['Inter5UpTime']:
                Inter5 = Inter5 - row['InterTech5Up'] + row['InterTech5']
            if curtime < row['Inter6UpTime']:
                Inter6 = Inter6 - row['InterTech6Up'] + row['InterTech6']
            if curtime < row['Inter7UpTime']:
                Inter7 = Inter7 - row['InterTech7Up'] + row['InterTech7']
            if curtime < row['Inter8UpTime']:
                Inter8 = Inter8 - row['InterTech8Up'] + row['InterTech8']
            if curtime < row['Inter9UpTime']:
                Inter9 = Inter9 - row['InterTech9Up'] + row['InterTech9']
            if curtime < row['Inter10UpTime']:
                Inter10 = Inter10 - row['InterTech10Up'] + row['InterTech10']
                
            DictInter = {
                         1:Inter1,  #丰登 增加军资产量
                         2:Inter2,  #铸造 增加铸币产量
                         3:Inter3,  #屯兵 提升校场容纳士兵数量
                         4:Inter4,  #天工 缩短建筑建造时间
                         5:Inter5,  #鲁班 缩短器械制造时间
                         6:Inter6,  #募兵 缩短征兵时间
                         7:Inter7,  #巧匠 减少建造消耗
                         8:Inter8,  #精炼 减少装备强化消耗
                         9:Inter9,  #威严 减少武将训练消耗
                         10:Inter10,#慧眼 减少武将培养消耗 
                         }
            if tag:
                return DictInter
            RetDic.setdefault(row['UserId'], DictInter)
        return RetDic
        
    
    def updateInterVip(self):
        '''更新内政VIP加成,升级VIP时调用'''
        VipLevel = self.db.out_field('tb_user','VipLevel',"UserId=%s"%self.uid)
        
        CfgVipInter =  Gcore.getCfg('tb_cfg_vip_inter',VipLevel)
        d = {
             'InterVip1':CfgVipInter.get('AddInter1'),
             'InterVip2':CfgVipInter.get('AddInter2'),
             'InterVip3':CfgVipInter.get('AddInter3'),
             'InterVip4':CfgVipInter.get('AddInter4'),
             'InterVip5':CfgVipInter.get('AddInter5'),
             'InterVip6':CfgVipInter.get('AddInter6'),
             'InterVip7':CfgVipInter.get('AddInter7'),
             'InterVip8':CfgVipInter.get('AddInter8'),
             'InterVip9':CfgVipInter.get('AddInter9'),
             'InterVip10':CfgVipInter.get('AddInter10'),
             }
        self.db.update('tb_inter',d,"UserId=%s"%self.uid)
        Gcore.getMod('Event',self.uid).interGet()#事件触发
            
    def updateInterTech(self,TechType,TechLevel,LastEndTime):
        '''更新内政科技加成,内政科技升级时调用
        @param TechType: 内政科技类型
        @param TechLevel: 科技等级 (升级后)
        @param LastEndTime: 升级完成时间
        '''
        TechLevelDown = TechLevel-1 #前一等级
        oldValue = Gcore.getCfg('tb_cfg_tech_inter',(TechType,TechLevelDown),'InterEffect')
        newValue = Gcore.getCfg('tb_cfg_tech_inter',(TechType,TechLevel),'InterEffect')
        print oldValue, newValue
        oldField = 'InterTech%s'%TechType
        newField = 'InterTech%sUp'%TechType
        TimeField = 'Inter%sUpTime'%TechType
        d = {
             oldField:oldValue,
             newField:newValue,
             TimeField:LastEndTime,
             }
        self.db.update('tb_inter',d,"UserId=%s"%self.uid)
        Gcore.getMod('Event',self.uid).interGet()#事件触发
        print self.db.sql
        
    def updateInterGeneral(self):
        '''更新内政武将加成,每天定时执行时调用 (更新所有人 与self.uid无关)'''
        
        TBNUM = Gcore.config.TBNUM
        for i in xrange(TBNUM):
            EffectInfo = {}
            sql = "SELECT UserId,ForceValue,Witvalue,SpeedValue,LeaderValue,b.InterEffectId \
            FROM tb_general%s a INNER JOIN tb_cfg_general b ON a.GeneralType = b.GeneralType"%i
            rows = self.db.fetchall(sql)
            for row in rows:
                UserId = row['UserId']
                TotalAttr = row['ForceValue']+row['Witvalue']+row['SpeedValue']+row['LeaderValue']
                if UserId not in EffectInfo:
                    EffectInfo[UserId]={}
                InterTypeList = str(row['InterEffectId']).split(',')
                for InterType in InterTypeList:
                    if int(InterType):
                        if InterType not in EffectInfo[UserId]:
                            EffectInfo[UserId][InterType] = 0
                        #单个计算，也可优化为分组计算
                        EffectInfo[UserId][InterType]+=self._calInterGeneral(InterType, TotalAttr) 
            
            #print EffectInfo
            for UserId,dictInter in EffectInfo.iteritems():
                if not dictInter:
                    continue
                d = {}
                for InterType,InterValue in dictInter.iteritems():
                    d['InterGeneral%s'%InterType] = round(math.floor(InterValue*100)/100,2) #去掉2位小数以后
                
                self.db.update('tb_inter',d,"UserId=%s"%UserId)
                #print self.db.sql

    def _calInterGeneral(self,InterType,TotalAttr):
        '''计算属性加成内政公式
        @武将内政效果=初始数值+属性加成
        @属性加成=阀值*(该武将属性总和*系数/(该武将属性总和*系数+1))*100%
        '''

        attr_init = {1:0.01,2:0.01,3:0.01,4:0.01,5:0.01,6:0.01,7:0.01,8:0.01,9:0.01,10:0.01} #初始数值
        factor = 0.00002#系数
        divider = 0.15 #阀值
        initvalue = attr_init.get( int(InterType) )
        
        t = divider*(TotalAttr*factor/(TotalAttr*factor+1)) #属性加成
        s = initvalue+t
        return s
        
    
    #--------------------END 内政内部接口------------------------  


if __name__ == '__main__':
    uid = 1005
    c = InterMod(uid)
    #print c.updateInterGeneral()
#     print c.getInterEffect(6, 3774)
    print c.updateInterGeneral()
#     print c.getInterEffects({1:100, 5:100})
#    print c.getInter([1001, 1003])
#     print c._calInterGeneral(1,54)

