# -*- coding:utf-8 -*-  
# author:lizr
# date:2013-5-7
# RabbitMQ 操作类库
from sgLib.core import Gcore
import sgCfg.config as config
import gevent.queue
import json
import time
import amqp

class Rabbit(object):
    def __init__(self):
        self._queue = gevent.queue.Queue()
        self.con = None
        
    def start(self):
        pass

    def put(self, msg):
        print ' >> Rabbit not running...'
        #self._queue.put(msg)
        #print time.time(),'Rabbit.put > _queue.put',msg

    def loop(self):
        print 'Rabbit.loop()'
        delay = 1 #延迟标志 1数据库内有延迟 0没有
        while True:
            msg = self._queue.get()
            try:
                self.send(msg)
                if delay:
                    db = Gcore.getNewDB() 
                    rows = db.out_rows('tb_delay_mq','*')
                    if rows:
                        for row in rows:
                            print 'tb_delay_mq',row
                            affected_row = db.update('tb_delay_mq', {'lockstate':1}, "id=%s AND lockstate=0"%row['id'])
                            if affected_row:
                                try:
                                    msgdelay = eval(row['msg']) #需要把这条消息发出去
                                except Exception:
                                    continue
                                else:
                                    self.send(msgdelay)
                                finally:
                                    db.delete('tb_delay_mq','id=%s'%row['id'])
                    db.close()
                delay = 0
            except Exception, e:
                print 'Exception at Rabbit.loop() ',e
                #将队列插入数据库
                db = Gcore.getNewDB()
                dic = {
                       'msg':str(msg),
                       'CreateTime':Gcore.common.nowtime(),
                       }
                result = db.insert('tb_delay_mq',dic)
                if not result:
                    self._queue.put(msg) #如果插不进去 再加回队列中
                    gevent.sleep(10) #等待数据库恢复
                db.close()
                delay = 1
                self.con = None
    
    def send(self,msg):
        '''把msg发送到rabbitMQ服务器'''
        print 'Rabbit.send > ',msg
        chan = self.ensure_chan()
        message = amqp.Message(str(msg))
        message.properties['delivery_mode'] = 2
        toServerId = msg['toServerId']
        eid = toServerId % config.EXCHANGE_NUM
        if eid==0:
            eid = config.EXCHANGE_NUM
        chan.basic_publish(message, exchange='sggameexchange%d'%eid, routing_key=str(toServerId))
        
    def ensure_chan(self):
        '''获取channel'''
        if not isinstance(self.con, amqp.connection.Connection):
            self.con = amqp.Connection(host=config.MQ_HOST, userid=config.MQ_UID, \
                       password=config.MQ_PWD, virtual_host=config.MQ_VHOST, insit=False)
        else:
            for k in self.con.channels:
                if isinstance(self.con.channels[k], amqp.channel.Channel):
                    return self.con.channels[k]
        return self.con.channel()

if '__main__' == __name__:
    '''调试'''
    r = Rabbit()
    #print r.put({'toServerId':2, 'optId':15013})
    #print r.loop()
    Gcore.sendmq(15013, 1,{'jj':'sb'})
    print 'before sleep'
    time.sleep(10)
    print 'end'

