#coding:utf8
#author:zhoujj
#消息的逻辑处理模块

from sgLib.core import Gcore
from sgLib.base import Base
import datetime
import time
import struct

LEN_HEADER = '!I'
LEN_HEADER_SIZE = struct.calcsize(LEN_HEADER)
'''
协议号定义:
1:被设置为藩国
2:藩国被释放
3:释放奴隶
4:你被攻打中
5:防御工事损坏   (可考虑把攻城的几个协议号合到一个)
6:被攻打战报
7:被抢夺资源
8:增减荣誉
9:被攻打者获得保护
'''
class MqManager(object):
    def __init__(self):
        self.db = Gcore.getNewDB()
        self.mapInfo = {
                        1:'becomehold',
                        2:'freehold',
                        3:'autofree',
                        4:'befight',
                        5:'defenseDamage',
                        6:'battleReport',
                        7:'lostCoin',
                        8:'gainHonour',
                        9:'gotProtect',
                        }
    def checkOpt(self,msg):
        print 'MqManager.checkOpt',msg
        msg = eval(msg)
        optId = int( msg['optId'] )
        para = msg['para']
        print 'para', para
        calledMethod = getattr(self, self.mapInfo[optId])
        try:
            calledMethod(para)
        except Exception,e:
            print e
            raise
    
    #================================== 运行MQ逻辑 ======================================
    def becomehold(self,para):
        '''协议号1: 被设置为藩国
        @todo 收集一下资源，推送给前端被设为藩国
        '''
        uid, hid, hsid, htime = int(para['GiverId']), int(para['HolderId']), int(para['HolderServerId']), int(para['EndTime'])
        update_dic = {}
        update_dic['HolderId'] = hid
        update_dic['HolderServerId'] = hsid
        update_dic['HoldEndTime'] = htime
        self.db.update('tb_user', update_dic, 'UserId="%s"'%uid)
        #纳贡记录
        arr = {"UserId":uid, "HolderId":hid, "HolderServerId":hsid, "Jcoin":0, "Gcoin":0, "LastGiveTime":htime}
        self.db.insert('tb_hold_log', arr)
        #反抗进度
        arr = {"UserId":uid, "HolderId":hid, "HolderServerId":hsid,
               "ProcessTotal":0, "RevengeCount":0, "LastRevengeDate":datetime.date.today()}
        self.db.insert('tb_hold_revenge', arr)
        #如果有藩国的话全部释放掉
        # + 玩家的藩国
        
        holds = Gcore.getMod('Building_hold',uid).getHold()
        for h in holds:
            param = {"typ":2, "uid":h["UserId"], "sid":h.get("ServerId", Gcore.getServerId())}
            Gcore.getUI('Building_hold',uid).SlaveOperand(param)
        
    def freehold(self,para):
        '''协议号2: 藩国被释放
        @todo 收集一下资源，推送给前端被释放
        '''
        uid = int(para['GiverId'])
        res = self.db.update('tb_user', {'HolderId':0, 'HolderServerId':0, \
                           'HoldEndTime':0}, 'UserId="%s"'%uid)
        res = self.db.execute('DELETE FROM `tb_hold_log` where UserId="%s"'%uid)
        res = self.db.execute('DELETE FROM `tb_hold_revenge` where UserId="%s"'%uid)
    

    def autofree(self,para):
        '''协议号3: 释放奴隶'''
        uid, suid, ssid = map(int, [para["HolderId"], para['GiverId'], para['GiverServerId']])
        param = {"typ":2, "uid":suid, "sid":ssid}
        Gcore.getUI('Building_hold',uid).SlaveOperand(param)
        
    def befight(self,para):
        '''协议号4: 你被攻打中'''
        t = 18 if Gcore.TEST else 180
        UserId = para['UserId']
        Fighter = para['Fighter']
        FightEndTime = time.time()+t
        sql = "UPDATE tb_user SET FightEndTime='%s',Fighter='%s' WHERE UserId=%s" \
        %(FightEndTime,Fighter,UserId)
        self.db.execute(sql)
        para = {"UserId":UserId, "Type":1, "Data":{'FightRestTime':t,'Fighter':Fighter} }
        self._notifyServer(8888, para)
    
    def defenseDamage(self,para):
        '''协议号5: 防御工事损坏'''
        UserId = para['UserId']
        Defense = para['Defense'] #有损坏变化的工事
        b = Base(UserId)
        tb_wall_defense = b.tb_wall_defense()
        for k,v in Defense.iteritems():
            sql = "UPDATE %s SET LifeRatio='%s' WHERE WallDefenseId='%s'"%(tb_wall_defense,v,k)
            result = self.db.execute(sql)
            print 'result:sql',result,sql
        Gcore.getMod('Redis',UserId).offCacheWallDefense() #更新缓存
    
    def battleReport(self,para):
        '''协议号6: 战报'''
        self.db.insert('tb_battle_report',para)
        
        print self.db.sql
    
    def lostCoin(self,para):
        '''协议号 7：被抢夺资源'''
        UserId = para['UserId']
        coinDict = para['coinDict']
        print 'ps lostCoin',coinDict
        Gcore.getMod('Building_resource',UserId).lostCoin(coinDict)
    
    def gainHonour(self,para):
        '''协议号 8：增减荣誉'''
        print 'ps gainHonour',para
        UserId = para['UserId']
        Honour = para['Honour']
        Gcore.getMod('Player',UserId).gainHonour(Honour)
    
    def gotProtect(self,para):
        '''协议号 9：更新保护时间'''
        print 'ps gotProtect',para
        UserId = para['UserId']
        AddSecond = para['AddSecond']
        Gcore.getMod('Player',UserId).addProtectTime(AddSecond)
#        sql = "UPDATE tb_user SET ProtectEndTime=ProtectEndTime+'%s' WHERE UserId='%s'"%(AddTime,UserId)
#        self.db.execute(sql)
#        ProtectEndTime = self.db.out_field('tb_user','ProtectEndTime','UserId=%s'%UserId)
#        key = '%s.%s'%(ServerId,UserId)
#        Gcore.redisM.hset('sgProtect',key,ProtectEndTime)
#        Gcore.sendmq(1, 10000, {UserId:self.uid,'protectEndTime':protectEndTime}) #发送到总服更新 攻城查找表
        
    def _notifyServer(self,optId,para={}):
        '''通知服务器'''
        from sgCfg import config
        SECRET_DATA_OPEN = config.SECRET_DATA_OPEN  #是否开启数据加密和压缩
        from sgLib.pyMcrypt import encode
        from sgLib.setting import Setting
        import gevent.socket
        import json
        s = gevent.socket.socket()
        port  = Setting.getGatewayPort()
        if not port:
            port = config.CFG_GATEWAYSERV_PORT
        else:
            port -= 1 #战斗端口起动的，上一个端口,调试才用到
        
        print 'config.CFG_GATEWAYSERV_HOST',config.CFG_GATEWAYSERV_HOST
        print 'port',port
        sock=(config.CFG_GATEWAYSERV_HOST, int(port) ) #8082 8888
        try:
            s.connect(sock)
        except gevent.socket.error, e:
            raise
        a = {"opt_id":optId, "para": para, "opt_key":''}
        buff = json.dumps(a)
        print '_notifyServer', buff
        if SECRET_DATA_OPEN:
            buff = encode(buff,iszip=True)
        packed_len = struct.pack(LEN_HEADER, len(buff))
        s.sendall(packed_len + buff)
        s.close()
        
if '__main__' == __name__:
    '''模块内测试'''
    c = MqManager()
    msg = {}
    c.checkOpt(msg)