#coding:utf8
#author:李志荣
#date:2013-5-14
#竞技场相关数值计算

import math

from CfgReader import cr
M = 1.2 #地形系数
W = 1.5 #攻克系数

def gen01Dict(chance,skillId):
    '''获取01的字典
    @author: Lizr
    @param chance: 出现技能ID的概率  可以是小数或整数  0.2=20=20%概率
    @param skillId: 技能ID 
    @return: {1:24,2:0,3:0,4:24....}
    '''
    import random
    if chance<1:
        chance*=100
    lis01 = []
    for i in xrange(100):
        if i<=chance:
            lis01.append(skillId)
        else:
            lis01.append(0)
    random.shuffle(lis01)
    dict01 = dict(zip(xrange(1, len(lis01) + 1, 1),lis01))
    dict1 = {}
    for k,v in dict01.iteritems():
        if v:
            dict1[k] = v
    return dict1

def getArmyAttack(**kw):
    '''计算方阵(军队)初始攻击力 未加技能加成
    初始攻击力 = 方阵初始士兵数量*兵种攻击*(1+α*武力)*军团科技加成*地形系数
    '''
    A = {1:0.000145,2:0.000145}
    
    
    #间接变量
    generalType = kw['generalType'] #武将类型
    soldierType = kw['soldierType'] #兵种类型
    landForm = kw.get('landForm',0) #地形
    
    #直接变量
    soldierAttack = kw['soldierAttack'] #兵种攻击 (已加成军团科技)
    soldierNum = kw['soldierNum'] #士兵数量
    forceValue = kw['forceValue'] #武将武力
    
    #缺省变量 
    clubTechAdd = kw.get('clubTechAdd',1)  #军团科技加成
    
    job = cr.get_cfg('tb_cfg_general', generalType, 'Job')

    m = M if cr.get_cfg('tb_cfg_soldier',soldierType,'LandForm')==landForm else 1
    a = A[job]
    if 0:
        print 'soldierAttack',soldierAttack
        print 'clubTechAdd',clubTechAdd
        print 'forceValue',forceValue
        print 'soldierNum',soldierNum
        print 'm',m
        print 'forceValue',forceValue
        print 'a',a
    
    result = soldierAttack * clubTechAdd * (1+a*forceValue) * soldierNum  * m
    
    return int(result)

def Get9Coord(x,y,space=1,isSelf=True): 
    ''' 给出9宫格中心坐标和间隔，获取周边的军队中心坐标
    @param x:中心坐标x
    @param y:中心坐标y
    @param space: 军队间隔
    @param isSelf: True已方  False敌方 
    
    @return dict 包含9宫格的字典
    '''
    CoordDict = {}
    ix = space+3
    iy = (space+3)*2
    
    #第一行
    CoordDict[1] = (x,y+iy)
    CoordDict[2] = (IncreaseX(x, y, ix),y+ix)
    CoordDict[3] = (x+ix,y)
    #第二行 
    CoordDict[4] = (IncreaseLeftX(x, y, ix),y+ix)
    CoordDict[5] = (x,y) #中心
    CoordDict[6] = (IncreaseLeftX(x, y, -ix),y-ix)
    #第三行
    CoordDict[7] = (x-ix,y)
    CoordDict[8] = (IncreaseX(x, y, -ix),y-ix)
    CoordDict[9] = (x,y-iy)
    
    if not isSelf: #若是NPC作映射
        opCoordDict = {}
        opCoordDict[1] = CoordDict[9]
        opCoordDict[2] = CoordDict[8]
        opCoordDict[3] = CoordDict[7]
        opCoordDict[4] = CoordDict[6]
        opCoordDict[5] = CoordDict[5]
        opCoordDict[6] = CoordDict[4]
        opCoordDict[7] = CoordDict[3]
        opCoordDict[8] = CoordDict[2]
        opCoordDict[9] = CoordDict[1]
        CoordDict = opCoordDict
    return CoordDict

def IncreaseX(x,y,step):
    '''右上或左下移动step步的时候增加x
    @param step:大于0右上 , 小于0左下 
    '''
    if bool(y%2):
        x = x+math.ceil(step/2)
    else:
        x = x+step/2
    return int(x)

def IncreaseLeftX(x,y,step):
    '''左上或右下移动step步的时候增加x
    @param step:大于0左上 , 小于0右下 
    '''
    if bool(y%2)==0:
        x = x-math.ceil(step/2)
    else:
        x = x-step/2
    return int(x)

def getArmyInfo(pvpType,serverId,userId,groupId,posId, generalRows, SoldiersTech): 
    '''获取参战军队信息 refer:BattleMod.getMyArmy 
    @param pvpType: 竞技类型 1:1v1 2:2v2 3:3v3
    @param serverId: 服务器ID
    @param userId: 用户DI
    @param groupId: 分组ID(1组 2组)
    @param posId: 组内成员ID(1,2,3,4,5,6)
    '''
    assert pvpType in (1,2,3)
    assert groupId in (1,2)
    assert posId in (1,2,3,4,5,6)
    
    MyArmy = {}
    MapId = pvpType
    #row_map = Gcore.getCfg('tb_cfg_pve_map',MapId)
    row_map = cr.get_cfg('tb_cfg_pvp_pos',(MapId,posId))
    CoordSet = Get9Coord(row_map['CenterX'], row_map['CenterY'], row_map['ArmySpace'], False)

    armyId = 100*posId
    armyNum = 0
    for row in generalRows:
        armyId += 1
        i = row['PosId']
        SoldierType = row['TakeType']
        SoldierNum = row['TakeNum']
        if SoldierNum == 0 or SoldierType == 0: #没有带兵不能上场，带兵类型是0也不能上场
            continue
        SoldierLevel = SoldiersTech.get(SoldierType,0)
        GeneralId = row['GeneralId']
        
        #row_soldier = cr.get_cfg('tb_cfg_soldier',SoldierType)
        row_soldier_up = cr.get_cfg('tb_cfg_soldier_up',(SoldierType,SoldierLevel))
        
        SoldierLife = row_soldier_up['Life']
        
        army = {}
        army['armyId'] = armyId
        army['armyUserId'] = '%s.%s' % (serverId, userId)
        army['armyType'] = groupId  #军队类型: 分组类型 1或2
        
        #army['__armySizeL'] = 3 #军队尺寸的长
        #army['__armySizeW'] = 3 #军队尺寸的宽
        
        army['armyLife'] = SoldierLife * SoldierNum   #军队的生命
        
        #按校场布阵 地图9宫格而定
        army['initPointX'] = CoordSet[i][0] #初始位置X
        army['initPointY'] = CoordSet[i][1] #初始位置Y
        army['generalId'] = GeneralId #武将ID 用于损兵
        army['generalType'] = row['GeneralType']   #武将技能种类 , 军队需要显示武将的名称 来源于武将类型配置
        army['generalLevel'] = row['GeneralLevel'] #武将技能等级
        SkillId = cr.get_cfg('tb_cfg_general',row['GeneralType'],'SkillId') #武将技能ID 暂定每个武将只有一个技能
        if SkillId:
            ChanceAdd = int( row['WitValue'] * 0.000055 )
            Chance = cr.get_cfg('tb_cfg_skill',SkillId,'SkillChance')+ChanceAdd
            army['SkillDict'] = gen01Dict(Chance,SkillId) 
        else:
            army['SkillDict'] = {}
        army['generalForce'] = row['ForceValue'] 
        army['generalWit'] = row['WitValue']  
        army['generalSpeed'] = row['SpeedValue']  
        army['generalLeader'] = row['LeaderValue']  
        
        army['soldierType'] = SoldierType
        #army['__soldierSort'] = row_soldier['SoldierSort'] #分类 步弓骑
        army['soldierLevel'] = SoldierLevel
        #army['__soldierLife'] = SoldierLife
        army['soldierNum'] = SoldierNum

        #army['__soldierAttackNum'] = row_soldier_up['Attack']
        #army['__soldierDefenseNum'] = row_soldier_up['Defense']
        #SumDefense += row_soldier_up['Defense']
        #army['__attackDistance'] = row_soldier['AttackDistance'] #攻击距离
        #army['__attackAngle'] = row_soldier['AttackRange'] #攻击角度
        #army['__attackFre'] = row_soldier['AttackFre'] #攻击频率
        #army['__armySpeed'] = row_soldier['Speed'] #移动速度
        #army['__warnRadius'] = row_soldier['WarnRadius'] #警戒距离 (半径 角度360度固定）
        army['face'] = 2 #面向            
        
        army['cur_armyLife'] = army['armyLife'] #当前军队生命 战斗中减少
        r = army
        ArmyAttack = getArmyAttack(
                                           generalType = r['generalType'],
                                           soldierType = r['soldierType'],
                                           soldierAttack = row_soldier_up['Attack'],
                                           soldierNum = r['soldierNum'],
                                           forceValue = r['generalForce'],
                                           )
        army['armyInitAttack'] = ArmyAttack
        armyNum += 1
        MyArmy[armyId] = army
    

    
    data = {
            'ArmyInfo':MyArmy,
            'armyNum':armyNum
            }
    return MyArmy

if __name__ == '__main__':
    import RedisMod
    uid = 1030
    generalRows = RedisMod.rm.getGeneralOnEmbattle(uid, 1)
    SoldiersTech = RedisMod.rm.getSoldierTech(uid, 1)
    print getArmyInfo(1,1,uid,1,2, generalRows, SoldiersTech)