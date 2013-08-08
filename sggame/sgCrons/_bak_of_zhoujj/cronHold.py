#coding:utf8

from gevent import monkey; monkey.patch_all()

import time
import sys

import amqp

import config
import pyDB
import pyCache
from sgLib.core import Gcore
import sgMod.subMod.InterMod as mod_inter

tb_num = 2
limit_cnt = 1000
cnt = 0
curtime = time.time()
send_conn = None
exchange_num = config.EXCHANGE_NUM

BuildingUpCfg = {}
for row in pyDB.out_rows('tb_cfg_building_up'):
    BuildingUpCfg[(row['BuildingType'], row['Level'])] = row

def getCfg(PrimaryKey, field=None):
    '''获取建筑升级配置'''
    row = BuildingUpCfg.get(PrimaryKey)
    if row is None:
        return None
    if not field:
        return row
    if not isinstance(field, basestring):
        raise TypeError, 'argument field should be basesting.'
    return row.get(field)

def ensure_conn(conn):
    '''指定连接获取channel'''
    if not isinstance(conn, amqp.connection.Connection) \
        or not conn.is_alive():
        try:
            conn = amqp.Connection(host=config.MQ_HOST, userid=config.MQ_UID, \
                       password=config.MQ_PWD, virtual_host=config.MQ_VHOST, insit=False)
            return conn.channel()
        except Exception, e:
            conn = None
            print >>sys.stderr, str(e)
            return False
    else:
        for k in conn.channels:
            if isinstance(conn.channels[k], amqp.channel.Channel):
                return conn.channels[k]
        return conn.channel()

while 1:
    print '第%s次循环' % (cnt+1)
    start, n = cnt * limit_cnt, limit_cnt - 1
    table = 'tb_user'
    fields = ['HoldEndTime', 'HolderServerId', 'HolderId', "UserId"]
    where = 'HolderId != 0 LIMIT %s,%s' % (start, n)
    rows = pyDB.out_rows(table, fields, where)

    if not rows:
        break
    print 'rows', rows

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
        print 'where', where
        rows1 = pyDB.out_rows(table, fields, where)
        print 'rows1', rows1
        if not rows1:
            continue
        
        #内政加成
        dictInters = mod_inter.InterMod(1).getInter(uids, curtime)
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
            hourvalue = getCfg((typ, lv), 'HourValue')
            
            u = Speed.setdefault(uid, {})
            cointype = 2 if typ == 5 else 1
            u[cointype] = u.get(cointype, 0) + hourvalue * \
                          (1 + (dictInters.get(uid, {}).get(cointype, 0)))
        print 'Speed', Speed

        #本服进贡表
        table, fields = 'tb_hold', ['LastCollectTime', 'EndTime', 'GiverId', \
                                    'JcoinGive', 'GcoinGive']
        where = 'GiverId=' + ' OR GiverId= '.join(map(str, uids))
        rows2 = pyDB.out_rows(table, fields, where)
        
        tmplst = []
        incdic = {}
        if rows2:
            for row in rows2:
                seconds = min(curtime, row['EndTime']) - row['LastCollectTime']
                jc = seconds * (Speed.get(row['GiverId'], {}).get(1, 0) / 3600.)
                gc = seconds * (Speed.get(row['GiverId'], {}).get(2, 0) / 3600.)
                j = row['JcoinGive'] + jc
                g = row['GcoinGive'] + gc
                tmplst.append([row['GiverId'], j, g])
                incdic[row["GiverId"]] = {1:jc,2:gc}
            # + 更新本服进贡表
            j, g = ' CASE GiverId ', ' CASE GiverId'
            for lst in tmplst:
                j += ' WHEN %d THEN %d ' % (lst[0], lst[1])
                g += ' WHEN %d THEN %d ' % (lst[0], lst[2])
            j += ' END '; g += ' END '
            sql = 'UPDATE %s SET JcoinGive=%s, GcoinGive=%s, LastCollectTime=%d WHERE %s' % (table, j, g, int(curtime), where)
            pyDB.execute(sql)
        
        #总服redis
        redis_client = pyCache.getConn()
        holds = redis_client.hgetall('sgHold')
        print 'holds', holds
        for giver in holds:
            print 'giver is', giver
            try:
                sid, uid = map(int, giver.split('.'))
                if sid != config.SERVER_ID: #奴隶不是本服的
                    continue
                v_fields = map(int, holds[giver].split('.'))
                print 'fields', fields
                if v_fields[0] == config.SERVER_ID:
                    continue
                
                endtime, lastcollecttime, j, g = v_fields[4:]
                seconds = int(min(endtime, curtime) - lastcollecttime)
                jc = int(seconds*(Speed.get(uid, {}).get(1, 0) / 3600.))
                gc = int(seconds*(Speed.get(uid, {}).get(2, 0) / 3600.))
                print 'jc', jc, 'gc',gc
                j += jc
                g += gc
                print 'j', j, 'g', g
                incdic[uid]={1:jc,2:gc}

                v = '.'.join(map(str, v_fields[0:5] + [int(curtime), j, g]))
                redis_client.hset('sgHold', giver, v)
            except Exception, e:
                print 'error', e
                raise

        #纳贡记录
        table = 'tb_hold_log'
        fields = ['UserId', 'Jcoin', 'Gcoin']
        where = 'UserId=' + ' OR UserId= '.join(map(str, uids))
        rows3 = pyDB.out_rows(table, fields, where)
        
        if rows3:
            jstr = 'CASE UserId '
            gstr = ' CASE UserId'
            for row in rows3:
                jstr += ' WHEN %d THEN %d' % (row["UserId"], incdic.get(row["UserId"], {}).get(1, 0) + row["Jcoin"])
                gstr += ' WHEN %d THEN %d' % (row["UserId"], incdic.get(row["UserId"], {}).get(2, 0) + row["Gcoin"])
            jstr += ' END '
            gstr += ' END '
            sql = 'UPDATE tb_hold_log SET Jcoin=%s, Gcoin=%s, LastGiveTime="%s" WHERE %s' \
                    % (jstr, gstr, curtime, where)
            pyDB.execute(sql)
        
    #自动解除关系
    for row in rows:
        if row["HoldEndTime"] > curtime:
            continue
        if row["HolderServerId"] == config.SERVER_ID: #本服
            ui = Gcore.getUI('Building_hold', row["HolderId"])
            ui.SlaveOperand({'typ':2, 'uid':row["UserId"], 'sid':config.SERVER_ID})
        else: #非本服，发消息
            try:
                msg = {'HolderId':row["HolderId"], "GiverId":row["UserId"], "GiverServerId":config.SERVER_ID}
                msg['optId'] = 3
                msg = str(msg)
                message = amqp.Message(msg)
                message.properties['delivery_mod'] = 2
                s2e = int(row["HolderServerId"])%exchange_num
                if not s2e:
                    s2e = exchange_num
                
                chan = ensure_conn(send_conn)
                chan.basic_publish(message, exchange='sggameexchange%d'%s2e, routing_key=str(row["HolderServerId"]))
                
            except Exception:
                #将队列插入数据库  @todo待测试
                db = Gcore.getNewDB()
                dic = {
                       'msg':msg,
                       'CreateTime':Gcore.common.nowtime(),
                       }
                result = db.insert('tb_delay_mq',dic)
                db.close()
    cnt += 1
