# -*- coding:utf-8 -*-
# author:Yew
# date:2013-3-28
# 战斗结束算法

from __future__ import division
import random


class FightOver(object):
    def __init__(self):
        self.param_def=0.003#防御-免伤计算系数()
        self.param_b=0.05#防御工事加成系数
        self.param_m=0.05#地形加成系数
        self.param_s_w=1#技能加成系数
        self.param_weak=0.15#兵种克制系数
        self.param_w_b=0.5#防御工事权重
        self.param_w_s=0.5#敌方技能平滑
        self.param_w_r=0.25#移&速权重
        self.param_e_dd=0.9#期望免伤
        self.param_e_u=10#期望效用

            
    def getAve(self,p=[]):
        '''计算均值'''
        if not p:
            return 0
        sum_date=sum(p)
        count=len(p)
        return sum_date/count

#    def getM(self,map_type,map_=[]):
#        '''获取地型加成'''
#        M_date=0.0
#        for eachMap in map_:
#            if eachMap==map_type:
#                M_date+=self.param_m
#        return M_date

    def getS(self,N,pro_=[]):
        '''获取技能加成系数'''
        S_date=0.0
        if N==0:
            return 0
        for eachPro in pro_:
            S_date+=eachPro*self.param_s_w
        return S_date/N

    def getW(self,N1,N2,target_weak_=[],type_=[]):
        '''获取兵型克制系数'''
        W_date=0.0
        for eachTW in target_weak_:
            for eachType in type_:
                if eachTW==eachType:
                    W_date+=self.param_weak
        return W_date/(N1*N2)

    def judgment(self,param={},testOutput=False):
        print 'FightOver > ',param
        target_type=param['target_type']#敌方类型  0:NPC 1:玩家
        N1=param['N1']#己方方阵当前数量
        N2=param['N2']#对方方阵当前数量
        TN1=param['TN1']#己方方阵种类数
        #TN2=param['TN2']#敌方方阵种类数
        b_n_2=param['b_n_2']#敌方防御工事数量
        b_t_n_2=param['b_t_n_2']#敌方防御工事种类
        #map_type=param['map_type']#地图地形
        time=param['time']#当前消耗时间
        atk_1=param['atk_1']#己方方阵当前攻击力
        atk_2=param['atk_2']#敌方方阵当前攻击力
        def_1=param['def_1']#己方方阵当前防御力
        def_2=param['def_2']#对方方阵当前防御力
        hp_1=param['hp_1']#己方方阵当前生命值
        hp_2=param['hp_2']#对方方阵当前生命值
        pro_1=param['pro_1']#己方方阵技能释放概率
        pro_2=param['pro_2']#敌方方阵技能释放概率
        rng_1=param['rng_1']#己方方阵当前射程
        rng_2=param['rng_2']#对方方阵当前射程
        spd_1=param['spd_1']#己方方阵当前移动速度
        spd_2=param['spd_2']#对方方阵当前移动速度
        type_1=param['type_1']#己方方阵兵种
        type_2=param['type_2']#敌方方阵兵种
        weak_target_1=param['weak_target_1']#己方方阵克制兵种
        weak_target_2=param['weak_target_2']#敌方方阵克制兵种
        #map_1=param['map_1']#己方方阵适应地形
        #map_2=param['map_2']#敌方方阵适应地形
        P=param['P']#进攻进度
        base_hp_2=param['base_hp_2']#敌方基地当前生命

        
        try:
            
            
            if N2!=0:
                atk_sum_1=sum(atk_1)
                hp_sum_1=sum(hp_1)
                atk_sum_2=sum(atk_2)
                hp_sum_2=min(sum(hp_2),base_hp_2*(2-P))
                def_ave_1=self.getAve(def_1)
                rng_ave_1=self.getAve(rng_1)
                spd_ave_1=self.getAve(spd_1)
                def_ave_2=self.getAve(def_2)
                rng_ave_2=self.getAve(rng_2)
                spd_ave_2=self.getAve(spd_2)
                dd1=1-def_ave_1*self.param_def/(1+def_ave_1*self.param_def)
                dd2=1-def_ave_2*self.param_def/(1+def_ave_2*self.param_def)#敌方减伤
                D=(1+(b_n_2+(b_t_n_2-(b_t_n_2*TN1)**0.5)/TN1)*self.param_b)**self.param_w_b
                #M1=self.getM(map_type,map_1)
                #M2=self.getM(map_type,map_2)
                
                R=((1+(rng_ave_1-rng_ave_2)/rng_ave_2)*(1+\
                (spd_ave_1-spd_ave_2)/spd_ave_2))**self.param_w_r
                
                
                S1=self.getS(N1,pro_1)
                if target_type==1:
                    S2=self.getS(N2,pro_2)
                else:
                    S2=(1+S1)**self.param_w_s-1
                

                W1=self.getW(N1,N2,weak_target_1,type_2)
                W2=self.getW(N1,N2,weak_target_2,type_1)
                
                rnd=random.uniform(-0.05,0.05)
                

                T=hp_sum_2*D/atk_sum_1/dd2/(1+S1)/(1+W1)/R
                
                
                
                t_c=(180-time)*0.8
                
                

                if T>t_c:
                    L1=t_c*atk_sum_2*D*(1+S2)*(1+W2)*dd1/hp_sum_1+rnd
                else:
                    L1=T*atk_sum_2*D*(1+S2)*(1+W2)*dd1/hp_sum_1+rnd
                
                

                if L1>1:
                    L1=1
                if L1<0:
                    L1=0
                U=R*(1+S1)*(1+W1)*atk_sum_1*dd2*(hp_sum_1/atk_sum_2/D\
                /(1+S2)/(1+W2)/dd1)/hp_sum_2+rnd
                L2=(L1-rnd)*(U-rnd)-rnd
                if L2>1:
                    L2=1
                if L2<0:
                    L2=0
                

                
                REST_1=round(1-L1,2)
                
                

                FP=round(P+L2*(1-time/180),2) if L2<1 else 1
                
                
                
                if FP>1:
                    FP=1
                    
                if testOutput:    
                    print 'R:',R
                    print 'S1:',S2
                    print 'S2:',S2
                    print 'W1:',W1
                    print 'W2:',W2
                    print 'D:',D
                    print 'rnds:',rnd
                    print 'T:',T
                    print 't_c:',t_c    
                    print 'L1:',L1
                    print 'U:',U
                    print 'L2:',L2  
                    print 'REST_1:',REST_1
                    print 'FP:',FP
            else:
                atk_sum_1=sum(atk_1)
                dd2=self.param_e_dd
                D=(1+(b_n_2+(b_t_n_2-(b_t_n_2*TN1)**0.5)/TN1)*self.param_b)**self.param_w_b
                #M1=self.getM(map_type,map_1)
                rnd=random.uniform(-0.05,0.05)
                
                T=base_hp_2*D/atk_sum_1/dd2/1
                
                t_c=(180-time)*0.8
                
                L1=(D-1)+rnd
                if L1>1:
                    L1=1
                if L1<0:
                    L1=0
                
                U=self.param_e_u
                
                REST_1=round(1-L1,2)

                FP=1 if T<(180-time) else round(P+(1-L1)*(1-time/180),2)
                if FP>1:
                    FP=1
                    
                if testOutput:    
                    print 'rnds:',rnd
                    print 'T:',T
                    print 'D:',D
                    print 't_c:',t_c    
                    print 'L1:',L1
                    print 'U:',U
                    print 'REST_1:',REST_1
                    print 'FP:',FP
                    
            if target_type==1:
                if P>0.5 or base_hp_2==0:
                    return{'result':1,'REST_1':1,'FP':P}
                if FP>0.5:
                    return{'result':1,'REST_1':REST_1,'FP':FP}
                if FP<=0.5:
                    return{'result':0,'REST_1':REST_1,'FP':FP}
            if target_type==0:
                if U<1 or T>t_c:
                #己方全灭 或者 时间结束，未能消灭敌方
                    return {'result':0,'REST_1':REST_1,'FP':FP}
                if T<t_c and U>=1:
                #敌方全灭
                    return {'result':1,'REST_1':REST_1,'FP':FP}
        except ZeroDivisionError:
            raise
            return False
            

def _test():
    '''测试方法'''
    p= {'b_t_n_2': 0, 'P': 0, 'b_n_2': 0, 'atk_2': [10031.9, 10037.7], 'atk_1': [10221.85, 10224.75, 10102.95, 20469.8, 20481.4], 'def_1': [10, 10, 10, 15, 15], 'def_2': [10, 10], 'type_2': [1, 3], 'type_1': [2, 1, 4, 1, 1], 'N1': 5, 'N2': 2, 'hp_1': [10000, 10000, 10000, 15000, 15000], 'rng_2': [75, 75], 'rng_1': [115, 75, 75, 75, 75], 'hp_2': [10000, 10000], 'TN1': 1, 'TN2': 1, 'weak_target_1': [1, 3, 0, 3, 3], 'weak_target_2': [3, 2], 'target_type': 0, 'base_hp_2': 15200.0, 'spd_2': [50, 80], 'spd_1': [38, 50, 65, 38, 38], 'time': 5.125, 'pro_1': [], 'pro_2': []}

    f=FightOver()
    re=f.judgment(p,True)
    print re
if __name__=='__main__':
    _test()
        
    
