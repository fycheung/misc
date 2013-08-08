#coding:utf8
#author:zhoujingjiang
#date:2013-1-30
#游戏内部接口:点将台

import time

from sgLib.core import Gcore
from sgLib.base import Base

class Building_trainMod(Base):
    '''点将台模型'''
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
        #武将培养表表名
        self.train_table = 'tb_general_train'

    def getMaxTrainNum(self, time_stamp, Buildings=None):
        '''获取点将台的最大培养次数'''
        if not isinstance(Buildings, (list, tuple)):
            modBuilding = Gcore.getMod('Building', self.uid)
            Buildings = modBuilding.getBuildingByType(18, TimeStamp=time_stamp)
        max_num = sum([Gcore.getCfg('tb_cfg_building_up',
                                    (18, Building['BuildingRealLevel']), 
                                    'MakeValue') 
                       for Building in Buildings 
                       if Building['BuildingState'] != 1])
        return max_num
    
    def initTrainInfo(self, TimeStamp, init=0, Buildings=None):
        '''向武将培养表中插入初始记录'''
        max_num = self.getMaxTrainNum(TimeStamp, Buildings)
        train_info = {
                      'TotalTrainNum':max_num + init,
                      'LastCalTime':TimeStamp,
                      'LastChangedTime':TimeStamp,
                      'CreateTime':TimeStamp,
                      'UserId':self.uid
                     }
        self.db.insert(self.train_table, train_info)
        return train_info

    def normalAddTrainNum(self, num=0, TimeStamp=None, Buildings=None, flag=True, **randoms):
        '''普通增加培养次数：比如定时赠送，定时恢复'''
        # 培养次数不能超过最大培养次数，超出部分丢弃
        # num - 增加的次数
        # + num = 0，获取当前的培养次数
        # + num < 0，减少当前的培养次数
        # + 如果randoms是非空字典，则表示普通培养：
        # + + num应等于-1。
        # randoms是空 或 GeneralId, RandomForce, RandomWit,
        # + RandomSpeed, RandomLeader都是randoms的key
        # flag-是否将当前的培养次数更新到数据库
        print 'normalAddTrainNum', 'num=%s'%num

        TimeStamp = TimeStamp if TimeStamp else time.time()
        if not isinstance(Buildings, (list, tuple)):
            modBuilding = Gcore.getMod('Building', self.uid)
            Buildings = modBuilding.getBuildingByType(18, TimeStamp=TimeStamp)
        
        #1，查出培养次数
        train_info = self.db.out_fields(self.train_table,
                                        ['TotalTrainNum', 'LastChangedTime', 'LastCalTime'],
                                        'UserId=%s' % self.uid)
        if not train_info: #没有该用户的培养信息
            train_info = self.initTrainInfo(TimeStamp, Buildings=Buildings)
        if randoms:
            train_info.update(randoms)
            train_info['IsValid'] = 1

        for building in Buildings:
            if train_info['LastCalTime'] < building['CompleteTime'] <= TimeStamp:
                if building['LastOptType'] == 2:
                    continue
                elif building['LastOptType'] == 1:
                    num += Gcore.getCfg('tb_cfg_building_up',
                        (18, building['BuildingRealLevel']), 'MakeValue') - \
                        Gcore.getCfg('tb_cfg_building_up',
                        (18, building['BuildingRealLevel'] - 1), 'MakeValue')
                elif building['LastOptType'] == 0:
                    num += Gcore.getCfg('tb_cfg_building_up',
                                        (18, 1), 
                                        'MakeValue')
                else:pass

        max_num = self.getMaxTrainNum(TimeStamp, Buildings)
        #2，自动恢复的次数
        cd = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_TRAIN)["cd"]
        seconds_past = TimeStamp - train_info['LastChangedTime']
        new_add_cnt = int(seconds_past / cd)
        
        if train_info['TotalTrainNum'] >= max_num and randoms:
            train_info['TotalTrainNum'] += num
        elif train_info['TotalTrainNum'] >= max_num:pass
        else:            
            train_info['TotalTrainNum'] = min(
                            min(train_info['TotalTrainNum'] + new_add_cnt,
                            max_num) + num, 
                            max_num)
        if train_info['TotalTrainNum'] < 0:
            return -1 #次数不足
        
        train_info['LastChangedTime'] = TimeStamp - seconds_past % cd
        train_info['LastCalTime'] = TimeStamp
        #3，将更新写回数据库
        if flag:
            self.db.update(self.train_table, 
                           train_info,
                           'UserId=%s' % (self.uid, ))
            return train_info['TotalTrainNum'], max_num
        return train_info

    def superAddTrainNum(self, num, TimeStamp=None):
        '''超级增加培养次数：比如使用道具'''
        #num-增加的次数，培养次数可超过最大培养次数
        assert num > 0, 'num应该大于0'
        TimeStamp = TimeStamp if TimeStamp else time.time()

        train_info = self.normalAddTrainNum(0, TimeStamp, flag=False)
        train_info['TotalTrainNum'] += num
        
        return self.db.update('tb_general_train',
                              train_info,
                              'UserId=%s' % self.uid)
    
    def goldenTrain(self, general_id, rand_force, rand_wit, rand_speed, rand_leader):
        '''黄金培养'''
        print '黄金培养'
        sql = '''UPDATE %s SET IsValid=1, GeneralId=%s, 
                    RandomForce=%s, RandomWit=%s, 
                    RandomSpeed=%s, RandomLeader=%s
                    WHERE UserId=%s''' % (self.train_table, 
                                          general_id,
                                          rand_force,
                                          rand_wit,
                                          rand_speed,
                                          rand_leader,
                                          self.uid)
        return self.db.execute(sql)
    
    
    def fullAddTrainNum(self, Buildings=None):
        '''将培养次数恢复到最大'''
        max_num = self.getMaxTrainNum(time.time(), Buildings)
        sql = """UPDATE %s SET TotalTrainNum=
                IF(TotalTrainNum<%d, %d, TotalTrainNum) 
                WHERE UserId=%s""" % (self.train_table, max_num, 
                                      max_num, self.uid)
        return self.db.execute(sql)

    def saveTrainGeneral(self, general_id, force, wit, speed, leader):
        '''保存培养'''
        sql = '''UPDATE %s SET ForceValue=ForceValue+%d,
                                 WitValue=WitValue+%d,
                                 SpeedValue=SpeedValue+%d,
                                 LeaderValue=LeaderValue+%d,
                                 TrainForceValue=TrainForceValue+%d,
                                 TrainWitValue=TrainWitValue+%d,
                                 TrainSpeedValue=TrainSpeedValue+%d,
                                 TrainLeaderValue=TrainLeaderValue+%d
                             WHERE UserId=%s AND GeneralId=%s''' \
                                 % (self.tb_general(), force, wit, speed, leader,
                                    force, wit, speed, leader, self.uid, general_id)
        flag = self.db.execute(sql)
        if flag:
            Gcore.getMod('Event',self.uid).generalChangeAttr(force,speed,wit,leader)#任务事件
        return flag

    def getTrainRandoms(self, GeneralId):
        '''获取武将培养的随机值'''
        return self.db.out_fields(self.train_table, 
                                  ['RandomForce', 'RandomWit', 
                                   'RandomSpeed', 'RandomLeader'], 
                                  '''UserId=%s AND IsValid=%s AND 
                                  GeneralId=%s''' % (self.uid, 1, GeneralId))
    def cancTrainRandoms(self):
        '''将武将培养的随机值设置为无效'''
        return self.db.update(self.train_table, 
                              {"IsValid":0, 
                               'GeneralId':0,
                               'RandomForce':0,
                               'RandomSpeed':0,
                               'RandomWit':0,
                               'RandomLeader':0,}, 
                              'UserId=%s' % self.uid)
#end class Building_trainMod
