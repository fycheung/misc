#coding:utf8

import time
import copy
import random

import redis
redis_client = redis.StrictRedis(host='10.1.1.19', port=6379, password='123123')

def getLvRange(SearchDict):
    '''获取等级范围'''
    sum = 0.
    for k in sorted(SearchDict.keys()):
        r = random.random()
        sum += SearchDict[k]
        if r <= sum:
            return k

def getLv(UserLevel, MaxLevel=99):
    '''获取等级'''
    assert UserLevel >= 15, 'UserLevel 大于等于 15'

    SearchDict = {1:0.5, 2:0.3, 3:0.1, 4:0.1}
    SearchRange = \
    {
        1:range(max(15, UserLevel-5), UserLevel+5+1), 
        2:filter(lambda lv:lv>=15, range(UserLevel-10, UserLevel-5)) + \
        range(UserLevel+5+1, UserLevel+10+1), 
        3:range(15, UserLevel-10),
        4:range(UserLevel+10+1, MaxLevel)
    }
    while 1:
        k = getLvRange(SearchDict)
        LvRange = SearchRange[k]
        if not LvRange:
            continue
        Lv = random.choice(LvRange)
        return Lv

def getCamp(UserCamp, Camps=[1, 2, 3]):
    '''获取阵营'''
    return random.choice([Camp for Camp in Camps if Camp != UserCamp])

def getOnLineUser():
    '''获取在线玩家'''
    return []

def acquireLock(UserId, ServerId):
    '''获取锁'''
    expire = 30 #过期时间
    curtimestamp = int(time.time()) #当前时间
    lockname = 'sgLock.%d.%d' % (UserId, ServerId) #锁名
    stat = redis_client.setnx(lockname, curtimestamp + expire)
    if stat:
        return True
    else: #获取锁失败，检查是否超时
        ttd = int(redis_client.get(lockname))
        if ttd > curtimestamp: #锁尚未过期，获取锁失败
            return False
        else: #锁已经过期
            ttd2 = int(redis_client.getset(lockname, curtimestamp + expire))
            if ttd2 <= curtimestamp: #仍然过期，成功获得锁
                return True
            else: #被其他客户端先获得了，获取锁失败。
                return False

#确保先获得了锁，才释放。
def releaseLock(UserId, ServerId):
    '''释放锁'''
    return redis_client.delete('sgLock.%d.%d' \
                    % (UserId, ServerId))

#确保先获得了锁，才设置。
def setexpire(UserId, ServerId):
    '''设置保护时间'''
    lockname = 'sgLock.%d.%d' % (UserId, ServerId)
    when = int(time.time() + 2 * 60 * 60)
    return redis_client.expireat(lockname, when)

def grepUser(UserLevel, UserCamp, ServerGroup, MaxLevel=99, Camps=[1,2,3]):
    '''匹配被攻打的玩家'''
    onlineusers = getOnLineUser()
    for cnt in range(1, 101, 1): #读配置
        lv, camp = getLv(UserLevel, MaxLevel), getCamp(UserCamp, Camps)

        #获取所有满足条件的用户
        keys = redis_client.keys('sgGrep.%d.*.*.%d.%d' % (ServerGroup, lv, camp))
        if not keys:
            continue
        keysCopy = copy.deepcopy(keys)
        for key in keys:
            chosen = random.choice(keysCopy)
            fields = chosen.split('.')
            if len(fields) != 6:
                continue
            UserId, ServerId = int(fields[2]), int(fields[3])
            # 匹配成功的条件
            # + 离线且未被匹配
            if chosen not in onlineusers and acquireLock(UserId, ServerId):
                return UserId, ServerId 
            else:
                keysCopy.remove(chosen)
    return False #匹配失败

if '__main__' == __name__:
    print grepUser(21, 3, 1)
    #print acquireLock(1, 2)
