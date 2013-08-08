# -*- coding:utf-8 -*-
# author:Lizr
# date:2012-12-21
# 游戏外部接口

from sgLib.core import Gcore

class RedisUI(object):
    '''缓存竞技场所需信息'''
    def __init__(self, uid):
        self.uid = uid
    
    def OnCacheAll(self, param={}):
        '''缓存竞技场所需信息'''
        optId = 30001 
        
        modRedis = Gcore.getMod('Redis', self.uid)
        try:
            modRedis.onCacheAll()
        except Exception:
            return Gcore.out(optId, -30001001)
        else:
            return Gcore.out(optId)

if '__main__' == __name__:
    uid = 1005
    c = RedisUI(uid)
    c.OnCacheAll()
    