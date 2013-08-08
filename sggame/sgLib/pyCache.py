# -*- coding:utf-8 -*-
from redis import Redis


class Cache(object):

    _instance =None
    

    def __init__(self,arg = 0):
        self.rds = Redis(db=arg)

    def __new__(self,*arg,**karg):        
        if not self._instance:
            self._instance = super(Cache,self).__new__(self,*arg,**karg)
        return self._instance

 
    def get(self,key):
        return self.rds.get(key)

    def set(self,key,value):
        return self.rds.set(key,value)


cache = Cache()

#取缓存
def getCache(key):
    return cache.get(key)

#存缓存
def setCache(key,value):
    return cache.set(key,value)
