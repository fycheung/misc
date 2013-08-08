# -*- coding:utf-8 -*-  
# author:Lizr
# date:2013-6-7
# 清档工具,开服时用,小心使用


import umysqldb
# 初始化
conn = umysqldb.connect(host='10.1.1.18', port=3306, user='gamesg', passwd='1231234', db='gamesg2')
cur = conn.cursor()
cur.execute("show tables")
tables = cur.fetchall()
for table in tables:
    table = table[0]
    if table.startswith('tb_cfg_'):
        continue
    elif table in ('tb_config','tb_config_core'):
        continue
    else:
        cur.execute("truncate table %s"%table)
cur.execute('ALTER TABLE  `tb_user` AUTO_INCREMENT =1001')
conn.commit()    


# 将开发网的拆分2表 扩展成10表
cur.execute("show tables")
result = cur.fetchall()
alltables = [r[0] for r in result]

#必需要检查有没有少表
ten_list = ['tb_bag','tb_building','tb_general','tb_wall_defense','tb_equip']
for t in ten_list:
    for i in xrange(2,10):
        tb = '%s%s'%(t,i)
        if tb not in alltables:
            sql = 'CREATE TABLE %s LIKE %s0'%(tb,t)
            try:
                cur.execute(sql)
            except:
                pass

conn.commit()  
print 'add 10 table finish'


print 'inited finish'

