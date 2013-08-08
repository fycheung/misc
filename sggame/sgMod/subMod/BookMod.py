# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-2-5
# 游戏内部接口,书院(兵种科技和内政科技)

import time
from sgLib.core import Gcore
from sgLib.base import Base


class BookMod(Base):
    """docstring for ClassName模板"""
    def __init__(self, uid):
        '''注释'''
        Base.__init__(self,uid)
        self.uid = uid
        #print self.db #数据库连接类
        
#--------------------------START内部接口---------------------------------------------------- 
    def getTechsLevel(self, TechCategory, TimeStamp=None):
        '''获取玩家的科技等级'''
        #author:zhoujingjiang
        #TechCategory - 1兵种,2内政
        
        TimeStamp = TimeStamp if TimeStamp else time.time()
        TechsLevel = self.db.out_rows('tb_book_tech', 
                        ['TechType', 'TechLevel', 'LastEndTime'], 
                        'UserId=%s AND TechCategory=%s' % (self.uid, TechCategory))           
        
        TechsDic = dict([(tech['TechType'], 
            tech['TechLevel'] if tech['LastEndTime']<TimeStamp else tech['TechLevel']-1) 
            for tech in TechsLevel])
        
        if TechCategory == 1:
            Techs = {}
            SoldierCfg = Gcore.getCfg('tb_cfg_soldier')
        
            MaxSortLevel = {}
            for tech in TechsDic:
                MaxSortLevel[SoldierCfg[tech]['SoldierSort']] = max(TechsDic[tech], 
                            MaxSortLevel.get(SoldierCfg[tech]['SoldierSort'], 0))
            for soldier in SoldierCfg:
                if SoldierCfg[soldier]['SoldierSide'] != 4:
                    Techs[soldier] = TechsDic.get(soldier, 0)
                else:
                    Techs[soldier] = MaxSortLevel.get(SoldierCfg[soldier]['SoldierSort'], 0)
            return Techs

        else:
            TechTypes = [typ for typ, _ in Gcore.getCfg('tb_cfg_tech_inter')]          
            for TechType in TechTypes:
                TechsDic.setdefault(int(TechType), 0)
            return TechsDic

#--------------------------END内部接口----------------------------------------------------
    def getBookInfo(self):
        '''
        :获取书院信息
        '''
        buildingMod = Gcore.getMod('Building',self.uid)
        b = buildingMod.getBuildingByType(12)
        b = b[0] if len(b)>=1 else None 
        return b
    
    def getUpgradingTech(self,buildingId):
        '''
        :查询正在升级中的科技
        @return: 如果有返回科技，没有返回None
        '''
        now = time.time()
        fields = ['TechId','TechCategory','TechType','TechLevel','LastEndTime']
        tech = self.db.out_fields('tb_book_tech',fields,'UserId=%s AND BuildingId=%s AND %s<LastEndTime'%(self.uid,buildingId,now))
        return tech
    
    
    def getTechs(self,techCategory):
        '''
        :获取兵种或内政所有科技信息
        @param techCategory:科技类别
        '''
        fields = ['TechId','TechCategory','TechType','TechLevel']
        return self.db.out_rows('tb_book_tech',fields,'UserId=%s AND TechCategory=%s'%(self.uid,techCategory))
    
    def getTech(self,techCategory,techType):
        '''
        :获取一项科技信息
        @param techCategory: 科技类别
        @param techType: 科技类型
        '''
        now = time.time()
        tech = self.db.out_fields('tb_book_tech',['*'],'UserId=%s AND TechCategory=%s AND TechType=%s'%(self.uid,techCategory,techType))
        if not tech:
            data = {'UserId':self.uid,
                    'TechCategory':techCategory,
                    'TechType':techType,
                    'TechLevel':0,
                    'LastStartTime':now,
                    'LastEndTime':now
                    }
            data['TechId']=self.db.insert('tb_book_tech',data)
            tech = data
        return tech
    
    def getTechMaxLevel(self,techCategory,techType,bLevel):
        '''
        :查询科技可研究最大等级
        @param techCategory:
        @param techType:
        '''
#         category = 'soldier' if techCategory==1 else 'inter'
#         field = 'max(%sTechLevel)'%category
#         where = '%sType=%s AND BookLevelNeed<=%s'%(category,techType,bLevel)
#         return self.db.out_field('tb_cfg_tech_%s'%category,field,where)
        
        if techCategory==1 and techType<200:
            cfgTable = 'tb_cfg_tech_soldier'
            tlv = 'SoldierTechLevel'
            blv = 'BookLevelNeed'
            tt = 'SoldierType'
            
        elif techCategory==1 and techType>=200:
            cfgTable = 'tb_cfg_wall_school'
            tlv = 'DefenseLevel'
            blv = 'WallLevelNeed'
            tt = 'DefenseType'
            
        else:
            cfgTable = 'tb_cfg_tech_inter'
            tlv = 'InterTechLevel'
            blv = 'BookLevelNeed'
            tt = 'InterType'
        return max([t[tlv] for t in Gcore.getCfg(cfgTable).values() if bLevel>=t[blv] and t[tt]==techType])
    
    def updateTech(self,techCategory,techType,data):
        '''
        :更新科技信息
        @param techCategory:科技类别
        @param techType:科技种类
        @param data:更新数据
        '''
        where = 'UserId=%s AND TechCategory=%s AND TechType=%s'%(self.uid,techCategory,techType)
        return self.db.update('tb_book_tech',data,where)
    
#------------------------------------------------------------------------------ 
#书院外部等级
#     def getSoldiersScience(self):
#         '''返回我的兵种科技等级'''
#         #todo 稍后完善
#         result = {}
#         for i in range(1,19):
#             result[i]= self.getTechRealLevel(1,i)
#         return result
#     
#     def getTechRealLevel(self,techCategory,techType):
#         '''
#         :根据类别和科技类型ID查询科技等级
#         @param Category:类型1：兵种，2：内政
#         @param type：科技类型
#         '''
#         level = 0
#         tech = self.db.out_fields('tb_book_tech',['*'],'UserId=%s AND TechCategory=%s AND TechType=%s'%(self.uid,techCategory,techType))
#         if tech is None:
#             return level
#         if time.time()<tech.get('LastEndTime'):
#             level = tech.get('TechLevel')-1
#         else:
#             level = tech.get('TechLevel')
#         return level
#     
    
    
    def test(self):
        '''测试方法'''
#        return self.db.out_rows('tb_book_tech',['*'],'BuildingType=1')
#        return Gcore.getCfg('tb_cfg_tech_inter')
        return self.db.out_field('tb_user','UserId','UserId=9999999999')
    
        

if __name__ == '__main__':
    uid = 43664
    b = BookMod(uid)
    print b.getTechsLevel(1)
#    print b.getBookLevel()
#    print b.test()
#    print b.test().get((90,3))
#     print b.getSoldiersScience()


#     print b.getTechMaxLevel(cat,tt,bt),'sdfas'
#     print max([t[tlv] for t in Gcore.getCfg(cfgTable).values() if bt>=t[blv] and t[techType]==tt])
#    print b.getTechsLevel(1)
#     print b.test()
#     print b.getTech(1,101)