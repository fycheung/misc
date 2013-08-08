#coding:utf8
from __future__ import division
from gevent import monkey; monkey.patch_all()

from os.path import dirname,abspath
system_root = dirname(dirname( abspath( __file__ ) ) ) #定义上层目录为根目录 
import sys;sys.path.insert(0,system_root)  #把项目根目录加入默认库路径 

import time
from sgLib.core import Gcore

tb_num = Gcore.config.TBNUM

limit_cnt = 1000
cnt = 0
curtime = time.time()
send_conn = None

db = Gcore.getDB()
GiveRatio = Gcore.loadCfg(1506).get('GiveRatio',0.05)
#if Gcore.TEST:
#    GiveRatio = 1
while 1:
    print '第%s次循环' % (cnt+1)
    start, n = cnt * limit_cnt, limit_cnt - 1
    table = 'tb_user'
    fields = ['HoldEndTime', 'HolderServerId', 'HolderId', "UserId"]
    if Gcore.TEST and 0: #指定用户测试 暂时
        where = 'HolderId != 0 AND UserId IN (1005) LIMIT %s,%s' % (start, n)
    else:
        where = 'HolderId != 0 LIMIT %s,%s' % (start, n)
    rows = db.out_rows(table, fields, where)
    if not rows:
        break

    UserIds = [row["UserId"] for row in rows]
    #计算生产速度 = 基础生产速度 + 内政加成
    for ind in range(0, tb_num):
        uids = [UserId for UserId in UserIds if UserId%tb_num == ind]
        
        if not uids:
            continue
        
        table = 'tb_building%s' % ind
        fields = ['UserId', 'BuildingType', 'BuildingLevel', 'CompleteTime']
        where = '(BuildingType=2 OR BuildingType=5) AND (UserId=' + \
        ' OR UserId= '.join(map(str, uids)) + ')'
        rows1 = db.out_rows(table, fields, where)
        if not rows1:
            continue
        
        #内政加成
        dictInters = Gcore.getMod('Inter',1).getInter(uids, curtime)
        
        #生产速度
        Speed = {}
        for row in rows1:
            uid, typ, lv, ct = row["UserId"], row["BuildingType"], \
            row["BuildingLevel"], row["CompleteTime"]
            if ct > curtime:
                lv -= 1
                if lv <= 0:
                    continue
            #读取配置
            hourvalue = Gcore.getCfg('tb_cfg_building_up',(typ, lv), 'HourValue')
            
            u = Speed.setdefault(uid, {})
            cointype = 2 if typ == 5 else 1
            u[cointype] = u.get(cointype, 0) + hourvalue * \
                          (1 + (dictInters.get(uid, {}).get(cointype, 0)))
        print 'Speed', Speed

        #本服进贡表
        table, fields = 'tb_hold', ['LastCollectTime', 'EndTime', 'GiverId', \
                                    'JcoinGive', 'GcoinGive']
        where = 'GiverId=' + ' OR GiverId= '.join(map(str, uids))
        rows2 = db.out_rows(table, fields, where)
        print 'aaa',db.sql
        tmplst = []
        incdic = {}
        if rows2:
            for row in rows2:
                print 'curtime',curtime
                print 'EndTime',row['EndTime']
                print 'min()',min(curtime, row['EndTime'])
                print 'LastCollectTime',row['LastCollectTime']
                seconds = min(curtime, row['EndTime']) - row['LastCollectTime']
                
                if seconds<0:
                    continue
                
                print 'seconds',seconds
                jc = seconds * (Speed.get(row['GiverId'], {}).get(1, 0) / 3600.) * GiveRatio
                gc = seconds * (Speed.get(row['GiverId'], {}).get(2, 0) / 3600.) * GiveRatio
             
                #j = row['JcoinGive'] + jc
                #g = row['GcoinGive'] + gc
                tmplst.append([row['GiverId'], jc, gc])
                incdic[row["GiverId"]] = {1:jc,2:gc}
            # + 更新本服进贡表
            j, g = ' CASE GiverId ', ' CASE GiverId'
            for lst in tmplst:
                j += ' WHEN %d THEN %d ' % (lst[0], lst[1])
                g += ' WHEN %d THEN %d ' % (lst[0], lst[2])
            j += ' END '; g += ' END '
            sql = 'UPDATE %s SET JcoinGive=JcoinGive+%s, GcoinGive=GcoinGive+%s, LastCollectTime=%d WHERE %s' % (table, j, g, int(curtime), where)
            print '进贡记录：',sql
            db.execute(sql)
        
        #总服redis
        redis_client = Gcore.redisM
        holds = redis_client.hgetall('sgHold')
        #print 'holds', holds
        for giver in holds:
            #print 'giver is', giver
            try:
                sid, uid = map(int, giver.split('.'))
                if sid != Gcore.getServerId(): #奴隶不是本服的
                    continue
                v_fields = map(int, holds[giver].split('.'))
                #print 'fields', fields
                if v_fields[0] == Gcore.getServerId():
                    continue
                
                endtime, lastcollecttime = v_fields[4:]
                seconds = int(min(endtime, curtime) - lastcollecttime)
                jc = int(seconds*(Speed.get(uid, {}).get(1, 0) / 3600.))
                gc = int(seconds*(Speed.get(uid, {}).get(2, 0) / 3600.))
                print 'jc', jc, 'gc',gc

                incdic[uid]={1:jc,2:gc}

                v = '.'.join(map(str, v_fields[0:5] + [int(curtime)]))
                redis_client.hset('sgHold', giver, v)
                
                #by Lizr
                key = Gcore.redisKey(uid)+'%s.%s'%(v_fields[0],v_fields[1])
                redis_client.hincrby('sgHoldJcoin',key,jc)
                redis_client.hincrby('sgHoldGcoin',key,gc)
                
            except Exception, e:
                print 'error', e
                raise

        #进贡记录
        table = 'tb_hold_log'
        where = 'UserId=' + ' OR UserId= '.join(map(str, uids))
        jstr = 'CASE UserId '
        gstr = ' CASE UserId'
        for UserId in uids:
            jstr += ' WHEN %d THEN %d' % (UserId, incdic.get(UserId, {}).get(1, 0))
            gstr += ' WHEN %d THEN %d' % (UserId, incdic.get(UserId, {}).get(2, 0))
        jstr += ' END '
        gstr += ' END '
        sql = 'UPDATE tb_hold_log SET Jcoin = Jcoin+%s, Gcoin = Gcoin+%s, LastGiveTime="%s" WHERE %s' \
                % (jstr, gstr, curtime, where)
        db.execute(sql)
        print '进贡日志:',sql
        
    #自动解除关系 (前台自己到时间，请求接口，自动更新资源情况)
    for row in rows:
        if row["HoldEndTime"] > curtime + 600: #提前10分钟释放
            continue
        if row["HolderServerId"] == Gcore.getServerId(): #本服
            ui = Gcore.getUI('Building_hold', row["HolderId"])
            ui.SlaveOperand({'typ':2, 'uid':row["UserId"], 'sid':Gcore.getServerId()})
        else: #非本服，发消息
            msg = {'HolderId':row["HolderId"], "GiverId":row["UserId"], "GiverServerId":Gcore.getServerId()}
            Gcore.sendmq(3, int(row["HolderServerId"]), msg)
    cnt += 1

runtime = time.time()-curtime
print 'Finish at:',Gcore.common.now()
print 'Total Runtime:', runtime