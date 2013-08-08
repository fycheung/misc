#-*- coding:utf-8 -*-
# note:   游戏配置
# date:   2012-05-15
# author: Lizr

#=============================== 分服独立配置  =================================
#服务器ID
CFG_SERVER_ID = 1 #分服n ID (统一用这个，弃用tb_config_core.ServerID)

#验证用户登录的密文
#SECRET_KEY = "*#@!!**&SGpythonkey"  (弃用，统一用tb_config_core.Encryption)

#城市服务器配置
CFG_GATEWAYSERV_HOST = "10.1.1.18" #*way.py已使用0.0.0.0 但两端口间socket通讯还要用
CFG_GATEWAYSERV_PORT = 8082

#战斗服务器配置
CFG_BATTLESERV_HOST = "10.1.1.18"  #*way.py已使用0.0.0.0 但两端口间socket通讯还要用
CFG_BATTLESERV_PORT = 8083

#本地 mysql数据库配置
DB_HOST = "10.1.1.18" 
DB_PORT = "3306"
DB_USR = "gamesg"
DB_PWD = "1231234"
DB_SELECT = "gamesg"
DB_CHARSET = "utf8"

#本服Redis 配置
REDISL_HOST = "10.1.1.18"
REDISL_PORT = 6379
REDISL_PWD = "" 
#================================END 分服独立配置 ===========================


#================================ 平台内各服通用配置 ===========================
#总服Redis 配置
REDISM_HOST = "10.1.1.19"  #10.1.1.19
REDISM_PORT = 6379 
REDISM_PWD = "123123"  #123123


#总服MQ服务器IP和端口
MQ_HOST = '183.60.41.107:5672' 
MQ_UID = 'guest'
MQ_PWD = 'guest'
MQ_VHOST = '/'
EXCHANGE_NUM = 2 #MQ交换机数量
#============================= END 平台内各服通用配置 ===========================


#====================================== 通用配置 =======================================
#项目根目录
from os.path import dirname,abspath
SYSTEM_ROOT = dirname( dirname( abspath( __file__ ) ) )  #定义上层目录为根目录 

#开发调试模式
TEST = 1 #1开发  2测试  0真网
TBNUM = 2 #拆表数量, 开发网和2 , 真网是 10
HEARTBEAT_TIME = 30 if not TEST else 30  #socket心跳时间

#调试等级
# Level Numeric value : NOTSET 0  | DEBUG 10 | INFO 20 | WARNING 30 | ERROR 40  | CRITICAL 50
LOGGING_OUT_LEVEL = 10 #输出级别  真网30
LOGGING_LOG_LEVEL = 10 #日志级别  真网30

#数据传输密文(与前台数据传输的加密,与客户端约定,不能修改)
SECRET_DATA_KEY = "*@#!*!*&"
SECRET_DATA_OPEN = 1 #是否开启数据传输的加密和压缩

#连接池配置
DBPoolCfg = {}
DBPoolCfg['mincached'] = 0 #启动时开启的空连接数量(缺省值 0 意味着开始时不创建连接)
DBPoolCfg['maxcached'] = 288 #连接池使用的最多连接数量(缺省值 0 代表不限制连接池大小)
DBPoolCfg['maxshared'] = 0 #最大允许的共享连接数量(缺省值 0 代表所有连接都是专用的)如果达到了最大数量，被请求为共享的连接将会被共享使用。
DBPoolCfg['maxconnections'] = 288 #最大允许连接数量(缺省值 0 代表不限制)
DBPoolCfg['blocking'] = True #设置在达到最大数量时的行为(缺省值 0 或 False 代表返回一个错误；其他代表阻塞直到连接数减少)
#====================================== END 通用配置 ====================================
