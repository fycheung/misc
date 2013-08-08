#coding:utf8
#author:zhoujingjiang
#date:2013-3-18
#配置表

#RabbitMQ的交换机数
EXCHANGE_NUM = 2 #设置为cpu个数的一半 

#分服ID
SERVER_ID = 2
#服务器分组
SERVER_GROUP = 1

#分服与交换机换算关系
# + server_id % exchange_num + 1
#分服与队列换算关系
# + server_id
#分服与路由键换算关系
# + server_id

#总服redis服务器配置
REDIS_HOST = '10.1.1.19'
REDIS_PORT = 6379
REDIS_PASSWD = '123123'
REDIS_DB = 0
REDIS_ENCODING = 'utf-8'

#MySQL服务器配置
DB_HOST = '10.1.1.18'
DB_PORT = 3306
DB_SELECT = 'gamesg'
DB_USER = 'gamesg'
DB_PASSWD = '1231234'
DB_CHARSET = 'utf8'

#MySQL连接池配置
DBPoolCfg = {}
DBPoolCfg['mincached'] = 0
DBPoolCfg['maxcached'] = 0
DBPoolCfg['maxshared'] = 0
DBPoolCfg['maxconnections'] = 0
DBPoolCfg['blocking'] = True

#总服RabbitMQ配置
MQ_HOST = '10.1.1.19:5672' #NOTICE : PORT IS HERE TOO.
MQ_UID = 'guest'
MQ_PWD = 'guest'
MQ_VHOST = '/'

#
LIMIT_COUNT = 1000
