#coding:utf8
#author:zhoujingjiang
#date:2013-5-16
#RabbitMQ模型

import time

import amqp
import gevent
import gevent.queue

import common
import config
import MySQLMod as db

class RabbitMod(common.Singleton):
    _inited = False
    def __init__(self):
        if not self.__class__._inited:
            self._queue = gevent.queue.Queue()
            self.conn = None
            self.send_let = None
            self.__class__._inited = True
 
    def start(self):
        '''启动'''
        self.send_let = gevent.spawn(self.loop)

    def kill(self):
        '''关闭'''
        if hasattr(self.send_let, 'kill'):
            self.send_let.kill()
        #将队列中未发送的消息，放入数据库
        while not self._queue.empty():
            msg = self._queue.get()
            db.insert('tb_delay_mq', 
                      {'msg':str(msg), 'CreateTime':time.time()})

    def send(self, optId, toServerId, param):
        try:
            assert isinstance(param, dict)
            param['optId'] = int(optId)
            param['toServerId'] = int(toServerId)
        except Exception:
            return False
        gevent.spawn(self._queue.put, param)
        return True
    
    def chk_msg(self, msg):
        '''检查消息'''
        if isinstance(msg, basestring):
            msg = eval(msg)
        assert isinstance(msg, dict)
        msg['toServerId'] = int(msg['toServerId'])
        return msg

    def loop(self):
        delay_num = 0
        while 1:
            if delay_num: #如果数据库内有延迟的消息，先发送。
                try:
                    delay_mqs = db.out_rows('tb_delay_mq')
                    for delay_mq in delay_mqs:
                        try:
                            msg = self.chk_msg(delay_mq['msg'])
                        except Exception:
                            pass
                        else:
                            self._send(msg)
                        finally:
                            stat = db.execute('tb_delay_mq', 'id=%s'%delay_mq['id'])
                            if not stat:
                                raise TypeError
                            delay_num -= 1
                except TypeError:
                    print '数据库出错'
                except Exception: #发送消息失败
                    self.conn = None

            msg = self._queue.get() #发送队列里的消息
            try:
                msg = self.chk_msg(msg)
            except Exception: #错误的消息
                continue
            try:
                self._send(msg)
            except Exception:
                stat = db.insert('tb_delay_mq', 
                          {'msg':str(msg), 'CreateTime':time.time()})
                if not stat:
                    self._queue.put(msg)
                self.conn = None
                delay_num += 1

    def _send(self, msg):
        '''发消息'''
        chan = self.ensure_chan()
        
        message = amqp.Message(str(msg))
        message.properties['delivery_mode'] = 2

        toServerId = msg['toServerId']
        eid = toServerId % config.EXCHANGE_NUM
        eid = eid if eid else config.EXCHANGE_NUM
        
        chan.basic_publish(message, exchange='sggameexchange%d'%eid, routing_key=str(toServerId))
        
    def ensure_chan(self):
        '''获取channel'''
        if not isinstance(self.conn, amqp.connection.Connection):
            self.conn = amqp.Connection(host=config.MQ_HOST, userid=config.MQ_UID, \
                       password=config.MQ_PWD, virtual_host=config.MQ_VHOST, insit=False)
        else:
            for k in self.conn.channels:
                if isinstance(self.conn.channels[k], amqp.channel.Channel):
                    return self.conn.channels[k]
        return self.conn.channel()
#end class RabbitMod

rm = RabbitMod()