#coding:utf8
#author:zhoujingjiang
#date:2013-3-20
#MySQL连接池和操作

from gevent import monkey; monkey.patch_all()

from random import randint

from DBUtils import PooledDB
import umysqldb

import config

escape_string = lambda s : umysqldb.escape_string(str(s))

class Singleton(object):
    '''单例模式'''
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance
#end class Singleton

class MySQLConPool(Singleton):
    '''数据库连接池'''
    _inited = False #实例是否被初始化
    def __init__(self):
        if not self.__class__._inited:
            self._pool = PooledDB.PooledDB(umysqldb, config.DBPoolCfg['mincached'], config.DBPoolCfg['maxcached'], \
                     config.DBPoolCfg['maxshared'], config.DBPoolCfg['maxconnections'], config.DBPoolCfg['blocking'], \
                     host=config.DB_HOST, user=config.DB_USER, passwd=config.DB_PASSWD, \
                     db=config.DB_SELECT, port=int(config.DB_PORT), charset=config.DB_CHARSET)
            self.__class__._inited = True
        else:
            pass

    def getConn(self):
        '''从连接池获取一个连接'''
        return self._pool.connection()
#end class MySQLConPool

_MySQLConPool = MySQLConPool()

def getConn():
    '''获取数据库连接'''
    return _MySQLConPool.getConn()

def getCur(conn):
    '''生成一个游标'''
    cur = conn.cursor(umysqldb.cursors.DictCursor)
    return cur

def close(conn, cur):
    try:
        if cur:
            cur.close()
        if conn:
            conn.close()
    except Exception, e:
        print '关闭数据库游标和连接时出错：%s' % str(e)

def printError(sql, e=None):
    print '=' * 50
    print '执行SQL出错 >>> ', sql
    print '错误   信息 >>>', e
    print '=' * 50

def insert(table, row):
    '''执行插入语句'''
    try:
        conn = getConn()
        cursor = getCur(conn)
        sql = None

        assert isinstance(row, dict) and len(row) > 0
        fields, values = zip(*row.items())
        sql = "INSERT INTO " + table + " (" + ",".join(fields) + ") VALUES(" + ",".join(map(escape_string, values)) + ")"
        cursor.execute(sql)
        res = cursor.lastrowid
    except Exception, e:
        printError(sql, e)
        res = False
    finally:
        close(conn, cursor)
        return res

def update(table, row, where):
    '''执行更新语句'''
    try:
        conn = getConn()
        cursor = getCur(conn)
        sql = None

        assert isinstance(row, dict) and len(row) > 0
        sqlArr = ['%s="%s"' % (k, row[k]) for k in row]
        sql = "UPDATE "+table +" SET "+",".join(sqlArr)+" WHERE "+where

        res = cursor.execute(sql)
    except Exception, e:
        printError(sql, e)
        res = False
    finally:
        close(conn, cursor)
        return res

def execute(sql, param = None):
    '''执行一条SQL，返回影响的行数'''
    try:
        conn = getConn()
        cursor = getCur(conn)

        if param:
            rowcount = cursor.execute(sql, param)
        else:
            rowcount = cursor.execute(sql)
    except Exception, e:
        printError(sql, e)
        rowcount = False
    finally:
        close(conn, cursor)
        return rowcount

def out_rows(table, fields = '*', where = '1'):
    '''返回值：False（出错），由字典组成的元组（查询结果），空元组（查询到0条记录）'''
    try:
        conn = getConn()
        cursor = getCur(conn)
        sql = None

        if not isinstance(fields, (list, tuple)):
            fields = [fields]

        sql = "SELECT " + ",".join(fields) + " FROM " + table + " WHERE " + where
        cursor.execute(sql)
        res = cursor.fetchall()
    except Exception, e:
        printError(sql, e)
        res = False
    finally:
        close(conn, cursor)
        return res

def out_fields(table, fields = '*', where = '1'):
    '''返回值：False（出错），字典，None'''
    try:
        conn = getConn()
        cursor = getCur(conn)
        sql = None

        if not isinstance(fields, (list, tuple)):
            fields = [fields]

        sql = "SELECT " + ",".join(fields) + " FROM " + table + " WHERE " + where

        cursor.execute(sql)
        res = cursor.fetchone()
    except Exception, e:
        printError(sql, e)
        res = False
    finally:
        close(conn, cursor)
        return res

def out_field(table, field, where = '1'):
    '''返回值：False（出错），列值，None'''
    try:
        conn = getConn()
        cursor = getCur(conn)
        sql = None

        if not isinstance(field, str):
            raise TypeError('argument field should be a string')
        sql = "SELECT " + field + " FROM " + table + " WHERE " + where

        cursor.execute(sql)
        res = cursor.fetchone()
        if res:
            res = res.get(field)
    except Exception, e:
        printError(sql, e)
        res = False
    finally:
        close(conn, cursor)
        return res

def rand_choose(table, where = 1, n = 1, fields = '*'):
    '''从表中随机选取n条记录'''
    line_cnt = out_field(table, 'count(*)', where)

    start = randint(0, line_cnt - n) if line_cnt > n else 0
    where = 'where LIMIT %s, %s' % (where, start, n)
    return out_rows(table, fields, where)

def insertmany(table, rows):
    '''插入多行'''
    try:
        conn = getConn()
        cursor = getCur(conn)
        sql = None

        values = [row.values() for row in rows]
        for row in rows:
            sql = 'insert into ' + table + '('+ ','.join(row.keys()) + \
              ') values(' + ','.join(['"%s"' for i in range(0, len(row.keys()))]) + ')'
            break
        print 'sql', sql
        res = cursor.executemany(sql, values)
    except Exception, e:
        printError(sql, e)
        res = False
    finally:
        close(conn, cursor)
        return res

def _test():
    '''模块内测试'''
    print insert('temp_tb_mac', {"Mac":1231, "UserId":1231, "remark":'123'})

if '__main__' == __name__:
    _test()
