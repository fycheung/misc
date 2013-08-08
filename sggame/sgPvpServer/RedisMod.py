#coding:utf8
#author:zhoujingjiang
#date:2013-5-13
#redis操作

import json

import gevent
from gevent.queue import Queue
from redis import StrictRedis

import common
import config

class RedisMod(common.Singleton):
    '''Redis模型'''
    __slots__ = []
    _redis_client = StrictRedis(host=config.REDIS_HOST,
                                port=config.REDIS_PORT,
                                password=config.REIDS_PWD,
                                db=config.REDIS_DB)
    _queue = Queue(maxsize=0)
    _send_let = None

    def __getattr__(self, attr):
        '''包装Redis客户端实例'''
        if hasattr(self.__class__._redis_client, attr):
            attribute = getattr(self.__class__._redis_client, attr)
            def callmethod(*args, **kwargs):
                try:
                    is_async = kwargs.pop('block') if 'block' in kwargs else True
                    if is_async: #异步-默认
                        return gevent.spawn(attribute, *args, **kwargs)
                    return attribute(*args, **kwargs) #阻塞-关键字参数block设置为False
                except TypeError: raise
                except Exception: return self.exception_deal({"attr":attr, "args":args, 
                                            "kwargs":kwargs}) if is_async else False
            return callmethod
        raise AttributeError, '没有这个属性'
            
    def exception_deal(self, delay_msg):
        '''发送失败处理'''
        gevent.spawn(self.__class__._queue.put, delay_msg)
        return True
    
    def loop(self):
        '''将队列中的数据发出去'''
        while True:
            try:
                delay_msg = self.__class__._queue.get()
                getattr(self, delay_msg['attr'])(*delay_msg['args'], **delay_msg['kwargs'])
            except Exception:
                pass

    def kill(self):
        '''关闭'''
        #关闭发送协程
        if hasattr(self.__class__._send_let, 'kill'):
            self.__class__._send_let.kill()
        # 如有必要，队列消息放数据库
        # + todo

    def start(self):
        '''开启'''
        self.__class__._send_let = gevent.spawn(self.loop)
    
    #竞技场相关
    def __getHsetFrmRedis(self, uid, sid, name, res_typ=None):
        #res_typ - 数据的类型
        try:
            res = self.__class__._redis_client.hget(name, '%s.%s'%(sid, uid))
            if res is None: #redis中没此用户的数据
                return None
            res = json.loads(res)
            if isinstance(res_typ, type):
                assert isinstance(res, res_typ)
            return res
        except AssertionError:
            print '错误的记录', res # todo 删除？
            return False
        except Exception, e: #redis错误：查询 或 里面有错误的信息。
            print 'Redis查询时出错', str(e) # todo 报警？
            return False
    
    def getGeneralOnEmbattle(self, uid, sid):
        '''获取上阵的武将信息'''
        name = "sgGeneralOnEmbattle"
        Generals = self.__getHsetFrmRedis(uid, sid, name, list)
        ret = []
        for General in Generals:
            try:
                if int(General['TakeType']) and \
                    int(General['PosId']) and \
                    int(General['TakeNum']):
                    ret.append(General)
            except Exception:
                continue
        return ret
    
    def getSoldierTech(self, uid, sid):
        '''获取兵种科技'''
        name = 'sgTech'
        return self.__getHsetFrmRedis(uid, sid, name, dict)
    
    def getUserInfo(self, uid, sid):
        '''获取用户信息'''
        name = 'sgUser'
        return self.__getHsetFrmRedis(uid, sid, name, dict)
    
    def getFriendInfo(self, uid, sid):
        '''获取好友信息'''
        name = 'sgFriend'
        return self.__getHsetFrmRedis(uid, sid, name, dict)
#end class RedisMod

rm = RedisMod() #单例

if __name__ == '__main__':
    '''unnittest'''
    #rm.set('zjj', 'haoren')
    gevent.sleep(2)
