# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-3-19
# 模块说明:将军府

import time
from sgLib.core import Gcore
from sgLib.base import Base

class Building_homeMod(Base):
    '''将军府模型'''
    def __init__(self,uid):
        Base.__init__(self,uid)
        self.uid = uid
    
    def getInters(self):
        '''获取内政影响加成'''
        result = {}
        now = time.time()
        inters = self.db.out_fields('tb_inter','*','UserId=%s'%self.uid)
        for i in xrange(1,11):
            inter = {}
            inter['Vip'] = float(inters.get('InterVip%s'%i))
            inter['General'] = float(inters.get('InterGeneral%s'%i))
            inter['Tech'] = float(inters['InterTech%s'%i] if now<inters['Inter%sUpTime'%i] else inters['InterTech%sUp'%i])
            inter['Total'] = inter['Vip']+inter['Tech']+inter['General']
            result[str(i)] = inter
        return result
    
    def getAchievements(self):
        '''
        :获取我的成就
        '''
        result = {}
        fields = ['AchieveType','Finished','NextAchieveId','CurrentAchieve']
        acs = self.db.out_rows('tb_achieve',fields,'UserId=%s'%self.uid)
        achCfgs = Gcore.getCfg('tb_cfg_achieve')
        types = achCfgs.keys()
        
        #查找成就记录中还没有的成就
        for ac in acs:
            acType = ac.get('AchieveType')
            if acType in types:
                types.remove(acType)
            
        #插入还没有初始化的成就数据
        if types: 
            insertRows = []
            for t in types:
#                 firstAchieve = min(achCfgs[t].keys())
                data = {'AchieveType':t,
                        'UserId':self.uid,
                        'NextAchieveId':1}
                insertRows.append(data)
                data['CurrentAchieve'] = 0
                data['Finished'] = 0
                result[t] = data
            self.db.insertmany('tb_achieve',insertRows)
        
        #生成以成就类型为key的字典
        for ac in acs:
            result[ac['AchieveType']] = ac
        return result
    
        
    
    def achieveTrigger(self,optId,data={'ValType':0,'Val':0}):
        aCfgs = Gcore.getCfg('tb_cfg_achieve')
        activeAction = self._getAchieveCache(optId)
        #查询与OptId对应的成就类型
        aData = {}
        ats = []
        for k in aCfgs.keys():
            optIds = aCfgs[k][1]['OptId'].strip().split(',')
            if (str(optId) in optIds) and (k in activeAction):
                ats.append(k)

        for at in ats:
            
            achieve = self.getAchieveInfo(at)
            aCfg = aCfgs.get(at)
            curAchieve = achieve.get('CurrentAchieve')
            maxAchieve = aCfg[max(aCfg.keys())]['AchieveRequire']
            #成就没完成
            if achieve.get('Finished')==0 and curAchieve<maxAchieve:
                updateVal = self.checkUpdateValue(at,data,curAchieve)
                if updateVal:
                    data = {'CurrentAchieve':updateVal,'NextAchieveId':achieve.get('NextAchieveId')}
                    aData[at] = data
        
        #更新任务
        if aData:
            self.updateAchieve(aData)
    
    
    
    
#------------------------------------------------------------------------------ 
#以下仅供UI和本模块调用

    def _getAchieveCache(self,action=''):
        '''获取成就缓存'''
        activeAchieve = Gcore.getUserData(self.uid, 'ActiveAchieve')#缓存活跃成就
        if (activeAchieve is None) or (not isinstance(activeAchieve,list or tuple)):
            myLog = Gcore.getLogger('zhanggh','achieve')
            myLog.error("成就缓存有异常，UserId:%s,动作:%s,用户缓存内容："%(self.uid,action))
            myLog.error( Gcore.StorageUser.get(self.uid))
            
            activeAchieve = self.getAchievements()
            activeAchieve = [k for k in activeAchieve if activeAchieve[k]['Finished']==0]
            Gcore.setUserData(self.uid,{'ActiveAchieve':activeAchieve})
        return activeAchieve
            
    
    def checkUpdateValue(self,at,data={'ValType':0,'Val':0},curAchieve=0):
        '''
        :处理成就更新的值
        @param at:成就类型
        @param data:成就数据
        @param curAchieve:当前成就值
        @attention: 不对成就类型作特殊处理都会直接Val+curAchieve
        '''
        valType = data.get('ValType',0)
        val = data.get('Val',0)
        result = 0
        now = time.time()
        if at==1:#升级将军府
            result = self.getHomeLevel()
        
        elif at==2:#收集军资或铜钱
            if valType==2:
                result=val+curAchieve
        elif at==3:#收集铜钱
            if valType==3:
                result=val+curAchieve
                
        elif at==5:#pve战役获得星
            if val>curAchieve:
                result = val
                
        elif at==7:#招募名将
            gt = Gcore.getCfg('tb_cfg_general',valType,'GeneralSort')
            if gt==1:
                result=val+curAchieve
                
        elif at==6:#兵种科技级数总和
            field='SUM(IF(LastEndTime<=%s,TechLevel,TechLevel-1))'%now
            where='UserId=%s AND TechCategory=1 AND (TechType Between 1 AND 99)'%self.uid
            result = self.db.out_field('tb_book_tech',field,where)

        elif at==8:#器械科技级数总和
            field='SUM(IF(LastEndTime<=%s,TechLevel,TechLevel-1))'%now
            where='UserId=%s AND TechCategory=1 AND (TechType Between 100 AND 199)'%self.uid
            result = self.db.out_field('tb_book_tech',field,where)
    
            
        elif at==9:#内政科技级数总和
            field='SUM(IF(LastEndTime<=%s,TechLevel,TechLevel-1))'%now
            where='UserId=%s AND TechCategory=2'%self.uid
            result = self.db.out_field('tb_book_tech',field,where)
            
        elif at==10:#雇佣兵数量
            sSide = Gcore.getCfg('tb_cfg_soldier',valType,'SoldierSide')
            if sSide==4:
                result=val+curAchieve
        
        elif at==16:#藩国数量
            result = Gcore.getMod('Building_hold',self.uid).getHoldNum()
            
        elif at==21:#攻城战胜利次数
            if data.get('BattleType')==2 and data.get('Result',{}).get('Result')==1:
                result = curAchieve+1
            
        elif at==23:#主城建筑数量
            tb_b = self.tb_building()
            result = self.db.out_field(tb_b,'Count(1)','UserId=%s AND BuildingType<100 AND (BuildingLevel>1 or CompleteTime<=%s)'%(self.uid,now))
        
        elif at==19:#士兵获得
            if valType<100:
                result = curAchieve+val
                    
        elif at==25:#器械数量
            if 100<valType<200:
                result = curAchieve+val
        
        
        #@todo: 这里添加更多处理
        else:#默认处理，简单相加
            result=val+curAchieve
        
        #成就值没有变化不更新
        if result and result>curAchieve:
            return result
        else:
            return 0
    
    def getAchieveInfo(self,at,fields=['*']):
        '''查询成就记录'''
        achieve = self.db.out_fields('tb_achieve',fields,'UserId=%s AND AchieveType=%s'%(self.uid,at))
        #没有成就先初始化成就数据
        if not achieve:
            if at in Gcore.getCfg('tb_cfg_achieve').keys():
                achieve = {'AchieveType':at,
                        'UserId':self.uid,
                        'NextAchieveId':1}
                self.db.insert('tb_achieve',achieve)
                achieve = self.db.out_fields('tb_achieve',fields,'UserId=%s AND AchieveType=%s'%(self.uid,at))
            else:
                achieve = False


        return achieve
    
    
    def updateAchieve(self,aData):
        '''更新成就，（更新相应缓存）'''
        aCfgs = Gcore.getCfg('tb_cfg_achieve')
        activeAction = self._getAchieveCache('updateAchieve')
#         
#         print 'Building_homeMod更新成就',aData
        
        pusAID = []
        updateNum = 0
        
        for aType in aData:
            data = aData[aType]
            curAchieve = data.get('CurrentAchieve')
            nextAchieveId = data.get('NextAchieveId')
            finished = data.get('Finished')
            overMax = 0
            
            #判断成就是否达成
            if curAchieve and nextAchieveId:
                aCfg = aCfgs[aType]
                nextAchieve = aCfg[nextAchieveId]['AchieveRequire']#下一成就值
                if curAchieve>=nextAchieve:
                    pusAID.append(aType)
                    
                    #成就记录不能超出最成就值
                    maxAchieve = aCfg[max(aCfg.keys())]['AchieveRequire']
                    if curAchieve>=maxAchieve:
                        overMax = 1
                        data['CurrentAchieve'] = maxAchieve
            
            #更新缓存
            if (aType in activeAction) and (overMax or finished):
                activeAction.remove(aType)
                
            flag = self.db.update('tb_achieve',data,'UserId=%s AND AchieveType=%s'%(self.uid,aType))
            if flag:
                updateNum += 1
                
        #更新缓存       
        Gcore.setUserData(self.uid, {'ActiveAchieve':activeAction})
           
        #成就达成推送
        if pusAID:
            print '成就达成',pusAID
            #暂不推送
#             Gcore.push(103,self.uid,{'ACT':pusAID})
            
        return updateNum
    
    def updateAchieveByWhere(self,data,where):
        '''
        :更新任务（不更新缓存）
        @param data:更新数据
        @param where:条件
        '''
        return self.db.update('tb_achieve',data,where)
    
    def updateAllAchieves(self):
        '''更新所有成就'''
        tb_achieve = 'tb_achieve'
        fields = ['AchieveType','CurrentAchieve','NextAchieveId']
        where = 'UserId=%s AND Finished=0'%self.uid
        achieves = self.db.out_rows(tb_achieve,fields,where)
        updateAchieves = {}
        for a in achieves:
            aId = a.get('AchieveType')
            curAchieve = a.get('CurrentAchieve')
            nextAchieve = a.get('NextAchieveId')
            updateVal = self.checkUpdateValue(aId,curAchieve=curAchieve)
            if updateVal:
                updateAchieves[aId] = {'CurrentAchieve':updateVal,'NextAchieveId':nextAchieve}
        
        if updateAchieves:
            self.updateAchieve(updateAchieves)

            
    
def _test():
    """注释"""
    uid = 44123
    b = Building_homeMod(uid)
#     Gcore.printd( b.getInters())
#     print b.getAchievements()
#     d = Gcore.getCfg('tb_cfg_achieve')
#    d = b.getNextAchieve(11,900)
#     d = b.achieveTriggerX()
#     print b.checkUpdateValue(1)
#     print b.achieveTrigger(15031,{'ValType':10,'Val':10})
#     d = Gcore.getCfg('tb_cfg_general',valType,'GeneralSort')
#     b.updateAllAchieves()
    print b._getAchieveCache()
    
if __name__ == '__main__':
    _test()