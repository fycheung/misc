#coding:utf8
#author:zhoujingjiang
#将用户表导入到redis

import pyDB
import pyCache
import config

redis = pyCache.getConn()

server_id = 2#config.SERVER_ID
server_group = config.SERVER_GROUP
limit_cnt = config.LIMIT_COUNT
fields = ['UserId','UserCamp','UserIcon',\
          'UserLevel', 'VipLevel']
cnt = 0

while 1:
    print '第%s次循环' % (cnt+1)
    start, n = cnt * limit_cnt, limit_cnt - 1
    rows = pyDB.out_rows('tb_user', fields, '1 LIMIT %s,%s' % (start, n))

    if len(rows) == 0:
        break

    for row in rows:
        UserId = row.pop('UserId')
        k = 'sgUser.%s.%s' % (UserId, server_id)
        v = row
        redis.set(k, v)
        
        lv = row.pop('UserLevel')
        camp = row.pop('UserCamp')
        k = 'sgGrep.%s.%s.%s.%s.%s' % (server_group, UserId, server_id, lv, camp)
        v = row
        redis.set(k, v)
    cnt += 1
#end while
