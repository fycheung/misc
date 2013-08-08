#coding:utf8
#author:zhoujingjiang
#date:2013-3-20
#获取Redis客户端对象

import redis
from redis.connection import PythonParser, HiredisParser

try:
    import Hiredis
    hiredis_available = True
except ImportError:
    hiredis_available = False

import config

DefaultParser = HiredisParser if hiredis_available else PythonParser

class Singleton(object):
    '''单例模式'''
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance
#end class Singleton

class RedisConPool(Singleton):
    '''Redis连接池类'''
    def __init__(self):
        '''初始化器'''
        self._pool = redis.ConnectionPool(host = config.REDIS_HOST, port = config.REDIS_PORT, \
                                          db = config.REDIS_DB, password = config.REDIS_PASSWD,\
                                          encoding = config.REDIS_ENCODING, parser_class = DefaultParser)
        self._client = redis.StrictRedis(connection_pool = self._pool)

    def getClient(self):
        '''获取客户端'''
        return self._client
#end class RedisConPool

#RedisConPool对象
_RedisConPool = RedisConPool()

def getConn():
    '''获取Redis客户端'''
    return _RedisConPool.getClient()

#Note : 线程之间传递pipeline对象是不安全的。
def _getPipeline():
    '''获取Pipeline'''
    return _RedisConPool.getClient().pipeline()

def _test():
    '''测试'''
    conn = getConn()
    print conn.setex('test', '10', 20)

if '__main__' == __name__:
    _test()
