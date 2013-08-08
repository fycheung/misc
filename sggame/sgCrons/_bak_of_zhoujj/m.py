#coding:utf8
#author:zhoujingjiang
#date:2013-04-12
#RabbitMQ

import sys
sys.path.append('../')

import amqp
import config

CONN = amqp.Connection(host=config.MQ_HOST, userid=config.MQ_UID, \
     password=config.MQ_PWD, virtual_host=config.MQ_VHOST, insist=False)
CHAN = CONN.channel() 

chan = CHAN
chan.queue_delete('sggamequeue1')
chan.queue_delete('sggamequeue2')
chan.queue_delete('rpc_queue1')
chan.queue_delete('test_queue')


#关闭channel和connection
CHAN.close()
CONN.close()
