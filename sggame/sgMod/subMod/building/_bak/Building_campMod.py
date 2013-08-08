#coding:utf8
#author:zhoujingjiang
#date:2013-1-3
#游戏内部接口:兵营，工坊，佣兵处模型

import time
import math

from sgLib.core import Gcore
from sgLib.base import Base

class Building_campMod(Base):
    '''兵营，工坊，佣兵处模型'''
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
    
    def cacAllTrainSoldierNum(self, time_stamp, queues):
        '''计算某一时刻的产兵量'''
        soldier_spawn = {}
        deletes = [] #征完兵的征兵队列
        remains = {} #每个ProcessId对应的剩余未生产数量
        for _, train_queues in queues.iteritems():
            speed = Gcore.getCfg('tb_cfg_building_up',
                                 (6, train_queues[0][1]),
                                 'HourValue')
            speed = int(speed / 3600)
            start_time = train_queues[0][2]
            seconds = time_stamp - start_time
            for train_queue in train_queues:
                seconds_need = int(math.ceil(train_queue[0]/(speed+0.0)))
                if seconds >= seconds_need:
                    seconds -= seconds_need
                    soldier_spawn[train_queue[4]] = \
                        soldier_spawn.setdefault(train_queue[4], 0) + train_queue[0]
                    deletes.append(train_queue[3])
                else:
                    soldier_spawn[train_queue[4]] = \
                        soldier_spawn.setdefault(train_queue[4], 0) + int(seconds * speed)
                    remains[train_queue[3]] = train_queue[0] - int(seconds * speed)
                    break
        return soldier_spawn, remains, deletes

    def getSoldierProcess(self, BuildingId=None):
        '''获取征兵进程'''
        table = 'tb_process_soldier'
        fields = ['ProcessId',
                  'BuildingId',
                  'SoldierType',
                  'SpawnNumRest',
                  'LastChangedTime', 
                  'BuildingLevel']
        where = ' UserId=%s ' % self.uid
        if BuildingId is not None:
            where += ' AND BuildingId=%s ' % BuildingId
        return self.db.out_rows(table, fields, where)

    def getQueue(self, TrainQueues):
        '''制作训练队列'''
        queues = {}
        for unit in sorted(TrainQueues, 
                           key=lambda dic:(dic["BuildingId"], dic["ProcessId"])):
            queues.setdefault(unit["BuildingId"], []).append([unit["SpawnNumRest"],
                                                              unit["BuildingLevel"],
                                                              unit["LastChangedTime"], 
                                                              unit["ProcessId"], 
                                                              unit["SoldierType"]])
        return queues

    def getMaxSoldierNum(self, Buildings):
        '''计算校场的最大存储量，内政有加成'''
        MaxNum = 0
        for Building in Buildings:
            MaxNum += Gcore.getCfg('tb_cfg_building_up', 
                                   (7, Building["BuildingRealLevel"]),
                                   "SaveValue")
        modInter = Gcore.getMod('Inter', self.uid)
        return modInter.getInterEffect(3, MaxNum) #内政加成

    def getSoldiers(self):
        '''从士兵表中查出士兵和器械'''
        return self.db.out_fields('tb_soldier',
                                  ["Soldier1","Soldier2","Soldier3","Soldier4","Soldier5",
                                   "Soldier6","Soldier7","Soldier8","Soldier9","Soldier10",
                                   "Soldier11","Soldier12","Soldier13","Soldier14","Soldier15",
                                   "Soldier16","Soldier17","Soldier18","Soldier101","Soldier102",
                                   "Soldier103","Soldier104","Soldier105"], 
                                  'UserId=%s' % self.uid)
                
    def getSoldierNum(self, TimeStamp):
        '''获取TimeStamp时刻，士兵、器械的数量'''
        soldiers = self.getSoldiers()

        TrainQueues = self.getSoldierProcess()
        queues = self.getQueue(TrainQueues)

        invalid = []
        for building in queues:
            if TimeStamp <= queues[building][0][2]:
                invalid.append(building)
        for k in invalid:
            del queues[k] #将最后计算时间大于当前时间的队列从训练队列中删除。
        if not queues: #空队列直接返回。
            return soldiers

        soldier_spawn, remains, deletes = self.cacAllTrainSoldierNum(TimeStamp, queues)
        #更新士兵表
        for soldier_type, spawn_num in soldier_spawn.iteritems():
            soldiers['Soldier%d'%soldier_type] += spawn_num
        table = 'tb_soldier'
        where = 'UserId=%s' % self.uid
        self.db.update(table, soldiers, where)
        
        table = 'tb_process_soldier'
        #更新征兵记录表
        if deletes:
            sql = 'DELETE FROM %s WHERE UserId=%s' % (table, self.uid)
            sql += ' AND ( ProcessId= ' + ' OR ProcessId = '.join(map(str, deletes)) + ' ) '
            self.db.execute(sql)
            print '删除sql', sql
        if remains:
            sql = '''UPDATE %s SET LastChangedTime=%s, 
                    SpawnNumRest=CASE ProcessId ''' % (table, TimeStamp)
            for remain in remains.iteritems():
                print 'remain', remain
                sql += ' WHEN %s THEN %s ' % remain
            sql += ' ELSE SpawnNumRest END '
            where = ' WHERE UserId=%s AND (ProcessId= ' % (self.uid, )
            where += ' OR ProcessId = '.join(map(str, remains.keys())) + ' ) '
            sql += where
            self.db.execute(sql)
            print '更新sql', sql
        
        if soldier_spawn: #added by zhangguanghui
            modEvent = Gcore.getMod('Event', self.uid)
            modEvent.soldierGet(soldier_spawn)

        return soldiers

    def wrapGetSoldierNum(self, buildings, time_stamp):
        '''兼容以前, 请用getSoldierNum'''
        return self.getSoldierNum(time_stamp)

    def changeSoldierNum(self, param, flag=1, TimeStamp=None):
        '''道具增兵 或 战斗损兵'''
        #flag - 1增兵，其他损兵。
        TimeStamp = TimeStamp if TimeStamp else time.time()
        soldiers = self.getSoldierNum(TimeStamp)
        
        if flag == 1: #增加 
            modBuilding = Gcore.getMod('Building', self.uid)
            Buildings = modBuilding.getBuildingByType(7, TimeStamp=TimeStamp) #校场
            MaxSoldierNum = self.getMaxSoldierNum(Buildings)
            
            NewAdd = sum(param.values()); NowOwn= sum(soldiers.values())
            TotalTrainingNum = 0
            for process in self.getSoldierProcess():
                TotalTrainingNum += process["SpawnNumRest"]

            if NewAdd + NowOwn + TotalTrainingNum > MaxSoldierNum:
                return -1 #增加的士兵数量超过了校场容量上限
            for typ in param:
                soldiers["Soldier%d"%typ] += param[typ]
            return self.db.update('tb_soldier', soldiers, 'UserId=%d'%self.uid)
        else: #减少 - 士兵或器械
            for typ in param:
                soldiers["Soldier%d"%typ] = max(soldiers["Soldier%d"%typ]-param[typ], 0)
            return self.db.update('tb_soldier', soldiers, 'UserId=%d'%self.uid)

    def TouchAllSoldiers(self, TimeStamp=None):
        #士兵
        TimeStamp = time.time() if TimeStamp is None else TimeStamp
        Soldiers = self.getSoldierNum(TimeStamp)    
        
        #训练队列
        TrainQueues = self.getSoldierProcess()
        queues = {}
        seq = 1
        for unit in sorted(TrainQueues, 
                           key=lambda dic:(dic["BuildingId"], dic["ProcessId"])):
            queues.setdefault(unit["BuildingId"],[]).append({'seq':seq, 
                                                             'num':unit["SpawnNumRest"],
                                                             'starttime':unit["LastChangedTime"], 
                                                             'soldiertype':unit["SoldierType"]})  
            seq += 1
        return {'Soldiers':Soldiers, 'TrainQueues':queues, "TimeStamp":TimeStamp}

    def updateSoldierNum(self, SoldierType, Num):
        '''更新tb_soldier中士兵或器械的数量'''
        table = 'tb_soldier'
        setClause = {'Soldier%s'%SoldierType:Num}
        where = 'UserId=%s' % self.uid
        return self.db.update(table, setClause, where)
        
    def updateSoldierProcess(self, Num, SoldierType, BuildingId):
        '''更新征兵数量'''
        table = 'tb_process_soldier'
        where = 'UserId=%s AND BuildingId=%s AND SoldierType=%s' \
                % (self.uid, BuildingId, SoldierType)
        if Num == 0:
            return self.db.execute('DELETE FROM %s WHERE %s' % (table, where))
        return self.db.update(table, {"SpawnNumRest":Num}, where)
    
    def updateProcessById(self, UpdateDic, BuildingId):
        '''按照BuildingId，更新征兵进程。'''
        table = 'tb_process_soldier'
        where = 'BuildingId=%s AND UserId=%s'%(BuildingId, self.uid) 
        return self.db.update(table, UpdateDic, where)
    
    def createSoldierProcess(self, SpawnNumRest, SoldierType, 
                             BuildingId, BuildingLevel, TimeStamp):
        '''创建一条征兵进程记录'''
        table = 'tb_process_soldier'
        valueClause = {"CreateTime":TimeStamp,
                       "LastChangedTime":TimeStamp, 
                       "BuildingLevel":BuildingLevel, 
                       "SpawnNumRest":SpawnNumRest,
                       "SoldierType":SoldierType, 
                       "BuildingId":BuildingId,
                       "UserId":self.uid}
        return self.db.insert(table, valueClause)
    
    def speedupSoldierProcess(self, ProcessId):
        #加速征兵进程
        sql = 'DELETE FROM `tb_process_soldier` WHERE ProcessId=%d' % ProcessId
        return self.db.execute(sql)
    
    def getHireByDate(self, BuildingId, Date):
        '''获取某天的佣兵处雇佣信息'''
        table = 'tb_soldier_hire'
        fields = ['Soldier4', 'Soldier5', 'Soldier9', 'Soldier10', 'Soldier14', 'Soldier15']
        where = 'UserId=%s AND LastChangedDate="%s" AND BuildingId=%s' % (self.uid, 
                                                                          Date, 
                                                                          BuildingId)
        res = self.db.out_fields(table, fields, where)
        return res
    
    def updateSoldierHire(self, Soldiers, BuildingId, Date):
        '''更新士兵雇佣表'''
        table = 'tb_soldier_hire'
        where = 'UserId=%s AND BuildingId=%s' % (self.uid, BuildingId)
        Soldiers['LastChangedDate'] = Date
        res = self.db.update(table, Soldiers, where)
        if not res:
            Soldiers['UserId'] = self.uid
            Soldiers['BuildingId'] = BuildingId
            return self.db.insert(table, Soldiers)
        return True
    
    def isSameCamp(self, SoldierType, flag=False):
        '''是否是同阵营的士兵'''
        #如果不是同一阵营的士兵返回False。否则返回士兵分类：1，士兵；2，器械；3，防御工事。
        UserCamp = self.getUserCamp()
        try:
            SoldierCfg = Gcore.getCfg('tb_cfg_soldier', SoldierType)
            SoldierSide = SoldierCfg["SoldierSide"]
            SoldierClass = SoldierCfg['SoldierClass']
        except Exception:
            return False
        else:
            if flag and SoldierSide == 4:
                return SoldierClass
            return SoldierClass if SoldierSide == 0 or SoldierSide == UserCamp else False
    
    def openSoliders(self, time_stamp=None, reverse=False):
        '''按照顺序返回玩家已开放的兵种'''
        #reverse-False从低到高，True从高到低
        modBuilding = Gcore.getMod('Building', self.uid)
        Buildings = modBuilding.getBuildingByType(6, TimeStamp=time_stamp)
        Buildings = [building for building in Buildings if building['BuildingState'] != 1]
        if not Buildings:
            return []
        max_level = max([building['BuildingRealLevel'] for building in Buildings])
        print 'max_level', max_level
        soldier_details = Gcore.getCfg('tb_cfg_soldier').values()
        soldiers = [soldier_detail for soldier_detail in soldier_details 
                    if soldier_detail['OpenLevel'] <= max_level 
                        and soldier_detail['SoldierClass'] == 1
                        and (soldier_detail['SoldierSide'] == 0 or
                        soldier_detail['SoldierSide'] == self.getUserCamp())]
        soldiers = sorted(soldiers, key=lambda dic:dic['OpenLevel'], reverse=reverse)
        Techs = Gcore.getMod('Book',self.uid).getTechsLevel(1)
        return [{soldier['SoldierType']:Techs.get(soldier['SoldierType'])} for soldier in soldiers]
#end class Building_campMod
