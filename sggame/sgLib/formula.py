# -*- coding:utf-8 -*-
# author:lizr
# date:2013-4-3
# 战斗公式类

from __future__ import division
from sgLib.core import Gcore

M = 1.2 #地形系数
W = 1.2 #攻克系数
class Formula:
    
    HP_mi = 0.8 #生命收益递减幂    e.g.总HP=（初始士兵数量^收益递减幂）*士兵HP
    AT_mi = 0.8 #攻击收益递减幂
    initBastionLife = 50000
    initBastionDefense = 10
    bLifeRatio = 0.25
    bRevengeRatio = 0.6
    failRewardRatio = 0 #失败获得金钱比例 0~1
    kSkillChance = 0.0001 #技能触发概率系数  公式中的φ ： 技能触发概率=A+概率阈值 * φ*智力/(φ*智力+1)
    
    @staticmethod
    def getArmyAttack(**kw):
        '''计算方阵(军队)初始攻击力 未加技能加成
        :(旧)初始攻击力 = 方阵初始士兵数量*兵种攻击*(1+α*武力)*军团科技加成*地形系数
        :初始攻击=((初始士兵数量^收益递减幂) *士兵攻击*（1+兵书效果） +α*武力) *（1+军团科技）*地形系数 ;
        '''
        #print 'getArmyAttack',kw
        A = {1:2, 2:1.5}
        
        
        #间接变量
        generalType = kw['generalType'] #武将类型
        soldierType = kw['soldierType'] #兵种类型
        landForm = kw['landForm'] #地形
        
        #直接变量
        soldierAttack = kw['soldierAttack'] #兵种攻击 (已加成军团科技)
        soldierNum = kw['soldierNum'] #士兵数量
        forceValue = kw['forceValue'] #武将武力
        
        #缺省变量 
        clubTechAdd = kw.get('clubTechAdd',1)  #军团科技加成
        
        job = Gcore.getCfg('tb_cfg_general', generalType, 'Job')
    
        m = M if Gcore.getCfg('tb_cfg_soldier',soldierType,'LandForm')==landForm else 1
        a = A[job]
        if 0:
            print 'soldierAttack',soldierAttack
            print 'clubTechAdd',clubTechAdd
            print 'forceValue',forceValue
            print 'soldierNum',soldierNum
            print 'm',m
            print 'forceValue',forceValue
            print 'a',a
        
        #result = soldierAttack * clubTechAdd * (1+a*forceValue) * soldierNum  * m
        result = (soldierNum**Formula.AT_mi * soldierAttack + a*forceValue) * clubTechAdd * m
        #print '(%s**%s * %s *%s*%s) * %s * %s'% \
        #(soldierNum, Formula.AT_mi, soldierAttack, a, forceValue, clubTechAdd, m)
        return int(result)
        
    @staticmethod
    def getArmyCurAttack(InitAttack,curLife,totalLife):
        '''当前攻击=(lowest+(1-lowest)*当前HP/总HP)*方阵初始攻击'''
        lowest = 0.8
        if totalLife == 0:
            return 0
        else:
            return (lowest+(1-lowest)*curLife/totalLife)*InitAttack
    
    @staticmethod
    def getArmyLife(SoldierLife , SoldierNum):
        '''计算军队生命
        @param SoldierLife: 武将带兵，单个等级兵种的生命
        @param SoldierNum:  武将带兵数量
        '''
        ArmyLife = SoldierLife * (SoldierNum ** Formula.HP_mi)
        return int(ArmyLife)
        
        
    @staticmethod
    def defenseAdd(oriDefense,SpeedValue,generalType):
        '''速度加成防御    
        @param oriDefense: 原始防御
        @param LeaderValue: 武将统帅 -> 武将速度
        :(新)初始防御=士兵防御+β*敏捷
        '''
        B = {1:0.03,2:0.03} #1文将  2武将
        job = Gcore.getCfg('tb_cfg_general', generalType, 'Job')
        b = B.get(job,0.03)
        newDefense = int( oriDefense + SpeedValue*b )
        #print 'oriDefense',oriDefense
        #print 'newDefense',newDefense
        return newDefense
    
    @staticmethod
    def speedAdd(oriSpeed,SpeedValue,generalType):
        '''计算速度 : 
        @param oriSpeed: 兵种速度
        @param SpeedValue: 武将速度
        :(新)士兵速度 * (1+ 速度阈值 * c *敏捷/(c * 敏捷+1）） * （1+兵书效果）
        '''
        C = {1:0.0003,2:0.0003} #1文将  2武将
        kSpeed = 0.5 #速度阈值
        job = Gcore.getCfg('tb_cfg_general', generalType, 'Job')
        c = C.get(job,0.0003)
        #v = int( oriSpeed*(1+SpeedValue*c) )
        v = oriSpeed *(1+ (kSpeed*c*SpeedValue) / (c*SpeedValue+1))
        return int(v)
    
    @staticmethod
    def curSpeed(v,skillaffect):
        '''计算当前移动速度=初始移动速度*(1+技能效果)'''
        return  int( v*(1+skillaffect) )
        
    @staticmethod
    def calSkillChance(SkillId,WitValue):
        '''计算 技能触发概率=A+概率阈值 * φ*智力/(φ*智力+1)
        @param oriSkillChance:公式中的A 
        @param WitValue:智力 
        '''
        q = Formula.kSkillChance
        kq = 0.4   #公式中的概率阈值
        oriSkillChance = Gcore.getCfg('tb_cfg_skill',SkillId,'SkillChance')
    
        return oriSkillChance + (kq * q * WitValue) / (q * WitValue + 1)
        
    @staticmethod
    def calBaseResource(StorageCoin,PredictOut):
        '''计算基础资源
        @param StorageCoin: 库存量
        @param PredictOut: 1小时产量
        P% = 0.04*(1+8*1小时产量/(1小时产量+目标库存量))
        :基础资源=P%*目标库存量+X小时产量
        '''
        X = 4 #预计X小时
        try:
            P = 0.05*(1+8*PredictOut/(PredictOut+StorageCoin))
            BaseResource = int(P*StorageCoin+X*PredictOut)
        except:
            BaseResource = 0
        return BaseResource
        
if __name__=='__main__':
    '''测试'''
    F = Formula
    #print Formula.calBaseResource(53956168, 2160)
    #print F.calBaseResource(1000,100)
    #print F.calSkillChance(0.2,1000)
    #print F.speedAdd(100,1000,1)
    ArmyAttack = F.getArmyAttack(
       generalType = 1,
       soldierType = 1,
       landForm = 1,
       soldierAttack = 2,
       soldierNum = 1000,
       forceValue = 100)
    
    print 'ArmyAttack',ArmyAttack
    
    
