# -*- coding:utf-8 -*-
# author:zhoujingjiang
# date:2013-2-25
# 游戏内部接口:理藩院

import time
import datetime
import random

from sgLib.base import Base
from sgLib.core import Gcore

class Building_holdMod(Base):
    '''理藩院模型'''
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
        self.serverid = int(Gcore.getServerId())
    
    def getMyHolder(self):
        '''获取我的主人信息,主要用于我是否是自由身'''
        table = 'tb_user'
        fields = ['HolderId', 'HolderServerId']
        where = 'UserId="%s" AND HolderId!=0 AND HolderServerId!=0 AND HoldEndTime>UNIX_TIMESTAMP()' % self.uid
        res = self.db.out_fields(table, fields, where)
        return res
            
    def getHolder(self, uid=None, sid=None, flag=True):
        '''获取主人：flag-True 需要主人信息， False 不需要主人信息'''
        #返回值：主人UserId，主人分服ID [，主人信息]。或None。
        uid = self.uid if not uid else uid
        sid = self.serverid if not sid else sid
        
        PeerUID, PeerSID = None, None
        if sid == self.serverid: #本服从MySQL查询。
            table = 'tb_user'
            fields = ['HolderId', 'HolderServerId', 'HoldEndTime']
            where = 'UserId="%s" AND HolderId!=0 AND HolderServerId!=0 AND HoldEndTime>UNIX_TIMESTAMP()' % uid
            res = self.db.out_fields(table, fields, where)
            if not res:
                return None
            PeerUID, PeerSID = res["HolderId"], res["HolderServerId"]
        else: #非本服从总服redis查
            holder = Gcore.redisM.hget('sgHold', '%s.%s' % (sid, uid))
            if not holder:
                return None
            try:
                fields = holder.split('.')
                PeerUID, PeerSID = int(fields[0]), int(fields[1])
            except Exception, e:
                print '一条错误的藩国记录:%s' % str(e)
                # 删除 ？
        
        
        holderInfo = {'hServerId':PeerSID, 'hUserId':PeerUID}
        
        if flag:
            #主人信息
            if PeerSID == self.serverid: #主人在本服，从mysql查。
                table = 'tb_user'
                fields = ['UserId','NickName','UserCamp','UserIcon','UserLevel','VipLevel']
                where = 'UserId="%s"' % PeerUID
                mi = self.db.out_fields(table, fields, where)
            else: #主人不在本服从总服redis查
                mi = Gcore.redisM.hget("sgUser", "%s.%s"%(PeerSID, PeerUID))
            
            holderInfo['hNickName'] = mi.get('NickName')
            
        return holderInfo
       
    def getDefeaters(self, TimeStamp=None):
        '''获取手下败将'''
        TimeStamp = TimeStamp if TimeStamp else time.time()
        HoldConfig = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_HOLD)
        ExpireTime = HoldConfig["ExpireTime"] #过期时间
        LimitCnt = HoldConfig["LimitCount"] #手下败将的最大个数
        
        table = 'tb_battle_record'
        fields = ['PeerUID', 'PeerSID', 'PeerName', 'PeerVipLevel',
                  'PeerCamp', 'PeerIcon', 'PeerLevel', 'MAX(CreateTime) as CreateTime']
        where = """UserId="%s" AND BattleResult=1 AND CreateTime>="%s" AND
                   BattleType=1
                 GROUP BY UserId, PeerUID, PeerSID LIMIT %s""" \
                % (self.uid, TimeStamp - ExpireTime, LimitCnt)
        res = self.db.out_rows(table, fields, where)
        return res   
    
    def delDefeater(self, PeerUID, PeerSID):
        '''删除一个手下败将：设置别人为藩国时，需要删除该手下败将'''
        sql = '''DELETE FROM tb_battle_record 
                 WHERE UserId="%s" AND PeerUID="%s" AND PeerSID="%s" 
              ''' % (self.uid, PeerUID, PeerSID)
        res = self.db.execute(sql)
        print '删除手下败将', res
        return res       
        
    def setHold(self, PeerUID, PeerSID):
        '''设置别人成为藩国'''
        #根据配置得出自动解除的天
        HoldConfig = Gcore.loadCfg(Gcore.defined.CFG_BUILDING_HOLD)
        RemoveRatio = HoldConfig['RemoveRatio']
        d = None
        for ind in range(1, len(RemoveRatio) + 1, 1):
            r = random.random()
            if  r <= RemoveRatio[str(ind)]:
                d = ind
                break

        #初始化元数据
        BeginTime = int(time.time()) #开始时间
        EndTime = BeginTime + int(d * 24 * 60 * 60) #预计结束时间（自动解除时间）
        # + StopTime是真正结束的时间：默认是EndTime
        # + LastCollectTime是最近一次奴隶的自动收集资源时间
        StopTime, LastCollectTime = EndTime, BeginTime    
        Jcoin, Gcoin = 0, 0 #奴隶的贡献
        
        print '是否是本服', PeerSID == self.serverid, PeerSID, self.serverid
        if PeerSID == self.serverid: #本服
            print '本服'
            # + 更新用户表
            arr = {'HolderId':self.uid,'HolderServerId':self.serverid,'HoldEndTime':EndTime}
            self.db.update('tb_user', arr, 'UserId=%s' % PeerUID)
            # + 插入本服藩国记录
            arr = {"HolderId":self.uid, "GiverId":PeerUID, "LastCollectTime":LastCollectTime,
                   "JcoinGive":Jcoin, "GcoinGive":Gcoin, "StopTime":StopTime, 
                   "BeginTime": BeginTime, "EndTime":EndTime}
            self.db.insert('tb_hold', arr)
            print self.db.sql
            # + 插入纳贡记录
            arr = {"UserId":PeerUID, "HolderId":self.uid, "Gcoin":0,
                   "HolderServerId":self.serverid, "Jcoin":0, "LastGiveTime":BeginTime}
            self.db.insert('tb_hold_log', arr)
            # + 插入藩国反抗记录
            date = datetime.date.strftime(datetime.date.fromtimestamp(BeginTime), "%Y-%m-%d")
            arr = {"UserId":PeerUID, "HolderId":self.uid, "HolderServerId":self.serverid,
                   "ProcessTotal":0, "RevengeCount":0, "LastRevengeDate":date}
            self.db.insert('tb_hold_revenge', arr)
        else: #非本服，发消息
            Gcore.sendmq(1, PeerSID, {'HolderId':self.uid,
                                      'HolderServerId':self.serverid,
                                      'GiverId':PeerUID,
                                      'EndTime':int(EndTime)})
        k = '%s.%s' % (PeerSID, PeerUID)
        v = '%s.%s.%s.%s.%s.%s.%s.%s' % (self.serverid, self.uid, BeginTime, StopTime, EndTime, LastCollectTime, Jcoin, Gcoin)
        Gcore.redisM.hset('sgHold', k, v)
        #Gcore.redisM.hset('sgHoldJcoin', k, 0)
        #Gcore.redisM.hset('sgHoldGcoin', k, 0)
        return True
        
    def getHold(self):
        '''获取藩国列表'''
        #获取在本服的藩国-从tb_user表中查
        table = 'tb_user'
        fields = ['UserId', 'NickName', "UserLevel", "VipLevel", 'UserCamp', 'UserIcon']
        where = 'HolderId="%s" AND HolderServerId="%s"' % (self.uid, self.serverid)
        res = self.db.out_rows(table, fields, where)
        if not isinstance(res, tuple):
            return False
        
        #获取跨服的藩国
        hold_records = Gcore.redisM.hgetall('sgHold')
        for giver in hold_records:
            try:
                giver_server_id, giver_id = map(int, giver.split('.'))
                if giver_server_id == self.serverid: #本服的忽略
                    continue
                
                info = Gcore.common.json_decode(hold_records[giver])
                fields = info.split('.')
                if int(info[0]) != self.serverid or \
                    int(info[1]) != self.uid: #不是我的藩国
                    continue
                try:
                    mui = Gcore.redisM.hget("sgUser", '1.1001', True)
                    assert isinstance(mui, dict)
                except Exception:
                    mui = {}
                mui['UserId'] = giver_id
                mui['ServerId'] = giver_server_id
                res += (mui, )
            except Exception:
                pass
        return res
    
    def isMyHold(self, uid, sid):
        '''判断是否是我的藩国'''
        #如果是我的藩国，返回（可纳贡的军资，可纳贡的铜币），否则返回False
        if sid == self.serverid:#本服
            table = 'tb_hold'
            fields = ['JcoinGive', 'GcoinGive']
            where = 'HolderId="%s" AND GiverId="%s"' % (self.uid, uid)
            res = self.db.out_fields(table, fields, where)
            return False if not res else (res["JcoinGive"], res["GcoinGive"])
        else: #跨服
            try:
                info = Gcore.redisM.hget('sgHold', '%s.%s' %(sid, uid))
                if not info:
                    return False
                fields = info.split('.')
                return (int(fields[6]), int(fields[7]))
            except Exception, e:
                print str(e)
                return False
    
    def freed(self, huid, hsid): #玩家达到一定要求，被释放。
        '''被释放'''
        if hsid == self.serverid: #占领者在本服
            #查出进贡的钱
            row = self.db.out_fields('tb_hold', ["JcoinGive", "GcoinGive"],\
                               'GiverId="%s" AND HolderId="%s"'%(self.uid, huid))
            if not row:
                return -1
            ja, ga = row["JcoinGive"], row["GcoinGive"]
            
            modCoin = Gcore.getMod('Coin', huid)
            j = modCoin.GainCoin(0, 2, ja, 'Building_holdMod.freed', {'hsid':hsid, 'huid':huid})
            g = modCoin.GainCoin(0, 3, ga, 'Building_holdMod.freed', {'hsid':hsid, 'huid':huid})
            if j < -1 or g < -1:
                return -2 #占领者收钱失败
            dic = {'HolderId':0,'HolderServerId':0,'HoldEndTime':0}
            self.db.update('tb_user', dic, 'UserId="%s"' % self.uid)
            self.db.execute('DELETE FROM `tb_hold` WHERE GiverId="%s" AND HolderId="%s"' % (self.uid, huid))
            self.db.execute('DELETE FROM `tb_hold_log` WHERE UserId="%s"' % self.uid)
            self.db.execute('DELETE FROM `tb_hold_revenge` WHERE UserId="%s"' % self.uid)
        else: #占领者不在本服
            Gcore.sendmq(3, hsid, {'HolderId':huid,
                          'GiverServerId':self.serverid,
                          'GiverId':self.uid})
        return 1
  
    def free(self, uid, sid, ts=None):
        '''释放'''
        if self.serverid == sid: #本服
            dic = {'HolderId':0,'HolderServerId':0,'HoldEndTime':0}
            self.db.update('tb_user', dic, 'UserId="%s"' % uid)
            self.db.execute('DELETE FROM `tb_hold` WHERE GiverId="%s" AND HolderId="%s"' % (uid, self.uid))
            self.db.execute('DELETE FROM `tb_hold_log` WHERE UserId="%s"' % uid)
            self.db.execute('DELETE FROM `tb_hold_revenge` WHERE UserId="%s"' % uid)
        else: #非本服
            Gcore.sendmq(2, sid, {'GiverId':uid})
        Gcore.redisM.hdel("sgHold", '%s.%s' % (sid, uid))
        return True 
        
    def collect(self, uid, sid, jr, gr, ts):
        '''纳贡'''
        if sid == self.serverid: #本服
            arr = {'JcoinGive':jr, "GcoinGive":gr}
            self.db.update('tb_hold', arr, 'HolderId="%s" AND GiverId="%s"' % (self.uid, uid))
        else: #非本服,更新总服redis
            try:
                v = Gcore.redisM.hget("sgHold", '%s.%s' % (sid, uid))
                if not v:
                    return False
                fields = v.split('.')
                fields[6], fields[7] = jr, gr
                print 'fields', fields
                v = '.'.join(map(str, fields))
                return Gcore.redisM.hset('sgHold', '%s.%s' % (sid, uid), v)
            except Exception, e:
                print str(e)
                return False
        return True
    
    def getRevent(self):
        '''获取反抗次数'''
        return self.db.out_fields('tb_hold_revenge', '*', 'UserId="%s"'%self.uid)
    
    def calcRevent(self, TimeStamp=None):
        '''计算当天的反抗次数，反抗进度'''
        TimeStamp = TimeStamp if TimeStamp else time.time()
        rel = self.getRevent()
        if rel is None \
           or rel["LastRevengeDate"] != datetime.date.fromtimestamp(TimeStamp):
            return (0, 0)
        else:
            return (rel["RevengeCount"], rel["ProcessTotal"])
    
    def setReventProcess(self, process, flag=0, TimeStamp=None):
        '''设置反抗进度:process-攻城进度；flag-0失败，1成功'''
        #返回值：-2 反抗次数已达到最大 -1 参数错误  0 没达到成功条件 1达到成功条件
        if not 0 <= process <=1:
            return -1 #攻城进度取值范围不对
        TimeStamp = TimeStamp if TimeStamp else time.time()
        cnt, pro = self.calcRevent(TimeStamp)
        ratio = 0.5 #读配置
        maxnum = 5 #读配置
        
        cnt_new = cnt + 1
        pro_new = pro + float(ratio * process) #取攻城进度的50%。
        if cnt_new > maxnum:
            return -2
        elif pro_new >= 1.0 or flag == 1: #累积进度达到100% ## 读配置
            self.db.execute('DELETE FROM `tb_hold_revenge` WHERE UserId="%s"'%self.uid)
            return 1
        else: #增加累计进度
            arr = {}
            arr['ProcessTotal'] = pro_new
            arr['RevengeCount'] = cnt_new
            arr['LastRevengeDate'] = datetime.date.strftime(
            datetime.date.fromtimestamp(TimeStamp), '%Y-%m-%d')
            self.db.update('tb_hold_revenge', arr, 'UserId="%s"'%self.uid)
#end class Building_holdMod

if '__main__' == __name__:
    uid = 1006
    c = Building_holdMod(uid)
    #print c.setReventProcess(0.36)
    print type(Gcore.getServerId())