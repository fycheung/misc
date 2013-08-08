#coding:utf8
#author:zhoujingjiang
#date:2013-3-20
#MySQL连接池和操作

from random import randint

from DBUtils import PooledDB
import umysqldb

import config
import common
import MailSender
escape_string = lambda s:umysqldb.escape_string(str(s))

class MySQLConPool(common.Singleton):
    '''数据库连接池'''
    _inited = False
    def __init__(self):
        if not self.__class__._inited:
            self._pool = PooledDB.PooledDB(umysqldb, config.DBPoolCfg['mincached'], config.DBPoolCfg['maxcached'], \
                     config.DBPoolCfg['maxshared'], config.DBPoolCfg['maxconnections'], config.DBPoolCfg['blocking'], \
                     host=config.DB_HOST, user=config.DB_USER, passwd=config.DB_PASSWD, \
                     db=config.DB_SELECT, port=int(config.DB_PORT), charset=config.DB_CHARSET)
            self.__class__._inited = True

    def getConn(self):
        '''从连接池获取一个连接'''
        return self._pool.connection()
#end class MySQLConPool

mp = MySQLConPool() #单例

error_count = 0
def getConn():
    '''获取数据库连接'''
    global error_count
    try:
        conn = mp.getConn()
        error_count = 0
        return conn
    except Exception: #从连接池获取连接失败。 #发报警邮件
        error_count += 1
        if error_count % 1000 == 1: #每隔100次发个邮件
            subject = 'server:%s connects MySQLdb Failed!'%config.SERVER_ID
            body = 'error count:%d' % error_count
            MailSender.sendmail(subject, body)
        return None

def getCur(conn):
    '''生成一个游标'''
    try:
        return conn.cursor(umysqldb.cursors.DictCursor)
    except Exception: #获取游标失败
        return None

def close(conn, cur):
    try:
        if cur:
            cur.close()
    except Exception, e:
        print '关闭数据库游标失败' % str(e)

    try:
        if conn:
            conn.close()
    except Exception, e:
        print '关闭数据库连接失败' % str(e)

def printError(sql, e=None):
    print '=' * 50
    print '执行SQL出错 >>> ', sql
    print '错误   信息 >>>', e
    print '=' * 50
    # 写SQL错误日志
    # + todo

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
    
def query(sql, param=None):
    '''执行一条SQL，返回结果集'''
    try:
        conn = getConn()
        cursor = getCur(conn)

        if param:
            cursor.execute(sql, param)
        else:
            cursor.execute(sql)
        res = cursor.fetchall()
    except Exception, e:
        printError(sql, e)
        res = False
    finally:
        close(conn, cursor)
        return res

def execute(sql, param=None):
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

def out_rows(table, fields='*', where='1'):
    '''返回值：False（出错），由字典组成的元组（查询结果），空元组（查询到0条记录）'''
    try:
        conn = getConn()
        cursor = getCur(conn)
        sql = None

        if not isinstance(fields, (list, tuple)):
            fields = [fields]

        sql = "SELECT " + ",".join(fields) + " FROM " + table + " WHERE %s " % where
        cursor.execute(sql)
        res = cursor.fetchall()
    except Exception, e:
        printError(sql, e)
        res = False
    finally:
        close(conn, cursor)
        return res

def out_fields(table, fields='*', where='1'):
    '''返回值：False（出错），字典，None'''
    try:
        conn = getConn()
        cursor = getCur(conn)
        sql = None

        if not isinstance(fields, (list, tuple)):
            fields = [fields]

        sql = "SELECT " + ",".join(fields) + " FROM " + table + " WHERE %s " % where

        cursor.execute(sql)
        res = cursor.fetchone()
    except Exception, e:
        printError(sql, e)
        res = False
    finally:
        close(conn, cursor)
        return res

def out_field(table, field, where='1'):
    '''返回值：False（出错），列值，None'''
    try:
        conn = getConn()
        cursor = getCur(conn)
        sql = None

        if not isinstance(field, str):
            raise TypeError('argument field should be a string')
        sql = "SELECT " + field + " FROM " + table + " WHERE %s " % where

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

def rand_choose(table, where=1, n=1, fields='*'):
    '''从表中随机选取n条记录'''
    line_cnt = out_field(table, 'count(*)', where)

    start = randint(0, line_cnt - n) if line_cnt > n else 0
    where = ' %s LIMIT %s, %s' % (where, start, n)
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
        res = cursor.executemany(sql, values)
    except Exception, e:
        printError(sql, e)
        res = False
    finally:
        close(conn, cursor)
        return res

def delete(table, where='1'):
    '''删除记录'''
    if where == '1':
        return execute('TRUNCATE TABLE %s' % table)
    else:
        return execute('DELETE FROM %s WHERE %s' % (table, where))