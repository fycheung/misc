#coding:utf8
#author:zhoujingjiang
#date:2013-2-25
#comment:校场外部接口

from sgLib.core import Gcore, inspector

class Building_schoolUI(object):
    '''校场功能外部接口'''
    def __init__(self, uid):
        self.mod = Gcore.getMod('Building_school', uid)
        self.uid = uid
    
    @inspector(15100)
    def GetSchoolInfo(self, param = {}):
        '''校场：获取信息页面'''
        optId = 15100
        
        TimeStamp = param['ClientTime']
        
        #校场的士兵数量
        modCamp = Gcore.getMod('Building_camp', self.uid)
        Soldiers = modCamp.getSoldierNum(TimeStamp)
        TotalSoldierNum = sum(Soldiers.values()) if Soldiers else 0
        body = {'Soldiers':Soldiers, 'TotalSoldierNum':TotalSoldierNum, "TimeStamp":TimeStamp}
        return Gcore.out(optId, body = body)
    
    @inspector(15102, ['GeneralId'])
    def MoveGeneral(self, param={}):
        '''校杨：移动武将'''
        optId = 15102
        
        GeneralId = param['GeneralId']
        PosId = param.get('PosId')
        
        modGeneral = Gcore.getMod('General', self.uid)
        EmbattleInfo = modGeneral.getMyGeneralsOnEmbattle(['GeneralId', 'PosId'])
            
        OnEmbattle = [General['PosId'] for General in EmbattleInfo if General['GeneralId'] == GeneralId]
        IsOccupy = [General['GeneralId'] for General in EmbattleInfo if General['PosId'] == PosId]
        
        GeneralNum = len(EmbattleInfo)
        recordData = {'uid':self.uid,'ValType':0,'Val':1,'GNum':0}#成就、任务记录 
        
        if (not OnEmbattle) and (not PosId): 
            return Gcore.error(optId, -15102001) #武将不在阵上无法移除
            
        if OnEmbattle and (not PosId):#从阵上移除武将
            GeneralNum -= 1
            self.mod.deletePos(GeneralId)
            recordData['GNum'] = GeneralNum
            return Gcore.out(optId, body = {},mission=recordData)
        
        if PosId not in range(1, 10, 1): #位置是1-9
            return Gcore.error(optId, -15102004)
                    
        if OnEmbattle and IsOccupy: #互换两名武将的位置
            stat = self.mod.exchangePos(GeneralId, OnEmbattle[0], IsOccupy[0], PosId)
        if OnEmbattle and (not IsOccupy):
            stat = self.mod.movePos(GeneralId, PosId)
        if (not OnEmbattle) and IsOccupy:
            stat = self.mod.insteadPos(GeneralId, IsOccupy[0], PosId)
            
        if (not OnEmbattle) and (not IsOccupy):
            #判断阵上武将是否满员
            if len(EmbattleInfo) >= 5:
                return Gcore.error(optId, -15102002) #阵上武将已满
            GeneralNum += 1
            stat = self.mod.addPos(GeneralId, PosId)
        if not stat:
            return Gcore.error(optId, -15102003) #布阵操作失败
        
        recordData['GNum'] = GeneralNum
        return Gcore.out(optId, body = {},mission=recordData)
            
    @inspector(15103, ['GeneralId', 'SoldierNum', 'SoldierType'])
    def ChangeSoldierNum(self, param={}):
        '''校场：改变武将的带兵类型，数量'''
        optId = 15103
        
        GeneralId = param['GeneralId']
        SoldierNum = param['SoldierNum']
        SoldierType = param['SoldierType']
        TimeStamp = param['ClientTime']
        
        modGeneral = Gcore.getMod('General', self.uid)
        Generals = modGeneral.getLatestGeneralInfo(TimeStamp=TimeStamp)
        GeneralsOnEmbattle = [General for General in Generals 
                              if General["PosId"] != 0]
        
        GeneralInfo = None
        SoldierOnEmbattle = 0
        for GeneralOnEmbattle in GeneralsOnEmbattle:
            if GeneralOnEmbattle['GeneralId'] == GeneralId:
                GeneralInfo = GeneralOnEmbattle
            if GeneralOnEmbattle['TakeType'] == SoldierType:
                SoldierOnEmbattle += GeneralOnEmbattle['TakeNum']
        
        kLeader = Gcore.loadCfg(Gcore.defined.CFG_BATTLE)["kLeaderAddNum"] #每统帅带兵数
        if not GeneralInfo:
            return Gcore.error(optId, -15103001) #该武将没上阵或没有该武将   
        if SoldierNum > (GeneralInfo['LeaderValue'] * kLeader): #需要改成读配置
            return Gcore.error(optId, -15103002) #带兵数量过大

        #校场的士兵数量
        modCamp = Gcore.getMod('Building_camp', self.uid)
        Soldiers = modCamp.getSoldierNum(TimeStamp)
        
        #空闲士兵数量
        SoldierFree = Soldiers.get('Soldier%s'%SoldierType, 0) - SoldierOnEmbattle
        
        #武将带兵数量
        if SoldierNum <= GeneralInfo['TakeNum']:
            TakeNum = SoldierNum
        else:
            TakeNum = min(SoldierNum, GeneralInfo['TakeNum'] + SoldierFree)
        
        UpGeneralInfo = {"TakeNum":TakeNum, "TakeType":SoldierType}
        modGeneral.updateGeneralById(UpGeneralInfo, GeneralId)
        
        recordData = {'uid':self.uid,'ValType':0,'Val':1}#成就、任务记录 
        return Gcore.out(optId, body = {"TakeNum":TakeNum, "TakeType":SoldierType},mission=recordData)
