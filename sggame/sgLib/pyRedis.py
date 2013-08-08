# -*- coding:utf-8 -*-  
# author:lizr
# date:2013-5-6
# Redis操作类库
from sgLib.core import Gcore
from redis import Redis
import gevent
import gevent.queue
import json
import time

def redisLock(key):
    '''总服redis锁 e.g. key: 1.1001'''
    redis = Gcore.redisM
    debug = 1
    lockState = 0
    lockTime = 180*2
    nowtime =  int(time.time())
    lockKey = 'lockSG.'+key #不想与sg* 的hash同名
    result = redis.setnx(lockKey,nowtime+lockTime) #倒数30秒+攻城时间180+发送MQ时间
#    if debug:
#        print 'redisLock >> lockKey : %s'%lockKey
    if result == 0:
        unlockTime = redis.get(lockKey)
        if not unlockTime:
            unlockTime = 0
        if nowtime > int(unlockTime): #死锁
            if debug:
                print 'redisLock >> %s try unlock dead lock'%lockKey
            unlockTime = redis.getset(lockKey,nowtime+lockTime)
            if nowtime> int(unlockTime):
                if debug:
                    print 'redisLock >> %s unlock dead lock and lock success!'%lockKey
                lockState = 1
            else:
                if debug:
                    print 'redisLock >> %s unlock dead lock fail'%lockKey
        else:
            if debug:
                print 'redisLock >> %s locking...'%lockKey
    else: #锁成功
        if debug:
            print 'redisLock >> %s lock success!!!'%lockKey
        lockState = 1
    return lockState

def redisUnlock(key):
    '''总服redis锁 e.g. key: 1.1001'''
    redis = Gcore.redisM
    debug = 1
    nowtime =  int(time.time())
    lockKey = 'lockSG.'+key #不想与sg* 的hash同名
    unlockTime = redis.get(lockKey)
    if not unlockTime:
        if debug:
            print 'redisUnlock >> %s no need to unlock'%lockKey
    elif nowtime> int(unlockTime):
        if debug:
            print 'redisUnlock >> %s dead lock no need to unlock'%lockKey
    else:
        result = redis.delete(lockKey)
        if result:
            print 'redisUnlock >>  %s unlock success'%lockKey
            
    return None

class MyRedis(Redis):
    '''Redis子类'''
    
    def start(self,sign):
        self.sign = sign #标示 redisL redisM
        self._queue = gevent.queue.Queue()
        
    def put(self, buff):
        '''有新的set就调用这个添另到队列里'''
        #print 'put',buff
        self._queue.put(buff)

    def loop(self):
        '''用协程一直查有没有队列信息要发'''
        delay = 1 #延迟标志 1数据库内有延迟 0没有
        
        print 'MyRedis.loop()'
        while True:
            buff = self._queue.get() 
            dic = json.loads(buff)
            try:
                if delay:
                    db = Gcore.getNewDB() 
                    #将数据库记录查出来再set,如果set成功就删除记录
                    try:
                        rows = db.out_rows('tb_delay_redis','*')
                        if rows:
                            for row in rows:
                                affected_row = db.update('tb_delay_redis', {'lockstate':1}, "id=%s AND lockstate=0"%row['id'])
                                if affected_row:
                                    try:
                                        #print 'affected_row',affected_row
                                        #callMethod = getattr(Redis,row['method'])
                                        if row['method'] =='hset':
                                            Redis.hset(self,row['h'],row['k'],row['v']) 
                                            if not Gcore.IsServer:
                                                print 'delay Redis.hset',row['h'],row['k'],row['v']
                                        elif row['method'] =='set':
                                            Redis.set(self,row['k'],row['v']) 
                                            if not Gcore.IsServer:
                                                print 'delay Redis.set',row['k'],row['v']
                                        db.delete('tb_delay_redis','id=%s'%row['id']) #删除
                                    except:
                                        db.update('tb_delay_redis', {'lockstate':0}, "id=%s"%row['id']) #解锁
                    except Exception,e:
                        print e
                        pass
                    finally:
                        db.close()
                if dic['method'] =='hset':
                    Redis.hset(self,dic['h'],dic['k'],dic['v']) 
                elif dic['method'] =='set':
                    Redis.set(self,dic['k'],dic['v']) 
                    #print 'Redis.set',dic['k'],dic['v']
                delay = 0
            except:
                #将队列插入数据库
                db = Gcore.getNewDB()
                dic['CreateTime'] = Gcore.common.nowtime()
                result = db.insert('tb_delay_redis',dic)
                #print db.sql
                if not result:
                    self._queue.put(buff) #如果插不进去 再加回队列中
                    gevent.sleep(10) #等待数据库恢复
                db.close()
                delay = 1
                
    def set(self,k,v):
        print '%s.set'%self.sign,k,v
        dic = {'method':'set','k':k,'v':v}
        buff = json.dumps(dic)
        self.put(buff)
    
    def hset(self,h,k,v):
        print '%s.hset'%self.sign,h,k,v
        dic = {'method':'hset','h':h,'k':k,'v':v}
        buff = json.dumps(dic)
        self.put(buff)
    
    def hget(self,h,k,jsondecode=False):
        '''重写Redis.hget方法  
        @param h: hash
        @param k: key
        @param jsondecode: 是否将结果解码json
        '''
        try:
            value = Redis.hget(self,h,k)
            if jsondecode:
                value = json.loads(value)
        except:
            value = {} if jsondecode else None
        
        return value
    
    def get(self,k):
        try:
            value = Redis.get(self,k)
        except:
            value = None
        
        return value
    
    def blockhset(self,h,k,v):
        '''阻塞hset'''
        return Redis.hset(self,h,k,v)
    
    def blockset(self,k,v):
        '''阻塞set'''
        return Redis.set(self,k,v)
    
if '__main__' == __name__:
    '''调试'''
    #方法重写参考：http://hi.baidu.com/thinkinginlamp/item/3095e2f52c642516ce9f32d5
    #Gcore.redisL = MyRedis(本地local) 
    #Gcore.redisM = MyRedis(总服master)
    #Gcore.start时 要开始2条协程 Gcore.redisL.loop() Gcore.redisM.loop() 
    #使用 Gcore.redisL.set()
    #使用 Gcore.redisM.set()
    #Gcore.redisM.set('foo','bar1')
    #time.sleep(10)
    #Gcore.runtime()
    
