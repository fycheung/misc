#coding:utf8
#author:zhoujingjiang
#date:2012-5-24
#PVP外部接口

import json
import time
import copy

import PvpMod
from RedisMod import rm
import RabbitMod
import HonourMod
import common
import config

mod = PvpMod.pm

def EnterRoom(optId, UserId, ServerId, ArenaType, **para):
    '''进入Pvp房间'''
    #获取用户等级
    UserInfo = rm.getUserInfo(UserId, ServerId)
    #if not UserInfo:
    #    return common.error(optId, -(optId * 1000 + 1)) #获取用户信息失败。
    #UserLevel = UserInfo['UserLevel']
    #if UserLevel < config.ARENA_MIN_LEVEL:
    #    return common.error(optId, -(optId * 1000 + 2)) #级别不够(至少五级)
    
    #上阵武将
    GeneralOnEmbbatle = rm.getGeneralOnEmbattle(UserId, ServerId)
    #if not GeneralOnEmbbatle:
    #    return common.error(optId, -(optId * 1000 + 3)) #尚未布阵
    
    #获取科技等级
    SoldierTechs = rm.getSoldierTech(UserId, ServerId)
    #if not SoldierTechs:
    #    return common.error(optId, -(optId * 1000 + 4)) #获取科技等级失败

    #获取好友信息
    Friends = rm.getFriendInfo(UserId, ServerId)

    if mod.is_in_arena(UserId, ServerId):
        return common.error(optId, -(optId * 1000 + 5)) #已在战斗中
        
    if not ArenaType in [1, 2, 3]:
        return common.error(optId, -(optId * 1000 + 6)) #竞技场类型错误
    #加入到房间
    Infos = {'Generals':GeneralOnEmbbatle, 'User':UserInfo,
             'Techs':SoldierTechs}
    et = time.time()
    stat = mod.enter_room(UserId, ServerId, 20, et, Friends, ArenaType, Infos) ##等级先写死成20。
    if stat == -1:
        return common.error(optId, -(optId * 1000 + 7)) #竞技场尚未开始
    if stat == -2:
        return common.error(optId, -(optId * 1000 + 8)) #进入房间失败。
    return common.out(optId) #成功进入房间

def LeaveRoom(optId, UserId, ServerId, **para):
    '''离开房间'''
    stat = mod.leave_room(UserId, ServerId)
    if stat:
        return common.out(optId) #成功离开房间
    return common.error(optId, -(optId * 1000 + 1)) #不在房间中

def LeaveArena(optId, UserId, ServerId, **para):
    '''离开竞技场'''
    stat = mod.leave_arena(UserId, ServerId)
    if stat:
        return common.out(optId) #成功
    return common.error(optId, -(optId * 1000 + 1)) #不在竞技场战斗中

def MultiCastOpt(optId, UserId, ServerId, body, **para):
    '''广播战斗信息'''
    #参数检查
    if isinstance(body, basestring): #如果是字符串，先尝试转成字典。
        try:
            body = json.loads(body)
        except Exception:
            return common.error(optId, -(optId * 1000 + 1)) #不是jason字符串，失败。
    if isinstance(body, dict):
        body['ServerTime'] = time.time() #加上服务器端时间戳
        body['UserId'] = '%s.%s' % (ServerId, UserId) #加上UserId，ServerId
    else:
        return common.error(optId, -(optId * 1000 + 2)) #参数类型错误

    FightObj = mod.is_in_arena(UserId, ServerId) # 获取战斗对象
    # 注意：由于返回的是弱引用，使用的时候应该加括号：FightObj()
    if not FightObj:
        return common.error(optId, -(optId * 1000 + 3)) #不在战斗中，无法广播战斗信息。
    
    #战斗过程验证放在此处
    
    
    print '战斗是否结束', FightObj().is_fight_over()
    print '战斗是否超时', FightObj().is_time_out()
    print '战果是', FightObj().fight_over()
    print '当前损兵', FightObj().soldier_lose()
    print '1组与二组的级差', FightObj().user_level_diff()
    print '士兵和武将的平均等级', FightObj().army_level_avg()
    #开始广播
    body = json.dumps({"body":body}) #广播之前，转成json。
    stat = FightObj().zmq_muticast(body)
    if stat < 0:
        return common.error(optId, -(optId * 1000 - stat + 3))
        # -1 发送内容不正确；-2 zmq发布失败
    return common.out(optId) #广播成功

def ArenaEnd(optId, UserId, ServerId, **para):
    '''战斗结束'''
    FightObj = mod.is_in_arena(UserId, ServerId) # 获取战斗对象
    # 注意：由于返回的是弱引用，使用的时候应该加括号：FightObj()
    if not FightObj:
        return common.error(optId, -(optId * 1000 + 1)) #不在战斗中，无法结束战斗。
    
    fight_result = FightObj().fight_over()
    if fight_result == False: #没有达到战斗结束的条件
        return common.error(optId, -(optId * 1000 + 2))
    
    #处理战斗结果
    # + 发送消息给分服
    RabbitMod.rm.send(optId, ServerId, 
                      copy.deepcopy(fight_result[(UserId, ServerId)]))
    # + 更新荣誉表
    HonourMod.addHonour(UserId, ServerId, 
                        fight_result[(UserId, ServerId)]['gainHonour'], 
                        time.time())
    
    #从竞技场中退出 
    stat = mod.leave_arena(UserId, ServerId)
    if stat: #返回战斗结果给玩家
        return common.out(optId, 
            body={'FightResult':fight_result[(UserId, ServerId)]}) #成功
    return common.error(optId, -(optId * 1000 + 3)) #不在竞技场战斗中

def GetWeekHonour(optId, UserId, ServerId, **para):
    '''获取本周荣誉'''
    HonourNum = HonourMod.getWeekHonour(UserId, ServerId)
    return common.out(optId, {"HornourNum":HonourNum})

def _test():
    '''模块内测试'''
    print EnterRoom(100, 43277, 1, 1)

if '__main__' == __name__:
    _test()