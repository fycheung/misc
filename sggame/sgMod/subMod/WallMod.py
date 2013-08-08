# -*- coding:utf-8 -*-
# author:Lizr
# date:2013-3-7
# 游戏内部接口,城墙模型

from sgLib.core import Gcore
from sgLib.base import Base
import time
from sgLib.formula import Formula

F = Formula
Coord = Gcore.Coord

class WallMod(Base):
    """城墙的模型"""
    def __init__(self, uid):
        '''注释'''
        Base.__init__(self,uid)
        self.uid = uid
        #print self.db #数据库连接类

    def test(self):
        '''测试方法'''
    
        
    def checkWallCoord(self,x,y,xSize=1,ySize=1,dExcept=[],gExcept=[]):
        '''
        :检查防御工事建造坐标是否允许
        @param x:x坐标
        @param y:y坐标
        @param xSize:x尺寸
        @param ySize:y尺寸
        @param dExcept:-list排除的防御工事
        @param gExcept:-list排除的军队防御
        @Author:Zhanggh 2013-4-11
        '''
#        return True#测试期间全部返回True
        dTable = self.tb_wall_defense()
        gTable = 'tb_wall_general'
        
        #判断是否需要排除工事或军队某个id的占用坐标
        if dExcept:
            dExcept = [str(dx) for dx in dExcept]
            dWhere = 'UserId=%s AND WallDefenseId NOT IN (%s)'%(self.uid,str.join(',',dExcept))
        else:
            dWhere = 'UserId=%s'%self.uid
        if gExcept:
            gExcept = [str(gx) for gx in gExcept]
            gWhere = 'UserId=%s AND WallGeneralId NOT IN (%s)'%(self.uid,str.join(',',gExcept))
        else:
            gWhere = 'UserId=%s'%self.uid
        
        #查询工事与军队占用的坐标
        ds = self.db.out_rows(dTable,['x','y','xSize','ySize'],dWhere)
        gs = self.db.out_rows(gTable,['x','y'],gWhere)
        dCoords = [Coord.ExpandCoord(d['x'], d['y'], d['xSize'],d['ySize']) for d in ds]
        gCoords = [Coord.ExpandCoord(g['x'], g['y'],3) for g in gs]
        usedCoords = reduce(lambda f,s:f+s,dCoords)+reduce(lambda f,s:f+s,gCoords)
        #可用坐标
        valCoords = Gcore.getCfg('tb_cfg_map_valid_siege').keys()
        #需要坐标
        needCoords = Coord.ExpandCoord(x, y, xSize, ySize)
        for nc in needCoords:
            if nc in usedCoords or nc not in valCoords:
                return False
        return True
    
        
    def getDefenseNum(self):
        '''
        :获取工事数量
        @return: {工事类型:工事数量}
        '''
        defenseTable = self.tb_wall_defense()
        nums = self.db.out_rows(defenseTable,['SoldierType','COUNT(SoldierType) as Num'],'UserId=%s GROUP BY SoldierType'%self.uid)
#        result = {num['SoldierType']: for num in nums}
        result = {}
        for num in nums:
            result[num['SoldierType']] = num['Num']
        return result
    
    def getWallInfo(self):
        '''
        :获取城墙建筑信息
        '''
        buildingMod = Gcore.getMod('Building',self.uid)
        b = buildingMod.getBuildingByType(19)
        b = b[0] if len(b)>=1 else None 
        return b
    
    def getAllDefenseInfo(self,fields='*',UserId=None):
        '''
        :获取布防界面 所有防御工事
        @param defenseId:工事ID
        '''
        if not UserId:
            UserId = self.uid
        defenseTable = self.tb_wall_defense(UserId)
        rows = self.db.out_rows(defenseTable,fields,'UserId=%s'%UserId)
        data = {}
        if rows:
            for row in rows:
                data[ row['WallDefenseId'] ] = row

        return data
    
    def getDefenseCount(self,UserId=None):
        '''分类统计'''
        if not UserId:
            UserId = self.uid
            
        sql = "SELECT COUNT(*) AS Count,SoldierType FROM %s WHERE UserId=%s GROUP BY SoldierType"%(self.tb_wall_defense(UserId),UserId)
        data = {}
        rows = self.db.fetchall(sql)
        if rows:
            for row in rows:
                data[ row['SoldierType'] ] = row['Count']
        return data
    
    def getDefenseInfo(self,defenseIds,fields=['*']):
        '''
        :获取防御工事信息
        @param defenseIds:防御工事ID int or list
        @author: Lizr
        '''
        tb_defense = self.tb_wall_defense()
        if isinstance(defenseIds,(tuple,list)):
            defenseIds = [str(t) for t in defenseIds]
            where = "WallDefenseId IN ("+str.join(",",defenseIds)+") AND UserId='%s'"%self.uid
            return self.db.out_rows(tb_defense, fields, where)
        else:
            return self.db.out_fields(tb_defense,fields,'WallDefenseId=%s AND UserId=%s'%(defenseIds,self.uid))
            

    def createDefense(self,data):
        '''
        :建造防御工事
        @param data:防御工事信息
        '''
        defenseTable = self.tb_wall_defense()
        return self.db.insert(defenseTable,data)
        
    
    def moveDefense(self,defenseId,x,y,towardStyle):
        '''
        :移动/旋转防御工事
        @param defenseId:
        @param x:
        @param y:
        @param towardStyle:
        '''
        defenseTable = self.tb_wall_defense()
        data={'x':x,
              'y':y,
              'TowardStyle':towardStyle}
        return self.db.update(defenseTable,data,'WallDefenseId=%s'%defenseId)
        
    def deleteDefense(self,defenseId):    
        '''
        :删除移动工事
        @param defenseId:
        '''
        defenseTable = self.tb_wall_defense()
        sql = 'DELETE FROM %s WHERE WallDefenseId=%s'%(defenseTable,defenseId)
        return self.db.execute(sql)
    
    def getDefenseGeneral(self,UserId=None):
        '''获取布防上场的武将'''
        if not UserId:
            UserId = self.uid
        kLeader = Gcore.loadCfg(Gcore.defined.CFG_BATTLE)["kLeaderAddNum"]
        SoldierTechs =  Gcore.getMod('Book',UserId).getTechsLevel(1)
        
        DenfeseGenerals = self.db.out_rows('tb_wall_general', ['GeneralId','x','y'], "UserId=%s"%UserId)
        if not DenfeseGenerals:
            return {}
        dictDG = {}
        for r in DenfeseGenerals:
            dictDG[ r.get('GeneralId') ] = r
    
        GeneralIds = [int(row['GeneralId']) for row in DenfeseGenerals]
        fields = ['GeneralId','GeneralType','GeneralLevel','ForceValue',
                  'WitValue','SpeedValue','LeaderValue','TakeType','TakeTypeDefense']
        
        GeneralInfo = {}
        Grows = Gcore.getMod('General',UserId).getGeneralInfo(GeneralIds,fields)
        for row in Grows:
            if not row['TakeTypeDefense']:
                if Gcore.getCfg('tb_cfg_soldier',row['TakeType'],'SoldierSide')==4:
                    row['TakeTypeDefense'] = 0
                else:
                    row['TakeTypeDefense'] = row['TakeType']
            else:
                if Gcore.getCfg('tb_cfg_soldier',row['TakeTypeDefense'],'SoldierSide')==4:
                    row['TakeTypeDefense'] = 0
                    
            row['Skill'] = Gcore.getCfg('tb_cfg_general',row['GeneralType'],'SkillId')
            SoldierType = row['TakeTypeDefense'] if row['TakeTypeDefense'] else 1
            SoldierLevel = SoldierTechs.get( SoldierType )
            SoldierNum = row['LeaderValue']*kLeader
            
            row['SoldierType'] = SoldierType
            row['SoldierLevel'] = SoldierLevel
            key = (SoldierType,SoldierLevel)
            cfg_soldier = Gcore.getCfg('tb_cfg_soldier_up',key)
            
#            row['Life'] = cfg_soldier['Life']*row['LeaderValue']*kLeader
#            row['Attack'] = cfg_soldier['Attack']*row['LeaderValue']*kLeader
#            row['Denfense'] = cfg_soldier['Defense']
            
            row['Life'] = F.getArmyLife(cfg_soldier['Life'], SoldierNum)
            row['Attack'] = F.getArmyAttack(
                                           generalType = row['GeneralType'],
                                           soldierType = row['SoldierType'],
                                           landForm = 4,
                                           soldierAttack = cfg_soldier['Attack'],
                                           soldierNum = SoldierNum,
                                           forceValue = row['ForceValue'],
                                           )
            row['Denfense'] = F.defenseAdd( cfg_soldier['Defense'],row['SpeedValue'],row['GeneralType']) 
                
            
#            del row['ForceValue']
#            del row['WitValue']
#            del row['SpeedValue']
#            del row['LeaderValue']
            
            del row['TakeType']
            del row['TakeTypeDefense']

            row['x'] = dictDG.get( row['GeneralId'] ).get('x')
            row['y'] = dictDG.get( row['GeneralId'] ).get('y')
           
            GeneralInfo[ row['GeneralId'] ] = row
        
        return GeneralInfo
        
    def getWallGeneralList(self):
        '''获取布防武将列表  参考getWallGeneralList()  
        @call: WallUI
        @author: by Lizr
        '''
        kLeader = Gcore.loadCfg(Gcore.defined.CFG_BATTLE)["kLeaderAddNum"]
        SoldierTechs =  Gcore.getMod('Book',self.uid).getTechsLevel(1)
        
        InListGeneral = self.db.out_list('tb_wall_general','GeneralId',"UserId=%s"%self.uid) #已布防
        
        fields = ['GeneralId','GeneralType','GeneralLevel','ForceValue',
                  'WitValue','SpeedValue','LeaderValue','TakeType','TakeTypeDefense']
        rows = Gcore.getMod('General',self.uid).getMyGenerals(fields)
        #Gcore.printd( rows )
        GeneralList = []
        for row in rows:
            if not row['TakeTypeDefense']:
                row['TakeTypeDefense'] = row['TakeType']

            row['Skill'] = Gcore.getCfg('tb_cfg_general',row['GeneralType'],'SkillId')
            SoldierType = row['TakeTypeDefense']
            SoldierLevel = SoldierTechs.get( SoldierType )
            row['SoldierType'] = SoldierType
            row['SoldierLevel'] = SoldierLevel
            key = (SoldierType,SoldierLevel)
            SoldierNum = row['LeaderValue']*kLeader
            
            cfg_soldier = Gcore.getCfg('tb_cfg_soldier_up',key)
            if cfg_soldier:
                #row['Life'] = cfg_soldier['Life']* row['LeaderValue']*kLeader
                #row['Attack'] = cfg_soldier['Attack']*row['LeaderValue']*kLeader
                #row['Denfense'] = cfg_soldier['Defense']
                
                row['Life'] = F.getArmyLife(cfg_soldier['Life'], SoldierNum)
                row['Attack'] = F.getArmyAttack(
                                               generalType = row['GeneralType'],
                                               soldierType = row['SoldierType'],
                                               landForm = 4,
                                               soldierAttack = cfg_soldier['Attack'],
                                               soldierNum = SoldierNum,
                                               forceValue = row['ForceValue'],
                                               )
                row['Denfense'] = F.defenseAdd( cfg_soldier['Defense'],row['SpeedValue'],row['GeneralType']) 
            else:
                row['Life'] = 0
                row['Attack'] = 0
                row['Denfense'] = 0
                
            row['InWall'] = row['GeneralId'] in InListGeneral #是否在布防中
            
#            del row['ForceValue']
#            del row['WitValue']
#            del row['SpeedValue']
#            del row['LeaderValue']
            
            del row['TakeType']
            del row['TakeTypeDefense']
           
            GeneralList.append(row)
        return GeneralList
        
    def setGeneral(self,GeneralId,x,y):
        where = "GeneralId=%s AND UserId=%s"%(GeneralId,self.uid)
        WallGeneralId = self.db.out_field( 'tb_wall_general', 'WallGeneralId', where )
        if not WallGeneralId:
            data = {
                 'GeneralId':GeneralId,
                 'x':x,
                 'y':y,
                 'UserId':self.uid,
                 }
            result = self.db.insert('tb_wall_general',data)
            return result
        else:
            data = {
                 'x':x,
                 'y':y,
                 }
            result = self.db.update('tb_wall_general',data, where)
            return result
    
    def removeGeneral(self,GeneralId):
        '''在布防上移除武将'''
        sql = "DELETE FROM tb_wall_general WHERE UserId = %s AND GeneralId=%s"%(self.uid,GeneralId)
        return self.db.execute(sql)
    
    def changeTypeGeneral(self,GeneralId,TakeType):
        '''变更武将带兵类型'''
        where = "GeneralId=%s"%GeneralId
        return self.db.update( self.tb_general(), {"TakeTypeDefense":TakeType}, where)
    
    def getWallGeneralNum(self):
        '''已上场武将数量'''
        table = self.tb_general()
        where = 'tb_wall_general.GeneralId = %s.GeneralId AND tb_wall_general.UserId=%s'%(table,self.uid)
        return self.db.out_field('tb_wall_general,%s'%table,'COUNT(*)',where) #防止解散的武将还在布防上

    
    def lastBattleReport(self,pageNum=20):
        '''获取最新战报'''
        where = "UserId=%s ORDER BY BattleReportId DESC LIMIT 0, %s "%(self.uid, pageNum)
        rows = self.db.out_rows('tb_battle_report','*',where)
        rowsReport = []
        hsid,huid = Gcore.getMod('Building_hold',self.uid).getMyHolder()
        print hsid,huid
        for row in rows:
            row['IsHolder'] = 1 if row['FighterServerId']==hsid and row['FighterId']==huid else 0 #是否是我的主人
            row['JcoinLost'] *= -1
            row['GcoinLost'] *= -1
            row['CreateTime'] = time.strftime('%y-%m-%d %H:%M',time.localtime(row['CreateTime'])) #13-06-15 12:11
            del row['UserId']
            rowsReport.append(row)
        return rowsReport
    
    def moveElement(self,p):
        '''批量移动元素'''
        result = True
        if 'DenfenseInfo' in p:
            for row in p['DenfenseInfo']: #e.g. {'WallDefenseId':1,'x':1,'y':1,'xSize':1,'ySize':3}
                WallDefenseId = row['WallDefenseId']
                del row['WallDefenseId']
                row.pop('DefenseType',None)
                result = result and self.db.update(self.tb_wall_defense(), row, 
                               "WallDefenseId=%s AND UserId=%s"%(WallDefenseId,self.uid) )
                
                
        if 'GeneralInfo' in p:
            for row in p['GeneralInfo']: #e.g. {'GeneralId':1,'x':8,'y':14}
                GeneralId = row['GeneralId']
                del row['GeneralId']
                result = result and self.db.update('tb_wall_general', row, 
                               "GeneralId=%s AND UserId=%s"%(GeneralId,self.uid) )
        
        
        return result
    
    def getRepaireCoin(self):
        '''统计查询修复的防御工事费用'''
        sql = "SELECT SUM(MakeCost*(1-LifeRatio)) AS Total FROM %s WHERE LifeRatio>0 AND UserId=%s" \
        %(self.tb_wall_defense(),self.uid)
        row = self.db.fetchone(sql)
        return row['Total']
    
    def repairWallDefense(self):
        '''修理所有防御工事'''
        sql = "UPDATE %s SET LifeRatio=1 WHERE LifeRatio<>1 AND UserId=%s"%(self.tb_wall_defense(),self.uid)
        return self.db.execute(sql)
    
    def clearWallDefense(self):
        '''清理已损坏的防御工事'''
        
        where = "LifeRatio=0 AND UserId=%s"%self.uid
        
        CfgKey = Gcore.defined.CFG_WALL
        DefenseCleanReturn = Gcore.loadCfg(CfgKey).get('DefenseCleanReturn')
        sql = "SELECT SUM(MakeCost*%s) AS CleanReturnTotal FROM %s WHERE %s" \
        %(DefenseCleanReturn,self.tb_wall_defense(),where)
        
        row = self.db.fetchone(sql)
        if row:
            CoinValue = row['CleanReturnTotal']
        else:
            CoinValue = 0
        if CoinValue:
            self.db.delete(self.tb_wall_defense(),where)
        return CoinValue
    
    def getWallBoxReward(self):
        '''获取城墙遗落宝箱的奖励'''
        CfgKey = Gcore.defined.CFG_WALL
        BoxAppearRatio = Gcore.loadCfg(CfgKey).get('BoxAppearRatio')
        from random import randint
        if Gcore.TEST: #开发网100机率获取
            BoxAppearRatio = 100
        if randint(1,100) <= BoxAppearRatio:
            RewardCfgList = Gcore.getCfg('tb_cfg_wall_box').values()
            RewardUnit = Gcore.common.Choice(RewardCfgList,count=1) 
            #e.g. {'GoodsId': 201, 'Ratio': 40, 'GoodsNum': 1, 'RewardId': 5, 'RewardType': 2}
          
            del RewardUnit['RewardId']
            del RewardUnit['Ratio']
            return RewardUnit
        else:
            return {}
        
        
if __name__ == '__main__':
    uid = 1001
    c = WallMod(uid)
#    c.getDefenseCount()
    #Gcore.printd( c.getAllDefenseInfo('*',1008) )
    #print c.getWallGeneralList()
    d =  c.getDefenseGeneral()
    #c.lastBattleReport()
    #Gcore.printd(d)
    #print c.checkWallCoord(38,34,1,3,dExcept=[3])
    #print c.getRepaireCoin()
    #print c.clearWallDefense()
    print c.getWallBoxReward()
    
    