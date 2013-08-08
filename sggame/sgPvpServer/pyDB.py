#coding:utf8
#author:zhoujingjiang
#date:2013-3-20
#MySQL连接池和操作

from random import randint

from sqlalchemy.pool import QueuePool
import mysql.connector

import config

def ConnCreator():
    '''建立一个数据库连接'''
    db_args = {}
    db_args['charset'] = config.DB_CHARSET
    db_args['host'] = config.DB_HOST
    db_args['user'] = config.DB_USER
    db_args['passwd'] = config.DB_PASSWD
    db_args['port'] = config.DB_PORT
    db_args['db'] = config.DB_SELECT
    
    return mysql.connector.connect(**db_args)

DBPool = QueuePool(ConnCreator,
                   pool_size=500,
                   max_overflow=-1,
                   recycle=86400,
                   use_threadlocal=False,
                   echo=True
                   )

conn = DBPool.connect()
cursor = conn.cursor()
cursor.execute('select * from tb_cfg_building')
print reduce(lambda x, y:x + (dict(zip(cursor.column_names, y)), ),
             cursor.fetchall(),
             ())


