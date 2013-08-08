#coding:utf8
#author:zhoujingjiang
#date:2013-2-7
#comment:武馆内部接口

import time

from sgLib.core import Gcore
from sgLib.base import Base

class Building_groundMod(Base):
    '''武馆模型'''
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
        
    def getGeneralById(self, Generals, GeneralId):
        '''根据提供的GeneralId，从Generals中提取武将信息'''
        for General in Generals:
            if General['GeneralId'] == GeneralId:
                return General
        return None
        
    def touchPractise(self, Generals, TimeStamp=None, UserLevel=None):
        '''更新武将训练表'''
        TimeStamp = TimeStamp if TimeStamp else time.time()
        UserLevel = UserLevel if UserLevel else self.getUserLevel()
        
        table = 'tb_general_practise'
        PractiseQueues = self.db.out_rows(table, '*', 'UserId=%s' % self.uid)

        modGeneral = Gcore.getMod('General', self.uid)
        FinshedQueues = []
        for PractiseQueue in PractiseQueues:
            General = self.getGeneralById(Generals, PractiseQueue["GeneralId"])
            if not General:
                print '检查武将表和训练表的一致性'
                continue

            if PractiseQueue["CompleteTime"] <= TimeStamp: 
                #训练所得经验
                ExpValue = int((PractiseQueue["CompleteTime"] - 
                                PractiseQueue["StartTime"])/60)*PractiseQueue["TrainExp"]
                modGeneral.incGeneralExp(General, ExpValue, UserLevel)
                
                #完成的训练队列
                FinshedQueues.append(str(PractiseQueue["PractiseId"]))
                print '到期PractiseId', PractiseQueue["PractiseId"]
            else:
                print '还差', PractiseQueue["CompleteTime"] -TimeStamp
                ExpValue = int((TimeStamp - PractiseQueue["StartTime"])/600)*10*PractiseQueue["TrainExp"] #读配置
                modGeneral.incGeneralExp(General, ExpValue, UserLevel, False)
            
        if FinshedQueues:
            sql = 'DELETE FROM `%s` WHERE %s' % (table, ' PractiseId= '+' OR PractiseId= '.join(FinshedQueues)) 
            print '删除武将训练', sql       
            self.db.execute(sql)
        return ([PractiseQueue for PractiseQueue in PractiseQueues if PractiseQueue["CompleteTime"] > TimeStamp], 
                Generals)

    def createPractise(self, GeneralId, TrainExp, StartTime, PractiseTime, PayCoin):
        '''插入一条训练记录''' 
        table = 'tb_general_practise'
        
        setClause = {}
        setClause["UserId"] = self.uid
        setClause["GeneralId"] = GeneralId
        setClause["TrainExp"] = TrainExp
        setClause["StartTime"] = StartTime
        setClause["CompleteTime"] = StartTime + PractiseTime
        setClause['TrainPay'] = PayCoin
        
        return self.db.insert(table, setClause)

    def deletePractise(self, PractiseId):
        '''删除一条训练记录'''
        sql = 'DELETE FROM %s WHERE PractiseId=%s AND UserId=%s' % ('tb_general_practise', 
                                                                      PractiseId, self.uid)
        return self.db.execute(sql)
    
    def getRapidRecord(self, date):
        '''获取突飞记录'''
        rapid_record = self.db.out_fields('tb_general_rapid', '*', 
                                          'UserId=%s AND LastChangedDate="%s"'%(self.uid, date))
        return rapid_record
    
    def changeRapidRecord(self, CDValue, LastRapidTime, PractiseCount, LastChangedDate, IsOverFlow):
        '''更新突飞记录'''
        update_dict = {}
        update_dict['CDValue'] = CDValue
        update_dict['LastRapidTime'] = LastRapidTime
        update_dict['PractiseCount'] = PractiseCount
        update_dict['LastChangedDate'] = LastChangedDate
        update_dict['IsOverFlow'] = IsOverFlow

        stat = self.db.update('tb_general_rapid', update_dict, 'UserId=%s'%self.uid)
        if not stat: #如果以前没有突飞记录则插入
            update_dict['UserId'] = self.uid
            return self.db.insert('tb_general_rapid', update_dict)
        return stat
    
    def speedCD(self):
        '''加速突飞记录的CD'''
        return self.db.update('tb_general_rapid', 
                              {'CDValue':0, 'IsOverFlow':0}, 
                              'UserId=%s' % (self.uid, ))
#end class Building_groundMod
