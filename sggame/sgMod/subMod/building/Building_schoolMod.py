#coding:utf8
#author:zhoujingjiang
#date:2013-2-25
#游戏内部接口:校场

from sgLib.base import Base

class Building_schoolMod(Base):
    ''' 校场模型 '''
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
    
    def exchangePos(self, GeneralId1, PosId1, GeneralId2, PosId2):
        '''两个武将互换阵上位置'''
        sql = '''
              UPDATE %s SET PosId = CASE GeneralId WHEN "%s" THEN "%s"
                                                   WHEN "%s" THEN "%s" END
              WHERE UserId=%s AND (GeneralId=%s OR GeneralId=%s)
              ''' % (self.tb_general(), GeneralId1, PosId2, GeneralId2, 
                     PosId1, self.uid, GeneralId1, GeneralId2)
        return self.db.execute(sql)
    
    def movePos(self, GeneralId, PosId):
        '''移动武将阵上位置'''
        return self.db.update(self.tb_general(), {"PosId":PosId}, 'UserId="%s" AND GeneralId="%s"' % (self.uid, GeneralId))
    
    def insteadPos(self, GeneralId1, GeneralId2, PosId):
        '''替换阵上武将:GeneralId1是上阵的武将，GeneralId2是被替换的武将'''
        sql = '''
              UPDATE %s SET PosId = CASE GeneralId WHEN "%s" THEN "%s" 
                                                           WHEN "%s" THEN "%s" END, 
                            GeneralState = CASE GeneralId WHEN "%s" THEN "%s"
                                                          WHEN "%s" THEN "%s" END
                        WHERE UserId="%s" AND (GeneralId=%s OR GeneralId=%s)
               ''' % (self.tb_general(), GeneralId1, PosId, GeneralId2, 0, GeneralId1, 1, GeneralId2, 2, self.uid, GeneralId1, GeneralId2)
        return self.db.execute(sql)
    
    def addPos(self, GeneralId, PosId):
        '''向阵上增加武将'''
        return self.db.update(self.tb_general(), {"PosId":PosId, "GeneralState":1}, "UserId='%s' AND GeneralId='%s'" % (self.uid, GeneralId))

    def deletePos(self, GeneralId):
        '''将武将从阵上移除'''
        return self.db.update(self.tb_general(), {"GeneralState":2, "PosId":0, "TakeNum":0}, 'UserId="%s" AND GeneralId="%s"' % (self.uid, GeneralId))
#end class Building_schoolMod
