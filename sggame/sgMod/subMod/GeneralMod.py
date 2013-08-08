#coding:utf8
#author:zhoujingjiang
#date:2013-1-28
#comment:武将模型

import time
import copy

from sgLib.core import Gcore
from sgLib.base import Base

class GeneralMod(Base):
    '''武将模型'''
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid

    def getLatestGeneralInfo(self, Generals=None, TimeStamp=None, UserLevel=None, 
                             GeneralIds=None, fields='*', IsClubTech=True):
        '''获取玩家武将的最新信息'''
        # 参数：
        # + Generals - 武将表中所有武将的信息
        # + fields - 已取消，兼容以前的程序，现返回所有的字段
        # + GeneralIds - 要查询的武将
        # + + int, long, str - 查询单个武将的信息
        # + + list, tuple - 查询多个武将的信息
        # + + None - 查询玩家所有武将的信息
        # + IsClubTech - 是否加上军团科技和宝物对武将四维属性的加成
        
        # 返回值：
        # + 单个武将：dict or None
        # + 多个武将：list
        # + 都不是：False

        if not TimeStamp:TimeStamp = time.time()
        if not Generals:Generals = self.getMyGenerals()
        if not UserLevel:UserLevel = self.getUserLevel()
        
        #加上武馆训练的经验
        modGround = Gcore.getMod('Building_ground', self.uid)
        _, Generals = modGround.touchPractise(Generals, TimeStamp, UserLevel)
        
        if IsClubTech: #四维属性加上各种加成
            # + 军团科技影响
            modClub = Gcore.getMod('Building_club', self.uid)
            club_tech_effects = modClub.getClubTechAdd()

            # + 宝物影响
            treasure_effects = self.getEquipExEffect([General['GeneralId'] for General in Generals])

            # + 四维加上各种加成
            for General in Generals:
                General["ForceValue"] += int(club_tech_effects[1])
                General["WitValue"] += int(club_tech_effects[2])
                General["LeaderValue"] += int(club_tech_effects[3])
                General["SpeedValue"] += int(club_tech_effects[4])

                treasure_effect = treasure_effects[General['GeneralId']]
                General["ForceValue"] += int(General["ForceValue"] * treasure_effect['force'])
                General["WitValue"] += int(General["WitValue"] * treasure_effect['wit'])
                General["SpeedValue"] += int(General["SpeedValue"] * treasure_effect['speed'])
                General["LeaderValue"] += int(General["LeaderValue"] * treasure_effect['leader'])

        if not GeneralIds: #返回所有武将的信息
            return Generals
        elif isinstance(GeneralIds, (int, long, str)): #返回单个武将的信息
            for General in Generals:
                if General["GeneralId"] == int(GeneralIds):
                    return General
            return None
        elif isinstance(GeneralIds, (list, tuple)): #返回多个武将的信息
            ret = []
            for General in Generals:
                if General["GeneralId"] in map(int, GeneralIds):
                    ret.append(General)
            return ret
        return False

    def getEquipExEffect(self, GeneralIds=None, EquipType=5):
        '''获得扩展的装备(宝物 或 兵书)对武将的影响'''
        # 参数：
        # + EquipType - 5是宝物4是兵书
        # + GeneralIds - int, long, str获取扩展装备对单个武将的影响
        # + + GeneralIds - list, tuple获取扩展装备对多个武将的影响
        # + + GeneralIds - None获取扩展装备所影响的所有的武将
        # + + 默认是None

        # 返回值：
        # + 单个武将返回字典
        # + + 【宝物如：{'force':0.04, 'leader':0.04, 'speed':0.0, 'wit':0.0}】
        # + + 【兵书如：{'soldiertype':1, 'life':0.04, 'defense':0.04, 'attack':0.0}】
        # + 多个武将返回嵌套的字典，key是武将ID，value是影响
        # + + 【如{1101:{'soldiertype':1, 'life':0.04, 'defense':0.04, 'attack':0.0}}】

        if EquipType != 4 and EquipType != 5:
            EquipType = 5 #既不是宝物，也不兵书，则计算宝物的影响
  
        init_data = {} #初始数据
        if EquipType == 5: #宝物
            init_data['force'] = 0.
            init_data['wit'] = 0.
            init_data['speed'] = 0.
            init_data['leader'] = 0.
        else: #兵书
            init_data['life'] = 0.
            init_data['attack'] = 0.
            init_data['defense'] = 0.

        is_single = False #是否是返回单个武将的影响
        where = ' UserId=%s AND EquipStatus=%s AND ( ' % (self.uid, 2)
        if isinstance(GeneralIds, (int, long, str)):
            is_single = True
            GeneralIds = int(GeneralIds)
            where += ' GeneralId = %s ' % GeneralIds
        elif isinstance(GeneralIds, (list, tuple)):
            GeneralIds = map(int, GeneralIds)
            where += ' GeneralId = ' + ' OR GeneralId = '.join(map(str, GeneralIds))
        else:
            where += ' GeneralId != 0 '
        where += ' ) '

        table = 'tb_equip_treasure' if EquipType == 5 else 'tb_equip_warbook'
        cfg_table = 'tb_cfg_equip_treasure' if EquipType == 5 else 'tb_cfg_equip_warbook'
        equips = self.db.out_rows(table, '*', where)
        if not equips:
            if is_single:
                return init_data
            return dict.fromkeys(map(int, GeneralIds), init_data)

        if is_single:GeneralIds = [GeneralIds]
        elif GeneralIds is None:GeneralIds = [equip['GeneralId'] for equip in equips]
        init_datas = {}
        for GeneralId in GeneralIds:
            init_datas[GeneralId] = copy.deepcopy(init_data)
        for equip in equips:
            equip_type = equip['EquipType'] #类型
            equip_strength_lv = equip['StrengthenLevel'] #强化度
            
            #读配置
            cfg = Gcore.getCfg(cfg_table, equip_type)
            if EquipType == 5:
                init_datas[equip['GeneralId']]['force'] += cfg['BaseForce'] + equip_strength_lv * cfg['GrowForce']
                init_datas[equip['GeneralId']]['wit'] += cfg['BaseWit'] + equip_strength_lv * cfg['GrowWit']
                init_datas[equip['GeneralId']]['speed'] += cfg['BaseSpeed'] + equip_strength_lv * cfg['GrowSpeed']
                init_datas[equip['GeneralId']]['leader'] += cfg['BaseLeader'] + equip_strength_lv * cfg['GrowLeader']
            else:
                init_datas[equip['GeneralId']]['life'] += cfg['BaseLife'] + equip_strength_lv * cfg['GrowLife']
                init_datas[equip['GeneralId']]['attack'] += cfg['BaseAttack'] + equip_strength_lv * cfg['GrowAttack']
                init_datas[equip['GeneralId']]['defense'] += cfg['BaseDefense'] + equip_strength_lv * cfg['GrowDefense']
                init_datas[equip['GeneralId']]['soldertype'] = cfg['SoldierType']

            if is_single:
                return init_datas[equip['GeneralId']]
        return init_datas
        
    def getGeneralInfo(self, GeneralIds, fields='*'):
        '''获取单个或多个武将的信息 '''
        # 武将的四维属性不是最新的
        if isinstance(GeneralIds, (tuple,list)):
            where = 'UserId = %s AND (GeneralId= ' % self.uid + ' OR GeneralId = '.join(map(str, GeneralIds)) + ')'
            return self.db.out_rows(self.tb_general(), fields, where)
        else:
            return self.db.out_fields(self.tb_general(), fields, 
                                      'GeneralId=%s AND UserId=%s' %(GeneralIds, self.uid))

    def getMyGenerals(self, fields='*'):
        '''获取玩家所有武将 '''
        # 武将的四维属性不是最新的
        table = self.tb_general()
        where = "UserId=%s" % self.uid
        return self.db.out_rows(table, fields, where)

    def getMyGeneralsOnEmbattle(self, fields='*'):
        '''获取玩家上阵武将'''
        # 武将的四维属性不是最新的
        table = self.tb_general()
        where = "UserId=%s AND PosId != %d" % (self.uid, 0)
        return self.db.out_rows(table, fields, where)
    
    def getWallDefenseGeneral(self):
        '''获取玩家布防的武将列表'''
        table, fields = 'tb_wall_general', 'GeneralId'
        where = 'UserId=%s' % self.uid
        rows = self.db.out_rows(table, fields, where)
        return [row['GeneralId'] for row in rows] if rows else []

    def getGeneralTypeList(self):
        '''获取玩家拥有的武将类型列表'''
        table, fields = self.tb_general(), 'GeneralType'
        where = 'UserId=%s' % self.uid
        rows = self.db.out_rows(table, fields, where)
        return [row['GeneralType'] for row in rows] if rows else []

    def cutGeneralTakeNum(self, cutDict, TimeStamp=None):
        '''武将损兵
        @note - 武将ID一定要是int
        @called - 战斗结束时
        '''
        if (not isinstance(cutDict, dict)) or (not cutDict):
            return -1 #参数不正确

        table = self.tb_general()
        fields = ['GeneralId', 'LeaderValue', 'TakeNum', 'TakeType']
        where = ' UserId=%s AND PosId!=%d ' % (self.uid, 0)
        where += ' AND (GeneralId= ' + ' OR GeneralId= '.join(map(str, cutDict.keys())) + ')'
        Generals = self.db.out_rows(table, fields, where)
        print '武将带兵信息', Generals

        if len(cutDict) != len(Generals):
            return -2 #并不是所有的武将都存在 或 有的武将不在阵上

        #更新武将表
        sql = ' UPDATE %s SET TakeNum=CASE GeneralId ' % table
        soldier_loss = {}
        for general_id in cutDict:
            for general in Generals:
                if general['GeneralId'] == general_id:
                    descnum = min(cutDict[general_id], general['TakeNum'])
                    general['TakeNum'] -= descnum
                    soldier_loss[general['TakeType']] = soldier_loss.setdefault(general['TakeType'], 
                                                                                0) + descnum
                    sql += ' WHEN %d THEN %d ' % (general['GeneralId'], general['TakeNum'])
                    break
        sql += ' ELSE TakeNum END WHERE %s' % where
        print '损兵，更新武将表sql', sql
        self.db.execute(sql)

        #更新士兵表
        sql = 'UPDATE %s SET ' % 'tb_soldier'
        col2num = []
        for soldier_type in soldier_loss:
            col = 'Soldier%s' % soldier_type
            num = soldier_loss[soldier_type]
            col2num.append(' %s = IF(%s>=%s, %s-%s, 0) ' % (col, col, num, col, num))
        sql += ' , '.join(col2num)
        sql += ' WHERE UserId = %s ' % self.uid
        print '损兵，更新士兵表sql', sql
        stat = self.db.execute(sql)
        print '损兵，更新士兵表sql执行结果', stat
        return True

    def autoAddSoldier(self, TimeStamp=None):
        '''自动补兵'''
        TimeStamp = TimeStamp if TimeStamp else time.time()

        #上阵武将的信息
        Generals = self.getLatestGeneralInfo(TimeStamp=TimeStamp)
        onembattle = sorted([General for General in Generals if General["PosId"] and \
                           General["TakeType"]], key=lambda dic:dic["PosId"])
        if not onembattle:
            return -1 #没有上阵武将

        #当前士兵总数
        modCamp = Gcore.getMod('Building_camp', self.uid)
        soldiers = modCamp.getSoldiers()

        #剩余的士兵
        for General in onembattle:
            soldiers["Soldier%d"%General['TakeType']] -= General['TakeNum']
            assert soldiers["Soldier%d"%General['TakeType']] >= 0

        kLeaderAddNum = Gcore.loadCfg(Gcore.defined.CFG_BATTLE).get('kLeaderAddNum')
        sql = 'UPDATE %s SET TakeNum=CASE GeneralId ' % self.tb_general()
        for General in onembattle:
            num = min(soldiers["Soldier%d"%General['TakeType']],
                      General['LeaderValue'] * kLeaderAddNum - General["TakeNum"])
            General["TakeNum"] += num
            soldiers["Soldier%d"%General['TakeType']] -= num
            sql += ' WHEN %d THEN %d ' % (General["GeneralId"], General["TakeNum"])

        where = 'UserId = %s AND ( GeneralId = ' % (self.uid, )+ \
        ' OR GeneralId = '.join([str(General["GeneralId"]) for General in onembattle]) + ' ) '
        sql += ' ELSE TakeNum END WHERE %s ' % where

        return self.db.execute(sql)

    def incGeneralExp(self, General, ExpValue, UserLevel=None, flag=True):
        '''增加武将经验'''
        # 参数
        # + flag - 是否将武将信息更新到武将表
        # + + True - 更新到武将表
        # + + False - 不更新到武将表
        # + General - dict - 武将信息

        if not UserLevel:UserLevel = self.getUserLevel()

        #读配置
        GeneralCfg = Gcore.getCfg('tb_cfg_general')
        GeneralUpCfg = Gcore.getCfg('tb_cfg_general_up')
        MaxLevel = max(GeneralUpCfg.keys()) #武将的最高等级

        #武将基础信息
        GeneralId = General['GeneralId']
        GeneralLevel = General['GeneralLevel']
        GeneralType = General['GeneralType']
        General['ExpValue'] += int(ExpValue)
        
        #判断升级
        for lv in xrange(1, MaxLevel+1, 1):
            if (lv + GeneralLevel > MaxLevel) or (lv + GeneralLevel > UserLevel):
                break

            NxtLvExp = GeneralUpCfg[lv + GeneralLevel]['Exp']
            if NxtLvExp > General['ExpValue']: #经验不够升级
                break

            #改变等级，经验值
            General['ExpValue'] -= NxtLvExp
            General['GeneralLevel'] += 1

            #属性成长
            General['ForceValue'] += GeneralCfg[GeneralType]['GrowForce']
            General['WitValue'] += GeneralCfg[GeneralType]['GrowWit']
            General['SpeedValue'] += GeneralCfg[GeneralType]['GrowSpeed']
            General['LeaderValue'] += GeneralCfg[GeneralType]['GrowLeader']
        
        if flag: #将升级信息写入数据库。
            self.updateGeneralById(General, GeneralId)
            
        if ExpValue: #added by zhangguanghui
            modEvent = Gcore.getMod('Event', self.uid)
            modEvent.generalExpGet(General['GeneralType'], ExpValue)

        return General
    
    def touchGeneralLv(self, UserLevel=None):
        '''主角升级时更新武将的升级信息'''
        if UserLevel is None:UserLevel = self.getUserLevel()
        
        Generals = self.getMyGenerals()
        if not Generals:return 1 #没有武将直接返回

        sql = ' UPDATE %s SET ' % self.tb_general()

        exp = ' ExpValue = CASE GeneralId '
        lv = ' GeneralLevel = CASE GeneralId '
        force = ' ForceValue = CASE GeneralId '
        wit = ' WitValue = CASE GeneralId '
        speed = ' SpeedValue = CASE GeneralId '
        leader = ' LeaderValue = CASE GeneralId '

        GeneralIds = []
        for General in Generals:
            self.incGeneralExp(General, 0, UserLevel, flag=False)
            GeneralIds.append(str(General['GeneralId']))

            exp += ' WHEN %s THEN %s ' % (General['GeneralId'], General['ExpValue'])
            lv += ' WHEN %s THEN %s ' % (General['GeneralId'], General['GeneralLevel'])
            force += ' WHEN %s THEN %s ' % (General['GeneralId'], General['ForceValue'])
            wit += ' WHEN %s THEN %s ' % (General['GeneralId'], General['WitValue'])
            speed += ' WHEN %s THEN %s ' % (General['GeneralId'], General['SpeedValue'])
            leader += ' WHEN %s THEN %s ' % (General['GeneralId'], General['LeaderValue'])
            
        exp += ' ELSE ExpValue END, '
        lv += ' ELSE GeneralLevel END, '
        force += ' ELSE ForceValue END, '
        wit += ' ELSE WitValue END, '
        speed += ' ELSE SpeedValue END, '
        leader += ' ELSE LeaderValue END '
        
        sql += exp + lv + force + wit + speed + leader
        sql += ' WHERE UserId=%s AND ( GeneralId= ' % (self.uid, ) + ' OR GeneralId= '.join(GeneralIds) + ' )'
        print '升级时更新武将表sql', sql
        return self.db.execute(sql)

    def updateGeneralById(self, UpGeneralInfo, GeneralId):
        '''更新武将的信息'''
        return self.db.update(self.tb_general(), UpGeneralInfo, 'GeneralId=%s AND UserId=%s' % (GeneralId, self.uid))

    def deleteGeneralById(self, GeneralId):
        '''遣散武将'''
        EquipMap = {1:"HelmetId",2:"ArmourId",3:"WeaponId",4:"SashId",5:"BootsId",6:"JewelryId"}
        GeneralInfo = self.getGeneralInfo(GeneralId)
        if not GeneralInfo:
            return -1 #没有该武将
        
        for part in EquipMap:
            if GeneralInfo[EquipMap[part]]:
                return -2 #该武将身上有装备
        
        #是否带了兵书
        stat = self.db.out_field('tb_equip_warbook', 'COUNT(1)', 
                                 'UserId=%s AND GeneralId=%s AND EquipStatus=%s' % (self.uid, GeneralId, 2))
        if stat:
            return -2 #武将身上有兵书

        #是否带了宝物
        stat = self.db.out_field('tb_equip_treasure', 'COUNT(1)', 
                                 'UserId=%s AND GeneralId=%s AND EquipStatus=%s' % (self.uid, GeneralId, 2))
        if stat:
            return -2 #武将身上有宝物

        #从武将表中删除武将
        table = self.tb_general()
        sql = 'DELETE FROM %s WHERE UserId=%s AND GeneralId=%s' % (table, self.uid, GeneralId)
        self.db.execute(sql)
        
        #如果武将正在训练,从训练表中删除
        self.db.execute('DELETE FROM `tb_general_practise` WHERE UserId=%s AND GeneralId=%s' \
                        % (self.uid, GeneralId))
        #如果在布防表中，从布防表中删除
        self.db.execute('DELETE FROM `tb_wall_general` WHERE UserId=%s AND GeneralId=%s' \
                        % (self.uid, GeneralId))
        #如果在被访问日志表中，删除 by Lizr
        self.db.execute('DELETE FROM `tb_interact_general` WHERE GeneralUserId=%s AND GeneralId=%s' \
                        % (self.uid, GeneralId))
        return 1

    def addNewGeneral(self, GeneralType, BuildingId, TimeStamp, GeneralState=2, flag=False, getWay=1):
        '''增加新武将'''
        # 参数
        # + BuildingId - 放武将的点将台ID
        # + GeneralType - 武将类型
        # + flag - 是否需要检查该类型的武将是否已存在
        # + getWay - 武将的获得方式

        GeneralCfg = Gcore.getCfg('tb_cfg_general', GeneralType)       
        
        if (flag and int(GeneralType) in self.getGeneralTypeList()) or not GeneralCfg:
            return False

        setClause = \
        {
         "UserId":self.uid,
         "GeneralType":GeneralType,
         "GeneralLevel":1,
         "TrainForceValue":0,
         "TrainWitValue":0,
         "TrainSpeedValue":0, 
         "TrainLeaderValue":0,
         "ForceValue":GeneralCfg.get('BaseForce'),
         "WitValue":GeneralCfg.get('BaseWit'),
         "SpeedValue":GeneralCfg.get('BaseSpeed'),
         "LeaderValue":GeneralCfg.get('BaseLeader'),
         "ExpValue":0,
         "Location":BuildingId,
         "GeneralState":GeneralState,
         "CreateTime":TimeStamp
        }
        stat = self.db.insert(self.tb_general(), setClause)
        
        if stat: #added by zhangguanghui
            logData = {'UserId':self.uid,'GeneralType':GeneralType,
                       'UserType':Gcore.getUserData(self.uid,'UserType'),
                       'GetWay':getWay,'CreateTime':time.time()}
            self.db.insert('tb_log_general', logData, isdelay=True)
        return stat

    def changeEquip(self, General, EquipPart, EquipInstead):
        '''给武将穿装备或更换武将装备'''
        EquipMap = {1:"HelmetId",2:"ArmourId",3:"WeaponId",4:"SashId",5:"BootsId",6:"JewelryId"}
        if not EquipMap.get(EquipPart):
            return -1 #装备部位出错
        Equipwearing = General[EquipMap[EquipPart]]

        if Equipwearing == EquipInstead:
            return -2 #装备已在身上穿着

        where = ' UserId=%s AND ( EquipId=%s AND EquipStatus<3 ' % (self.uid, EquipInstead) 
        if Equipwearing != 0:
            where += ' OR EquipId=%s )' % Equipwearing
        else: where += ' ) '
        Equips = self.db.out_rows(self.tb_equip(), '*', where)

        if (Equipwearing == 0 and len(Equips) != 1) or \
           (Equipwearing != 0 and len(Equips) != 2):
            return -3 #新装备不存在

        for Equip in Equips:
            if str(Equipwearing) == str(Equip["EquipId"]):
                Equipwearing = Equip
            if str(EquipInstead) == str(Equip["EquipId"]):
                EquipInstead = Equip
        
        #判断EquipInstead是否可穿
        # + 是否被其他武将穿戴
        if EquipInstead['EquipStatus'] == 2:
            return -4
        # + 判断是否达到可穿戴等级
        RequireLevel = Gcore.getCfg('tb_cfg_equip', 
                                    EquipInstead['EquipType'], 
                                    'RequireLevel')
        if RequireLevel > General['GeneralLevel']:
            return -5
        # + 判断强化度是否低于武将等级
        if EquipInstead['StrengthenLevel'] > General['GeneralLevel']:
            return -6
        # + 装备部位
        EquipPartTmp = Gcore.getCfg('tb_cfg_equip', 
                                    EquipInstead['EquipType'], 
                                    'EquipPart')
        if EquipPartTmp != EquipPart:
            return -7
        
        #换装
        # + 武将属性
        if Equipwearing == 0:
            General['ForceValue'] += EquipInstead['EnhanceForce']
            General['WitValue'] += EquipInstead['EnhanceWit']
            General['SpeedValue'] += EquipInstead['EnhanceSpeed']
            General['LeaderValue'] += EquipInstead['EnhanceLeader']
        else:
            General['ForceValue'] += EquipInstead['EnhanceForce'] - Equipwearing['EnhanceForce']
            General['WitValue'] += EquipInstead['EnhanceWit'] - Equipwearing['EnhanceWit']
            General['SpeedValue'] += EquipInstead['EnhanceSpeed'] - Equipwearing['EnhanceSpeed']
            General['LeaderValue'] += EquipInstead['EnhanceLeader'] - Equipwearing['EnhanceLeader']
        General[EquipMap[EquipPart]] = EquipInstead['EquipId']
        self.updateGeneralById(General, General['GeneralId'])
        
        modBag=Gcore.getMod('Bag', self.uid)
        # + 装备状态
        if Equipwearing == 0:
            sql = 'UPDATE %s SET GeneralId=%s, EquipStatus=%s where UserId=%s AND EquipId=%s' \
            % (self.tb_equip(), General['GeneralId'], 2, self.uid, EquipInstead['EquipId']) 
            stat = modBag.moveEquip(remove=EquipInstead['EquipId'])
            print '从背包删除装备', stat
        else:
            sql = '''UPDATE %s SET GeneralId = CASE EquipId WHEN %s THEN %s WHEN %s THEN %s END,
                                   EquipStatus = CASE EquipId WHEN %s THEN %s WHEN %s THEN %s END
                     WHERE UserId=%s AND ( EquipId=%s OR EquipId=%s )
                  ''' % (self.tb_equip(), Equipwearing['EquipId'], 0, 
                         EquipInstead['EquipId'], General['GeneralId'], 
                         Equipwearing['EquipId'], 1, 
                         EquipInstead['EquipId'], 2, self.uid, 
                         EquipInstead['EquipId'], Equipwearing['EquipId'])
            modBag.moveEquip(add=Equipwearing['EquipId'], remove=EquipInstead['EquipId'])
        
        self.db.execute(sql)
        return 1
    
    def changeEquip_EX(self, General, EquipId, EquipType):
        '''给武将穿或换兵书或宝物'''
        #EquipType - 1宝物；非1兵书
        
        #查出装备信息
        table = 'tb_equip_treasure' if EquipType == 1 else 'tb_equip_warbook'
        cfg_table = 'tb_cfg_equip_treasure' if EquipType == 1 else 'tb_cfg_equip_warbook'
        goods_type = 5 if EquipType == 1 else 4
        equips = self.db.out_rows(table, '*', 
            'UserId=%s AND (EquipId=%s OR GeneralId=%s)' % (self.uid, EquipId, General['GeneralId']))
        
        EquipInstead = None
        EquipWearing = None
        for equip in equips:
            if equip['GeneralId'] == General['GeneralId']:
                EquipWearing = equip
            if equip['EquipId'] == EquipId:
                EquipInstead = equip
        
        if EquipInstead is None:
            return -1 #没有这个兵书或宝物
        if EquipInstead['EquipStatus'] != 1:
            return -2 #要穿的兵书或宝物不处于空闲状态
        if (EquipInstead == EquipWearing):
            return -3 #兵书或宝物正在武将身上穿着
        
        #是否达到可穿戴等级
        require_level = Gcore.getCfg(cfg_table, 
                                     EquipInstead['EquipType'], 
                                     'RequireLevel')
        if require_level > General['GeneralLevel'] or require_level == 0:
            return -4 #未达到穿戴等级
        
        #装备强化等级是否小于武将等级
        if EquipInstead['StrengthenLevel'] > General['GeneralLevel']:
            return -5 #装备强化度大于武将等级

        modBag=Gcore.getMod('Bag', self.uid)
        sql = None
        if EquipWearing is None: #穿兵书或宝物
            print '穿兵书 或 宝物'
            # + 更新兵书表或宝物表
            sql = '''UPDATE %s SET GeneralId=%s, EquipStatus=%s WHERE UserId=%s AND EquipId=%s
                    ''' % (table, General['GeneralId'], 2, self.uid, EquipInstead['EquipId']) 
            # + 将装备从背包移除
            stat = modBag.moveEquip(remove=EquipInstead['EquipId'], goodsType=goods_type)
            print '从背包删除装备', stat
        else: #置换兵书或宝物
            sql = '''UPDATE %s SET GeneralId=CASE EquipId WHEN %s THEN %s WHEN %s THEN %s ELSE GeneralId END,
                        EquipStatus=CASE EquipId WHEN %s THEN %s WHEN %s THEN %s ELSE EquipStatus END
                    WHERE UserId=%s AND (EquipId=%s OR EquipId=%s)
                    ''' % (table, EquipWearing['EquipId'], 0, EquipInstead['EquipId'], 
                           General['GeneralId'], EquipWearing['EquipId'], 1, EquipInstead['EquipId'], 2,
                           self.uid, EquipInstead['EquipId'], EquipWearing['EquipId'])
            modBag.moveEquip(add=EquipWearing['EquipId'], remove=EquipInstead['EquipId'], goodsType=goods_type)
        print 'sql', sql
        self.db.execute(sql)
        return 1

    def stripEquip_EX(self, GeneralId, EquipType):
        '''将武将的兵书或宝物脱下来'''
        #EquipType - 1宝物；非1兵书
        table = 'tb_equip_treasure' if EquipType == 1 else 'tb_equip_warbook'
        goods_type = 5 if EquipType == 1 else 4
        
        where = ' UserId=%s AND GeneralId=%s AND EquipStatus=%s' % (self.uid, GeneralId, 2)
        wearing = self.db.out_fields(table, '*', where)
        if not wearing:
            return -1 #没穿装备，无法脱下。

        modBag = Gcore.getMod('Bag', self.uid)
        stat = modBag.moveEquip(add=wearing['EquipId'], goodsType=goods_type)
        print '向背包中增加装备', wearing['EquipId'], ('成功' if stat else '失败'), stat
        if not stat:
            return -2 #向背包中增加装备失败
        
        #更新兵书或宝物表
        fields = {'GeneralId':0, 'EquipStatus':1}
        return self.db.update(table, fields, where)

    def stripEquip(self, General, EquipPart):
        '''将武将某个部位的装备脱下来'''
        EquipMap = {1:"HelmetId",2:"ArmourId",3:"WeaponId",4:"SashId",5:"BootsId",6:"JewelryId"}
        Equipwearing = General.get(EquipMap.get(EquipPart))
        if not Equipwearing:
            return -1 #错误的请求：装备部位不正确或该武将在该部位上没有装备，无法脱下。
        
        modBag = Gcore.getMod('Bag', self.uid)
        stat = modBag.moveEquip(add=Equipwearing)
        print '向背包中增加装备', Equipwearing, ('成功' if stat else '失败'), stat
        if not stat:
            return -2 #向背包中增加装备失败
        
        Equipwearing = self.db.out_fields(self.tb_equip(), 
                                          '*', 
                                          'UserId=%s AND EquipId=%s' % (self.uid, Equipwearing))

        # 脱装备
        # + 减少武将属性
        General['ForceValue'] -= Equipwearing['EnhanceForce']
        General['WitValue'] -= Equipwearing['EnhanceWit']
        General['SpeedValue'] -= Equipwearing['EnhanceSpeed']
        General['LeaderValue'] -= Equipwearing['EnhanceLeader']  
        General[EquipMap[EquipPart]] = 0
        print '武将脱装备', EquipMap[EquipPart]
        # + 更新武将表
        self.updateGeneralById(General, General['GeneralId'])
        
        # + 装备状态
        self.db.update(self.tb_equip(), 
                       {"EquipStatus":1, "GeneralId":0},
                       'UserId=%s AND EquipId=%s' % (self.uid, Equipwearing['EquipId']))
        return 1
    
    def changeAttr(self, general_id, force, speed, wit, leader):
        '''改变武将的四维属性'''
        # general_id-武将Id, force-增加的武力值, speed-增加的速度值,
        # + wit-增加的智力值, leader-增加的统帅值.
        # + 如果四维为负数,则表示减少。

        if not (force or speed or wit or leader):
            return True
        sql = '''UPDATE %s SET ForceValue=ForceValue+%d,
                                SpeedValue=SpeedValue+%d,
                                WitValue=WitValue+%d,
                                LeaderValue=LeaderValue+%d
                WHERE UserId=%s AND GeneralId=%d''' \
                %(self.tb_general(), force, speed, wit, leader, self.uid, general_id)
        flag = self.db.execute(sql)
        if flag: #added by zhangguanghui
            Gcore.getMod('Event', self.uid).generalChangeAttr(force,speed,wit,leader)#任务事件
        return flag
    
    ##############下面程序是别人加的#################

    def warIncrGeneralExp(self,GeneralIds,ExpValue):
        '''战役成功后增加武经验
        @param GeneralIds:  武将ID列表
        @param Exp: 需要增加的经验
        '''
        Generals = self.getGeneralInfo(GeneralIds)
        UserLevel = self.getUserInfo('UserLevel')
        for General in Generals:
            self.incGeneralExp(General,ExpValue,UserLevel)
            #print 'warIncrGeneralExp',self.db.sql
            
    def getGeneralInterEffect(self):
        '''
        :获取武将内政影响
        '''
        result = {}
        gTable = self.tb_general()
        generalCfg = Gcore.getCfg('tb_cfg_general')
        generals= self.db.out_rows(gTable,['*'],'UserId=%s'%self.uid)
        for g in generals:
            gc = generalCfg.get(g.get('GeneralType'))
            ies = gc.get('InterEffectId')
            if not ies:
                continue
            ies = ies.split(',')
            for ie in ies:
                effectId = int(ie)
                gAttr = g['TrainForceValue']+g['TrainWitValue']+g['TrainSpeedValue']+g['TrainLeaderValue']
                gAttr += g['ForceValue']+g['WitValue']+g['SpeedValue']+g['LeaderValue']
                attrAdd = gAttr/5000.0#todo基数配置，内政初始数值配置
                effectValue = round(0.01*(1+attrAdd),2)
                result[effectId] = result.get(effectId,0) +effectValue 
        return result
    
    def addTrainRecord(self,gt,tt):
        '''
        :武将训练记录
        @param gt:武将类型
        @param tt:训练类型
        #By Zhanggh 2013-5-29
        '''
        data = {'UserId':self.uid,'GeneralType':gt,
                'UserType':Gcore.getUserData(self.uid,'UserType'),
                'TrainType':tt,'CreateTime':time.time()}
        self.db.insert('tb_log_general_train',data,isdelay=True)
#end class GeneralMod

if __name__ == '__main__':
    c = GeneralMod(44493)
    Gcore.printd(c.getLatestGeneralInfo())
