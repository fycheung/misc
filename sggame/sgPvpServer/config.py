#coding:utf8

#服务器ID
SERVER_ID = 'PVPSERVER'

#密钥
SECRET_KEY = "*#@!!**&SGpythonkey"

#战斗服务器
SERVER_IP = '10.1.1.18'
SERVER_PORT = 8086

#zeromq服务器
ZMQ_SERVER_HOST = '10.1.1.18'
ZMQ_SERVER_PORT = 15000 

#Redis服务器
REDIS_HOST = '10.1.1.19'
REDIS_PORT = 6379
REIDS_PWD = '123123'
REDIS_DB = 0

#MySQL服务器
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

#RabbitMQ配置
MQ_HOST = '10.1.1.19:5672'
MQ_UID = 'guest'
MQ_PWD = 'guest'
MQ_VHOST = '/'
EXCHANGE_NUM = 2

#邮件配置
SMTP_HOST = 'smtp.qq.com'
SMTP_PORT = 25
SMTP_USER = '744475502@qq.com'
SMTP_PASSWD = 'qby0410'
SMTP_RECEIVER = '15568852230@yeah.net' #接收邮箱


#主角最高等级
MAX_LEVEL = 99 
#1vs1,2vs2,3vs3的战斗时长
TIME_1V1 = 180
TIME_2V2 = 180
TIME_3V3 = 180
#能参加竞技场的最小等级
ARENA_MIN_LEVEL = 5