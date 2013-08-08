#coding:utf8
#author:zhoujingjiang
#date:2013-7-22
#comment:兵营，工坊，佣兵处内部模型

import time

from sgLib.core import Gcore
from sgLib.base import Base

class Building_campMod(Base):
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
        self._soldier_storage = 'tb_soldier_storage'

    def updateStorage(self, building_id, storage_num=None, last_changed_time=None, last_cal_time=None):
        '''更新士兵生产表'''
        update_dict = {}
        if storage_num is not None:update_dict['StorageNum'] = storage_num
        if last_changed_time is not None:update_dict['LastChangedTime'] = last_changed_time
        if last_cal_time is not None:update_dict['LastCalTime'] = last_cal_time
        if not update_dict:return True
        return self.db.update(self._soldier_storage, update_dict,
                              'UserId=%s AND BuildingId=%s' % (self.uid, building_id))

    def initRecord(self, building_id, building_type, time_stamp, building_level, complete_time):
        '''向士兵生产表插入一条初始记录'''
        cd_interval = 300 #计算时间间隔

        if complete_time <= time_stamp:
            last_changed_time = time_stamp - (time_stamp - complete_time) % cd_interval
        else:
            last_changed_time = complete_time

        init_data = {
                     'UserId':self.uid,
                     'BuildingId':building_id,
                     'BuildingType':building_type,
                     'StorageNum':Gcore.getCfg('tb_cfg_building_up', 
                                               (building_type, building_level), 
                                               'MakeValue'),
                     'LastChangedTime':last_changed_time,
                     'LastCalTime':time_stamp,
                     'CreateTime':time_stamp
                    }
        self.db.insert(self._soldier_storage, init_data)
        return init_data

    def getSoldierStorage(self, building_info, time_stamp, set_cal_time=None, is_sync=False, add_num=0):
        '''获取新兵数量'''
        #is_sync - 是否将更新写回数据库
        #set_cal_time - 设置兵营的最近征兵时间，如不设置则为time_stamp
        cal_interval = 300 #计算时间间隔
        time_stamp = int(time_stamp)

        building_level = building_info['BuildingRealLevel']
        building_type = building_info['BuildingType']
        building_id = building_info['BuildingId']
        last_opt_type = building_info['LastOptType']
        complete_time = building_info['CompleteTime']

        if last_opt_type == 0 and complete_time > time_stamp:
            print 'complete_time', complete_time
            print 'time_stamp', time_stamp
            return {} #兵营或工坊还未建造完成

        camp_record = self.db.out_fields(self._soldier_storage, '*', 
                                    'UserId=%s AND BuildingId=%s' % (self.uid, building_id))

        if not camp_record: #士兵生产表中没有该建筑的信息，插入一条初始记录
            camp_record = self.initRecord(building_id, building_type, time_stamp, building_level, complete_time)
        if time_stamp <= camp_record['LastCalTime']:return camp_record #本次计算时间太小

        if camp_record['LastCalTime'] < complete_time <= time_stamp and last_opt_type == 1:
            add_num += Gcore.getCfg('tb_cfg_building_up',
                                    (building_type, building_level),
                                    'MakeValue') - \
                        Gcore.getCfg('tb_cfg_building_up',
                                     (building_type, building_level-1),
                                     'MakeValue')

        camp_record['LastCalTime'] = time_stamp
        camp_cfg = Gcore.getCfg('tb_cfg_building_up',
                                (building_type, building_level))
        speed = camp_cfg['HourValue']
        make_value = camp_cfg['MakeValue']

        storage_num = camp_record['StorageNum']
        last_changed_time = camp_record['LastChangedTime']
        if last_changed_time >= time_stamp or last_changed_time + cal_interval > time_stamp:
            print '未到计算时间'
            if add_num : camp_record['StorageNum'] = min(storage_num + add_num, make_value)
            if set_cal_time : camp_record['LastChangedTime'] = set_cal_time
            if add_num or set_cal_time: self.db.update(self._soldier_storage, camp_record,
                                                       'UserId=%s AND BuildingId=%s'%(self.uid, building_id))
            return camp_record

        print '过去了', (time_stamp - last_changed_time) // cal_interval, '个计算时间间隔'
        print '生产速度', speed // 3600, '每秒'
        new_add_num = ((time_stamp - last_changed_time) // cal_interval) * cal_interval * (speed // 3600)
        print '理论生产', new_add_num
        print '已有', storage_num
        print '征兵上限', make_value

        camp_record['StorageNum'] = min(storage_num + new_add_num + add_num, make_value) #新兵数量
        camp_record['LastChangedTime'] = ((time_stamp) - (time_stamp-last_changed_time)%cal_interval) \
                                if not set_cal_time else set_cal_time

        if is_sync or add_num:
            print '将士兵生产信息写回数据库'
            self.db.update(self._soldier_storage, camp_record,
                            'UserId=%s AND BuildingId=%s' % (self.uid, building_id))
        else: print '不将士兵生产信息写回数据库'
        return camp_record
  
    def fullAddSoldier(self, building_id, building_type, building_level, last_changed_time, last_cal_time=None):
        '''将兵营或工坊的新兵数量置满 '''
        return self.db.update(self._soldier_storage,
                              {'StorageNum':Gcore.getCfg('tb_cfg_building_up',
                                                         (building_type, building_level),
                                                         'MakeValue'),
                               'LastCalTime':(time.time() if not last_cal_time else last_cal_time),
                               'LastChangedTime':last_changed_time},
                              'UserId=%s AND BuildingId=%s'%(self.uid, building_id))

    def getSoldiers(self):
        '''获取校场士兵的数量'''
        total_soldiers = self.db.out_fields('tb_soldier',
                                            '*',
                                            'UserId=%s' % self.uid)
        total_soldiers.pop('UserId')
        return total_soldiers
    
    def getSoldierNum(self, *args, **kwargs):
        '''兼容以前，用getSoldiers'''
        return self.getSoldiers()
    
    def wrapGetSoldierNum(self, *args, **kwargs):
        '''兼容以前，用getSoldiers'''
        return self.getSoldiers()
    
    def TouchAllSoldiers(self, time_stamp=None):
        '''计算某时刻各个兵营的新兵信息'''
        time_stamp = time_stamp if time_stamp else time.time()       
        modBuilding = Gcore.getMod('Building', self.uid)
        buildings = modBuilding.getBuildingByType([6, 8], TimeStamp=time_stamp)
        ret_dict = {}
        for building in buildings:
            spawn_detail = self.getSoldierStorage(building, time_stamp, is_sync=True)
            ret_dict[building['BuildingId']] = spawn_detail
        return {'SoldierStorage':ret_dict, 'Soldiers':self.getSoldiers()}

    def getMaxSoldierNum(self, buildings=None, time_stamp=None):
        '''计算校场士兵的最大数量'''
        if not isinstance(buildings, (list, tuple)):
            modBuilding = Gcore.getMod('Building', self.uid)
            buildings = modBuilding.getBuildingByType(7, TimeStamp=time_stamp) #校场
        MaxNum = 0
        for building in buildings:
            if building['BuildingState'] == 1 : continue
            MaxNum += Gcore.getCfg('tb_cfg_building_up', 
                                   (7, building["BuildingRealLevel"]),
                                   "SaveValue")
        modInter = Gcore.getMod('Inter', self.uid)
        return modInter.getInterEffect(3, MaxNum) #内政加成

    def changeSoldierNum(self, param, flag=1, TimeStamp=None, Buildings=None):
        '''道具增兵 或 战斗损兵'''
        #flag - 1增兵，其他损兵。
        TimeStamp = TimeStamp if TimeStamp else time.time()
        soldiers = self.getSoldiers()
        
        if flag == 1: #增加 
            if not isinstance(Buildings, (list, tuple)):
                modBuilding = Gcore.getMod('Building', self.uid)
                Buildings = modBuilding.getBuildingByType(7, TimeStamp=TimeStamp) #校场
            MaxSoldierNum = self.getMaxSoldierNum(Buildings)

            NewAdd = sum(param.values()); NowOwn= sum(soldiers.values())
            if NewAdd + NowOwn > MaxSoldierNum:
                return -1 #增加的士兵数量超过了校场容量上限
            for typ in param:
                soldiers["Soldier%d"%typ] += param[typ]
            return self.db.update('tb_soldier', soldiers, 'UserId=%d'%self.uid)
        else: #减少
            for typ in param:
                soldiers["Soldier%d"%typ] = max(soldiers["Soldier%d"%typ]-param[typ], 0)
            return self.db.update('tb_soldier', soldiers, 'UserId=%d'%self.uid)

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

if __name__ == "__main__":
    o = Building_campMod(44433)
    print o.TouchAllSoldiers()