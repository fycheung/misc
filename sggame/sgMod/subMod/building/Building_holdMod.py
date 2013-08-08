# -*- coding:utf-8 -*-
# author:zhoujingjiang
# date:2013-2-25
# 游戏内部接口:理藩院

import time
import datetime
import random

from sgLib.base import Base
from sgLib.core import Gcore
from sgLib.defined import CFG_BUILDING_HOLD

class Building_holdMod(Base):
    '''理藩院模型'''
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
        self.serverid = int(Gcore.getServerId())
    
    def hasHolder(self):
        '''是否有主人 by Lizr
        @return: 有 True  没有 False
        '''
        hsid,huid = self.getMyHolder()
        return True if huid else False
        
    def getMyHolder(self):
        '''获取我的主人服务器ID和用户ID,也可用于判断我是否是自由身
        @return tuple (1,1008)
        '''
        table = 'tb_user'
        fields = ['HolderServerId','HolderId']
        where = 'UserId=%s AND HolderId!=0 AND HolderServerId!=0 AND HoldEndTime>UNIX_TIMESTAMP()' % self.uid
        row = self.db.out_fields(table, fields, where)
        if row:
            return (row['HolderServerId'],row['HolderId'])
        else:
            return (0,0)
            
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
                   BattleType IN (1,2)
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
        
    def getProtectHoldTime(self, PeerUID, PeerSID, tm):
        '''获取调停保护时间 add by qiudx 2013/07/11'''
        tm = tm if tm else int(time.time())
        if PeerSID == self.serverid:
            pMod = Gcore.getMod('Player', PeerUID)
            protectHoldEndTime = pMod.getUserInfo('ProtectHoldEndTime')
            protectTime = protectHoldEndTime - tm
            protectTime = protectTime if protectTime > 0 else 0
        else:
            peerKey = Gcore.redisKey(PeerUID)
            protectHoldEndTime = Gcore.redisM.hget('sgProtectHold', peerKey)
            if protectHoldEndTime and protectHoldEndTime > tm:
                protectTime = protectHoldEndTime - tm
            else:
                protectTime = 0
        return protectTime
            
        
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
            pMod = Gcore.getMod('Player', PeerUID)
            protectHoldEndTime = pMod.getUserInfo('ProtectHoldEndTime')
            if BeginTime < protectHoldEndTime:
                return -1   #对方处于保护时间内，设置失败add by qiudx
            
            Data = Gcore.getMod('Building_resource',PeerUID).collectAll() #将地里的资源以自由身的身份收集一次
            Data['HoldEndTime'] = EndTime if not Gcore.TEST else int(time.time()+180)
            Data['HolderName'] = Gcore.getUserData(self.uid,'NickName')
            Data['GiveRatio'] = Gcore.loadCfg(1506).get('GiveRatio',0.05)
            Gcore.push(112, PeerUID, Data,Type=1)
            
            # + 更新用户表
            arr = {'HolderId':self.uid,'HolderServerId':self.serverid,'HoldEndTime':EndTime}
            self.db.update('tb_user', arr, 'UserId=%s' % PeerUID)
            # + 插入本服藩国记录
            arr = {"HolderId":self.uid, "GiverId":PeerUID, "LastCollectTime":LastCollectTime,
                   "JcoinGive":Jcoin, "GcoinGive":Gcoin, "StopTime":StopTime, 
                   "BeginTime": BeginTime, "EndTime":EndTime}
            #self.db.insert('tb_hold', arr)
            self.db.insert_update('tb_hold', arr, {"GiverId":PeerUID} )
            
            # + 插入纳贡记录
            arr = {"UserId":PeerUID, "HolderId":self.uid, "Gcoin":0,
                   "HolderServerId":self.serverid, "Jcoin":0, "LastGiveTime":BeginTime}
            self.db.insert_update('tb_hold_log', arr, {"UserId":PeerUID} )
            
            # + 插入藩国反抗记录
            date = datetime.date.strftime(datetime.date.fromtimestamp(BeginTime), "%Y-%m-%d")
            arr = {"UserId":PeerUID, "HolderId":self.uid, "HolderServerId":self.serverid,
                   "ProcessTotal":0, "RevengeCount":0, "LastRevengeDate":date}
            self.db.insert_update('tb_hold_revenge', arr, {"UserId":PeerUID} )
        else: #非本服，发消息
            peerKey = Gcore.redisKey(PeerUID)
            protectHoldEndTime = Gcore.redisM.hget('sgProtectHold', peerKey)
            if BeginTime < protectHoldEndTime:
                return -1   #潘国保护时间内，设置失败
            Gcore.sendmq(1, PeerSID, {'HolderId':self.uid,
                                      'HolderServerId':self.serverid,
                                      'GiverId':PeerUID,
                                      'EndTime':int(EndTime)})
        k = '%s.%s' % (PeerSID, PeerUID)
        v = '%s.%s.%s.%s.%s.%s' % (self.serverid, self.uid, BeginTime, StopTime, EndTime, LastCollectTime)
        Gcore.redisM.hset('sgHold', k, v) #货币相关已独立出来 by Lizr
        k += Gcore.redisKey(self.uid)
        Gcore.redisM.hset('sgHoldJcoin', k, 0) #1.1008.2.1001  前面是进贡的人 后面的纳贡的人
        Gcore.redisM.hset('sgHoldGcoin', k, 0)
        return True
        
    def getHold(self):
        '''获取藩国列表'''
        #获取在本服的藩国-从tb_user表中查
        table = 'tb_user'
        fields = ['UserId', 'NickName', "UserLevel", "VipLevel", 'UserCamp', 'UserIcon']
        where = 'HolderId="%s" AND HolderServerId="%s"' % (self.uid, self.serverid)
        res = self.db.out_rows(table, fields, where)

        #获取跨服的藩国
        hold_records = Gcore.redisM.hgetall('sgHold') #@todo 这个地方要注意,一次查出来记录大多！
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
    
    def getHoldNum(self):
        '''获取我的藩国数量'''
        try:
            holdInfo = self.getHold()
            return len(holdInfo)
        except:
            print 'Excetion in getHoldNum()'
            return 0
        
    def isMyHold(self, uid, sid):
        '''判断是否是我的藩国
        @note 如果是我的藩国，返回（可纳贡的军资，可纳贡的铜币），否则返回False
        '''
        
        if sid == self.serverid:#本服
            table = 'tb_hold'
            fields = ['JcoinGive', 'GcoinGive']
            where = 'HolderId="%s" AND GiverId="%s"' % (self.uid, uid)
            res = self.db.out_fields(table, fields, where)
            return False if not res else (res["JcoinGive"], res["GcoinGive"])
        else: #跨服
            try:
                key = '%s.%s' %(sid, uid)
                key += Gcore.redisKey(self.uid)
                Jcoin = Gcore.redisM.hget('sgHoldJcoin', key)
                Gcoin = Gcore.redisM.hget('sgHoldGcoin', key)
                return (int(Jcoin), int(Gcoin))
            except Exception, e:
                print str(e)
                return False
    
    def freed(self, huid, hsid): #玩家达到一定要求，被释放。
        '''被释放 , 玩家使用调解卡时调用,释放自己
        @param huid: 主人的用户ID
        @param hsid: 主人的服务器ID
        '''
        if hsid == self.serverid: #占领者在本服
            
            Data = Gcore.getMod('Building_resource',self.uid).collectAll() #将地里的资源以被占领的身份收集一次
            Data['HoldEndTime'] = 0
            Gcore.push(112, self.uid, Data,Type=0)
            
            #查出进贡的钱
            row = self.db.out_fields('tb_hold', ["JcoinGive", "GcoinGive"],\
                               'GiverId="%s" AND HolderId="%s"'%(self.uid, huid))
            if row:
                ja, ga = row["JcoinGive"], row["GcoinGive"]
                
                modCoin = Gcore.getMod('Coin', huid)
                j = modCoin.GainCoin(0, 2, ja, 'Building_holdMod.freed', {'hsid':hsid, 'huid':huid})
                g = modCoin.GainCoin(0, 3, ga, 'Building_holdMod.freed', {'hsid':hsid, 'huid':huid})
            
            dic = {'HolderId':0,'HolderServerId':0,'HoldEndTime':0}
            self.db.update('tb_user', dic, 'UserId="%s"' % self.uid)
            self.db.execute('DELETE FROM `tb_hold` WHERE GiverId="%s" AND HolderId="%s"' % (self.uid, huid))
            self.db.execute('DELETE FROM `tb_hold_log` WHERE UserId="%s"' % self.uid)
            self.db.execute('DELETE FROM `tb_hold_revenge` WHERE UserId="%s"' % self.uid)
            
        else: #占领者不在本服
            Gcore.sendmq(3, hsid, {'HolderId':huid,
                          'GiverServerId':self.serverid,
                          'GiverId':self.uid})
        #删除自己的藩国redis
        Gcore.redisM.hdel("sgHold", '%s.%s' % (self.serverid, self.uid))
        return 1
  
    def free(self, uid, sid, ts=None):
        '''主动释放别人'''
        if self.serverid == sid: #本服
            Data = Gcore.getMod('Building_resource',uid).collectAll() #被释放前,以被占领的身份收集一次
            Data['HoldEndTime'] = 0
            Gcore.push(112, uid, Data,Type=0)
            
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
        jr=abs(jr)
        gr=abs(gr)
        if jr or gr:
            if sid == self.serverid: #本服
                sql = "UPDATE tb_hold SET JcoinGive=JcoinGive-'%s',GcoinGive=GcoinGive-'%s' WHERE HolderId='%s' AND GiverId='%s'" \
                %(jr,gr,self.uid, uid)
                self.db.execute(sql)
                
            else: #非本服,更新总服redis
                key = '%s.%s' % (sid, uid)
                key+=Gcore.redisKey(self.uid)
                
                jr = int(jr)*-1
                gr = int(gr)*-1
                Gcore.redisM.hincrby('sgHoldJcoin',key,jr)
                Gcore.redisM.hincrby('sgHoldJcoin',key,gr)
        return True
    
    def getRevent(self):
        '''获取反抗次数'''
        return self.db.out_fields('tb_hold_revenge', '*', 'UserId="%s"'%self.uid)
    
    def getTotalTribute(self,HolderId,HolderServerId):
        '''获取总进贡数量'''
        where = 'HolderId=%s AND HolderServerId=%s AND UserId=%s'%(HolderId,HolderServerId,self.uid)
        return self.db.out_fields('tb_hold_log', 'Jcoin,Gcoin', where)
    
    def calcRevent(self, TimeStamp=None):
        '''计算当天的反抗次数，反抗进度'''
        TimeStamp = TimeStamp if TimeStamp else time.time()
        rel = self.getRevent()
        if not rel  \
           or rel.get('LastRevengeDate') != datetime.date.fromtimestamp(TimeStamp):
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
            hsid,huid = self.getMyHolder()
            if huid:
                self.freed(huid, hsid) #让自己被释放
                pMod = Gcore.getMod('Player', self.uid)
                protectTime = Gcore.loadCfg(CFG_BUILDING_HOLD)['RvProtectHoldSecond']
                pMod.addProtectHoldTime(protectTime)
            return 1
        else: #增加累计进度
            arr = {}
            arr['ProcessTotal'] = pro_new
            arr['RevengeCount'] = cnt_new
            arr['LastRevengeDate'] = datetime.date.strftime(
            datetime.date.fromtimestamp(TimeStamp), '%Y-%m-%d')
            self.db.update('tb_hold_revenge', arr, 'UserId="%s"'%self.uid)
    
    def collectAdd(self,Jcoin,Gcoin):
        '''理藩院等级 纳贡加成'''
        
        return Jcoin,Gcoin
#end class Building_holdMod

def test():
    uid = 43368
    c = Building_holdMod(uid)
    return c.setHold(43929,1)

if '__main__' == __name__:
    uid = 1001
    #res = test()
    #print res
    c = Building_holdMod(uid)
    print c.getHoldNum()
#    print c.setHold(1013, 1)
#    print c.setHold(1005, 1)
#    print c.setHold(1006, 1)
#    hsid,huid = c.getMyHolder()
 #   print hsid,huid
    #c.setReventProcess(0.57,1)
#     test()
    import time
    time.sleep(2)