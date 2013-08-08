#coding:utf8
#author:zhoujingjiang
#date:2013-04-12
#RabbitMQ

import sys
sys.path.insert(0, '../')
import amqp
import config

CONN = amqp.Connection(host=config.MQ_HOST, userid=config.MQ_UID, \
     password=config.MQ_PWD, virtual_host=config.MQ_VHOST, insist=False)
CHAN = CONN.channel() 

if len(sys.argv) != 2:
    sys.exit()

if sys.argv[1] == 'init':
    #在虚拟机下建立交换机，数量为cpu个数的一半
    exc_num = config.EXCHANGE_NUM
    for ind in range(1, exc_num + 1):
        CHAN.exchange_declare(exchange='sggameexchange%s'%ind, durable=True, \
                              auto_delete=False, type='direct')
    #建立队列和绑定，每个分服一个队列
    # + 假定server_id连续
    server_num = 3#config.SERVER_NUM
    for ind in range(1, server_num + 1):
        CHAN.queue_declare(queue='sggamequeue%s'%ind, durable=True, auto_delete=False)
        CHAN.queue_bind(queue='sggamequeue%s'%ind, exchange='sggameexchange%s'%(ind%exc_num+1),\
             routing_key=str(ind))

#关闭channel和connection
CHAN.close()
CONN.close()
