# -*- coding:utf-8 -*-  
# author:Lizr
# date:2012-12-21
# 数据库连接池和连接类
from gevent import monkey; monkey.patch_all() #必须要，去掉就变了单线线 协程堵塞 move to core
from random import randint
import umysqldb  #没有ping方法，作为DBUtils的dbapi不能开启ping参数
import MySQLdb
from DBUtils import PooledDB
import sgCfg.config as cfg
DebugLog = False

class DBPool(object):
    """数据库连接池"""
    pool = None
    @staticmethod
    def createPool():
        if not DBPool.pool:
            from sgLib.setting import Setting
            if Setting.getDatabase():
                DB_SELECT = Setting.getDatabase() #在gateway设置的数据库 不配置的
            else:
                DB_SELECT = cfg.DB_SELECT
            print '>>>创建连接池  ',DB_SELECT 
            DBPool.pool = PooledDB.PooledDB(umysqldb,
                                            cfg.DBPoolCfg['mincached'],
                                            cfg.DBPoolCfg['maxcached'],
                                            cfg.DBPoolCfg['maxshared'],
                                            cfg.DBPoolCfg['maxconnections'],
                                            cfg.DBPoolCfg['blocking'],ping=0,
                                            host=cfg.DB_HOST,
                                            user=cfg.DB_USR,
                                            passwd=cfg.DB_PWD,
                                            db=DB_SELECT,
                                            port=int(cfg.DB_PORT),
                                            charset=cfg.DB_CHARSET) #创建连接池
    @staticmethod
    def createCon():
        #print ' --- before createCon'
        #print 'DBPool',DBPool
        #print 'DBPool.pool',DBPool.pool
        if not DBPool.pool:
            DBPool.createPool()
        con = DBPool.pool.connection()
        #print ' --- after createCon',con
        return con

class DB(object):
    """连接类,读写分开预留接口 协程安全 所有协程可以共用一个DB() 单例
    #@todo 还不兼容语句中带有%的情况,待处理
    """
    def __init__(self):
        self.pool = DBPool
        self.sql = None #最后一次运行的sql,方便调试 线程不安全,不能用于执行
    def ssql(self):
        '''输出sql语句'''
        if TEST:
            print 'DB >>> '+self.sql
    
    def _set(self,sql):
        '''最后一次运行的sql,方便调试 线程不安全'''
        self.sql = sql
        
    def _create(self):
        '''从连接池拿连接和指针'''
        con = self.pool.createCon()
        cursor = con.cursor( umysqldb.cursors.DictCursor )
        #print 'DB._create',con,cursor
        return con,cursor
        
    def _close(self,con=None,cursor=None):
        '''关闭连接'''
        #print 'DB._close',con,cursor
        try:
            if cursor:
                cursor.close()
        except Exception,e:
            print ' --- DB.cursor > closed fail',e
        try:
            if con:
                con.close()
        except Exception,e:
            print ' --- DB.con > closed fail',e
    
    def close(self):
        '''旧 将弃用'''
        
    def query(self,sql,args=None,fetchAll=True):
        '''执行查询语句,并返回结果,推荐直接使用fetchone(),fetchall() 
        @note:涉及连接
        '''
        self._set(sql)
        if sql.lower().startswith('insert') or  sql.lower().startswith('update') or  sql.lower().startswith('delete'):
            self.sql_error(sql, 'DB.query can only execute query> %s\n' % sql)
            return False
        try:
            con,cursor = self._create() 
            cursor.execute(sql,args)
            if fetchAll:
                result =  cursor.fetchall()
                return result if result else () #有无记录返回类型一致 ,以免前端闪退
            else:
                result = cursor.fetchone()
                return result if result else {} #有无记录返回类型一致 ,以免前端闪退
        except Exception, e:
            self.sql_error(sql,e)
            return False
        finally:
            self._close(con, cursor)
            
    def execute(self,sql,args=None,isdelay=False):
        '''增 删 改
        @note:涉及连接
        @param isdelay: 是否到日志中心统一处理 
        '''
        self._set(sql)
        if isdelay:
            from sgLib.core import Gcore
            Gcore.sqldelay(sql)
        else:
            try:
                con,cursor = self._create()
                result = cursor.execute(sql, args) #如果是更新直接就是影响行数
                con.commit() #提交事务，兼容InnoDB
                if sql.lower().startswith('insert'):
                    return cursor.lastrowid  #如果是插入语句,返回lastid
                else:
                    return result
            except Exception, e: #Exception MySQLdb.Error
                self.sql_error(sql,e,'execute')
                return False
            finally:
                self._close(con,cursor)
            
    def executemany(self, sql, args):
        '''原有方法
        @note:涉及连接
        '''
        self._set(sql)
        try:
            con,cursor = self._create()
            return cursor.executemany(sql, args)
        except Exception, e:
            self.sql_error(sql,e,'executemany')
            return False
        finally:
            con.commit() #提交事务，兼容InnoDB
            self._close(con,cursor)
    
    #================================= 以下方法不涉及连接  ==================================  
    def fetchone(self, sql, args=None):
        '''查询一条记录  @return dict'''
        try:
            result = self.query(sql,args,fetchAll=False)
            return result if result else {} #有无记录返回类型一样 dict
        except Exception:
            return False

    def fetchall(self, sql, args=None):
        '''查询所有记录 @return tuple'''
        try:
            result = self.query(sql,args,fetchAll=True)
            return result if result else () #有无记录返回类型一样 tuple
        except Exception:
            return False
               
    def insert(self, table, row, isdelay=False):
        '''单条插入 @return int or False
        @param isdelay: 是否交由日志中心统一处理
        '''
        try:
            fields = []
            values = []
            for key in row:
                fields.append(key)
                values.append("'"+self.escape_string(str(row[key]))+"'")
            sql = "INSERT INTO "+table+" ("+str.join(",",fields)+") VALUES ("+str.join(",",values)+")"
            if isdelay:
                self.execute(sql, None, isdelay)
            else:
                return self.execute(sql)
        except Exception, e:
            self.sql_error(sql, e)
            return False


    def insertmany(self, table, rows):
        '''批量插入 rows: [{'id':1},{'id':2},{'id':2}] '''
        try:
            values = [row.values() for row in rows]
            sql = 'insert into ' + table + '('+ ', '.join(rows[0].keys()) + \
                ') values(' + ', '.join(['"%s"' for i in range(0, len(rows[0].keys()))]) + ')'
                
            self.executemany(sql, values)
        except Exception, e:
            self.sql_error(sql, e)
            return False

    def updatemany(self,table,info,where):
        '''一次更新多条记录 谨用 by Lizr
        @param table: 表名
        @param where: 条件(可能跟要更新的内容有关，暂自行构造 )
        @param info: 字段内容信息 [(0,1,2),(0,1,2),...]
        0为要更新的字段, 1为CASE的字段, 2为 WHEN k THEN v的字典, 3(可省)ELSE的值
        @note: 如果where中条件包含 又没有给出WHEN THEN的值 就会改为ELSE的值,如果没有给出ELSE的值便是0或空
        @例: 
        #单字段更新，比较常用的情况
        info = ('val1','val2',{1:2,2:3,3:4,4:5},'val1') 
        
        #多单段更新
        info = [('val1','val2',{1:2,2:3,3:4,4:5}), ('val3','val4',{1:0,2:1,3:2},'val1')] 
        where = 'id in (1,2,3,4)'
        '''
        assert isinstance(info, (list,tuple))
        
        if isinstance(info,tuple):
            info = [info]
        sql = 'UPDATE %s SET'%table
        for row in info: 
            sql += ' %s = CASE %s' % (row[0], row[1])
            for k,v in row[2].iteritems():
                sql += ' WHEN %s THEN %s' % (k,v)
            if len(row)>3:
                sql += ' ELSE %s' % row[3]
            sql += ' END,' #如果where中有包含 但又没给出when then则会变为0, 如果这种情况用ELSE 原字段 END
        sql = sql.strip(',') + ' WHERE %s'%where
        print 'updatemany >> %s'%sql
        return self.execute(sql)

    def update(self,table,row,where):
        '''执行更新语句  @return int'''
        try:
            sqlArr = []
            for key in row:
                if type(row[key]) == str:
                    row[key] = self.escape_string(row[key])
                sqlArr.append("%s='%s'"%(key,row[key],))
            sql = "UPDATE "+table +" SET "+str.join(",",sqlArr)+" WHERE "+where
            return self.execute(sql)
        except Exception, e:
            self.sql_error(sql, e)
            return False

    def insert_update(self, table, arr, arr_check):
        '''存在则更新，不存在则插入'''
        assert type(arr) is dict, 'arr must be a dict'
        assert type(arr_check) is dict, 'arr_check must be a dict'

        CheckClause = ' AND '.join([(str(item[0]) + '=' + '"%s"' % item[1]) \
                                for item in arr_check.iteritems()])
        stat = self.out_field(table, 'count(1)', CheckClause)
        if stat is False:
            return False
        if stat:
            #update_arr = dict(list(set(arr.items() + arr_check.items())))
            update_arr = dict(list(set(arr.items()) - set(arr_check.items())))
            return self.update(table, update_arr, CheckClause) 
        return self.insert(table, arr)
    
    def delete(self,table,where):
        '''删除记录 '''
        sql = "DELETE FROM "+table+" WHERE "+where
        return self.execute(sql)

    def count(self,table,where='1'):
        '''获取数量 @return int'''
        return self.out_field(table,'count(1)',where)

    def out_field(self,table,field,where='1'):
        '''field是列名,返回一个值'''
        try:
            sql = "SELECT "+field+" FROM "+table+" WHERE "+where
            row = self.fetchone(sql)
            if not row:
                return None
            return row.get(field)
        except Exception, e:
            self.sql_error(sql,e)
            return False
    
    def out_fields(self,table,fields,where):
        '''
        #@todo 改名为out_row
        fields是一个列表,包含列名,返回一个字典
        return value:False-执行sql时出错。None-没有从数据库中查出记录。dict-从数据库中读出的记录。
        '''
        try:
            if not isinstance(fields, (list, tuple)):
                fields = [fields]
            
            sql = "SELECT "+str.join(",",fields)+" FROM "+table+" WHERE "+where
            row = self.fetchone(sql)
            return row
        except Exception,e:
            self.sql_error(sql,e)
            return False
    
    def out_list(self,table,field,where='1',distinct=False):
        ''' 查询所有满足条件的多行中的field(有相同或不同) 组成一个列表 
        @return list
        @example:
        out_list('tb_general1','GeneralType','UserId=%s',True) #获取我的武将类型列表
        out_list('tb_building1','BuildingId','BuildingType=5') #获取我的类型为5的所有建筑ID列表
        '''
        try:
            if distinct: 
                field = "DISTINCT("+field+")"
            sql = "SELECT "+field+" FROM "+table+" WHERE "+where
            rows = self.fetchall(sql)
            rlist = []
            for row in rows:
                rlist.append(row.get(field))
            return rlist
        except Exception, e:
            self.sql_error(sql,e)
            return []

    def out_rows(self,table,fields,where='1'):
        '''返回值：False（出错），由字典组成的元组（查询结果），空元组（查询到0条记录）'''
        try:
            if not isinstance(fields, (list, tuple)):
                fields = [fields]

            sql = "SELECT "+str.join(",",fields)+" FROM "+table+" WHERE "+where
            return self.fetchall(sql)
        except Exception, e:
            self.sql_error(sql,e)
            return False

    def out_rand(self, table, fields='*', where='1', n=1):
        '''从表中随机选取n条记录'''
        line_cnt = self.count(table,where)
        start = randint(0, line_cnt - n) if line_cnt > n else 0
        where = '%s LIMIT %s, %s' % (where, start, n)
        if n>1:
            return self.out_rows(table, fields, where)
        else:
            return self.out_fields(table, fields, where)
    
    def inWhere(self,field,inList,notIn=False):
        '''in 或 not in 条件封装 
        @param field: 字段
        @param inList: 列表 
        @param notIn: 是否在
        @return string 条件字符串
        @example:
        inWhere('id',[1,2,3])  >> id in ('1','2','3')
        inWhere('Name',['a','b','c'])  >> Name in ('a','b','c')
        '''
        assert isinstance(field, str)
        assert isinstance(inList, (list,tuple))
        inList = [str(cell) for cell in inList]
        if notIn:
            where = field+" NOT IN ('"+str.join("','",inList)+"')"
        else:
            where = field+" IN ('"+str.join("','",inList)+"')"
        return where

    def escape_string(self,s):
        '''有时间测试的话 改为用pymysql 不想再装MySQLdb模块'''
        return MySQLdb.escape_string(s) #不能使用umysqldb.escape_string() 有区别 待优化

    def pymysql_escape_string(self,s):
        '''这是从pymysql拿过来的 ,改了默认添加的单引号  "'%s'" => "%s"'''
        import re
        ESCAPE_REGEX = re.compile(r"[\0\n\r\032\'\"\\]")
        ESCAPE_MAP = {'\0': '\\0', '\n': '\\n', '\r': '\\r', '\032': '\\Z',
                  '\'': '\\\'', '"': '\\"', '\\': '\\\\'}
        return ("%s" % ESCAPE_REGEX.sub(
                lambda match: ESCAPE_MAP.get(match.group(0)), s))
        
    def sql_error(self,sql,err_msg=None,err_sign=None):
        print '-'*50
        print 'sql_error: >>> ',sql
        print err_msg,err_sign
        print '-'*50
        import time
        from sgLib.core import Gcore 
        if Gcore.IsServer : #只服务器模式才记录错误日志
            now = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
            #---------暂都保存多条 note表已删-----------
#            if Gcore.TEST:
#                try:
#                    sqllog = "INSERT INTO temp_sqlerror_logall (MySQL,MySQLError,RecordTime) VALUES('%s','%s','%s')"\
#                    %(self.escape_string(sql),self.escape_string(str(err_msg)),now)
#                    con,cursor = self._create()
#                    cursor.execute(sqllog)  #此处不能用self.execute否则出错会循环调用
#                    con.commit()
#                    self._close(con,cursor)
#                except:
#                    print 'sql_error: >>>  logall error',sqllog
            #---------暂都保存多条-----------
            
            try:
                sqllog = "INSERT INTO temp_sqlerror_log (MySQL,MySQLError,RecordTime)  VALUES ('%s','%s','%s')"%(self.escape_string(sql),self.escape_string(str(err_msg)),now)
                sqllog += " ON DUPLICATE KEY UPDATE ApearTimes=ApearTimes+1,RecordTime='%s'"%now
                from sgLib.core import Gcore
                Gcore.sqldelay(sqllog)
            except:
                print 'sql_error: >>>  sql_error delay',sqllog
        
        
        
if __name__ == '__main__':
    '''测试'''
    import gevent
    import time
    import sys
    import random
    db = DB()
    print '-'*100
    db.execute('test sql')
#    info = [('val1','val2',{1:2,2:3,3:4,4:5}), ('val3','val4',{1:0,2:1,3:2},'val1')] #,5:6
#    where = 'id in (1,2,3,4)'
#    db.updatemany('_test2',info,where)

    #sql = 'insert into tb_mission(Status, MissionId, UserId, GetValue, CreateTime, CompleteTime) values("%s", "%s", "%s", "%s", "%s", "%s")'
    #db.execute(sql,[3, 1164, 43415, 3, 1371781255, 1371781255])
    
    #args = [[3, 1164, 43415, 3, 1371781255, 1371781255], [3, 1165, 43415, 3, 1371781255, 1371781255], [1168, 1, 43415, 1371781255, 0]]
    #db.executemany(sql, args)
#    for arg in args:
#        print arg
#        db.execute(sql, arg)
    ''' #协程测试
    def test(i):
        #print db.query("SELECT * FROM tb_user order by rand() limit 0 ,1")
        #print db.execute("SELECT * FROM tb_user order by rand() limit 0 ,1")
        #print db.fetchall("SELECT * FROM tb_user order by rand() limit 0 ,1")
        #print db.fetchone("SELECT * FROM tb_user order by rand() limit 0 ,1")
        #print db.executemany("insert into _test2(val) values(%s)",[1,2,3,4,5])
        #print db.insert('_test2',{'val':100})
        #print db.insertmany('_test2', [{'val':101},{'val':102},{'val':103}])
        #print db.update('_test2',{'val':i},'id=4')
        i +=1
        #print db.insert_update('_test2', {'id':i,'val':100}, {'id':i})
        #print db.delete('_test2','id=%s'%i)
        #print db.count("_test2")
#        s = random.randint(1,4)
#        gevent.sleep(s)
#        print '%s,%s'%(i,db.out_field('_test', 'val', 'id=%s'%i) )
#        j = i+random.randint(1,4)
#        print '%s,%s'%(j,db.out_field('_test', 'val', 'id=%s'%j) )
#        k= i+random.randint(1,4)
#        print '%s,%s'%(k,db.out_fields('_test', '*', 'id=%s'%k) )
        print db.out_fields('_test', '*', 'id=%s'%i)
        #print db.out_list('_test2', 'val')
        #print db.out_rows('_test2','*')
        #print db.out_rand('_test2','*')
        #print db.inWhere('id', [1,2,3])
    chs = []
    for i in xrange(2000):
        chs.append(gevent.spawn(test,i))
    gevent.joinall(chs)
    '''
    time.sleep(100)
