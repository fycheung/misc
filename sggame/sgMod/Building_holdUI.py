# -*- coding:utf-8 -*-
# author:zhoujingjiang
# date:2013-3-6
# 游戏外部接口:理藩院

import sys
import time

from sgLib.core import Gcore, inspector

class Building_holdUI(object):
    '''理藩院功能外部接口'''
    def __init__(self, uid):
        self.mod = Gcore.getMod("Building_hold", uid)
        self.uid = uid

    @inspector(15121, ['typ', 'uid', 'sid'])
    def SlaveOperand(self, param={}):
        '''对藩国的操作    纳贡 或 释放'''
        optId = 15121
        
        typ = param['typ'] #操作类型：1，纳贡。2，释放。
        uid = param['uid'] #藩国UserId
        sid = param['sid'] #藩国ServerId
        ts = param['ClientTime'] #客户端时间戳
        recordData = {}#成就记录
        
        stat = self.mod.isMyHold(uid, sid)
        if not stat: #不是玩家的藩国
            return Gcore.error(optId, -15121001)  
        Jcoin, Gcoin = stat[0], stat[1]
               
        modCoin = Gcore.getMod('Coin', self.uid)
        classMethod = '%s.%s' % (self.__class__.__name__, sys._getframe().f_code.co_name)
        if typ == 1: #1，纳贡
            if Jcoin == 0 and Gcoin == 0:
                return Gcore.error(optId, -15121002) #不可收集
            j = modCoin.GainCoin(optId, 2, Jcoin, classMethod, param)
            g = modCoin.GainCoin(optId, 3, Gcoin, classMethod, param)
            if j < -1 or g < -1:
                return Gcore.error(optId, -15121003) #增加货币操作失败
            j = 0 if Jcoin==0 else j
            g = 0 if Gcoin==0 else g
            self.mod.collect(uid, sid, j, g, ts)
            recordData = {'uid':self.uid,'ValType':0,'Val':1}#成就记录
        elif typ == 2: #2，释放。
            j = modCoin.GainCoin(optId, 2, Jcoin, classMethod, param)
            g = modCoin.GainCoin(optId, 3, Gcoin, classMethod, param)
            self.mod.free(uid, sid, ts)
        else:
            return Gcore.error(optId, -15121005) #操作类型错误
        return Gcore.out(optId, body = {"Jcoin":j, "Gcoin":g},mission=recordData)     
    
    @inspector(15122, ['SlaveUID', 'SlaveSID'])
    def SetHold(self, param={}): 
        '''设置藩国'''
        optId = 15122
        
        BuildingId = param.get('BuildingId') #建筑ID
        if not BuildingId:
            BuildingId = Gcore.getMod('Building',self.uid).getBuildingIdByType(10) #by Lizr
            
        suid = param['SlaveUID'] #奴隶ID
        ssid = param['SlaveSID'] #奴隶服务器ID
        ts = param['ClientTime'] #时间戳
        
        #if self.mod.getHolder(self.uid, Gcore.getServerId(), False) is not None:
        #    return Gcore.error(optId, -15122001) #玩家本身不是自由身 -> 改为不是自由身也可以设为别人为藩国
        
        if self.mod.getHolder(suid, ssid, False) is not None:
            return Gcore.error(optId, -15122002) #要设置的玩家不是自由身
        
        #是否是我的手下败将
        MyDefeaters = self.mod.getDefeaters()
        if not (suid, ssid) in [(d["PeerUID"], d["PeerSID"]) for d in MyDefeaters]:
            return Gcore.error(optId, -15122003) #不是手下败将
        
        #藩国最大数量
        modBuilding = Gcore.getMod('Building', self.uid)
        BuildingInfo = modBuilding.getBuildingById(BuildingId, TimeStamp = ts)
        #print 'BuildingId',BuildingId
        #print 'BuildingInfo',type(BuildingInfo),BuildingInfo
        if not BuildingInfo:
            return Gcore.error(optId, -15122004) #玩家没有这个理藩院
        if BuildingInfo['BuildingState'] == 1:
            return Gcore.error(optId, -15122005) #建筑正在建造   
        if BuildingInfo['BuildingType'] != 10:
            return Gcore.error(optId, -15122006) #建筑不是理藩院
        MaxNum = Gcore.getCfg('tb_cfg_building_up', (10, BuildingInfo['BuildingRealLevel']), 'SaveValue')
        
        if len(self.mod.getHold()) >= MaxNum:
            return Gcore.error(optId, -15122007) #藩国数量已达最大
        hsid, huid = self.mod.getMyHolder()
        
        if hsid == ssid and huid == suid:
            return Gcore.error(optId, -15122009) #不能设自己的主人为藩国
        
        stat = self.mod.setHold(suid, ssid)
        if stat == -1:
            return Gcore.error(optId, -15122010) #玩家处于调停中，无法设为潘国
        elif stat < 0:
            return Gcore.error(optId, -15122008) #设置藩国失败
        
        #从手下败将中删除
        self.mod.delDefeater(suid, ssid)
        
        #被设为藩国也不释放自己的藩国
        ''' # 释放掉藩国的所有藩国, 如果是本服，调用本服接口
        if ssid == Gcore.getServerId():
            ui = Gcore.getUI('Building_hold', suid)
            print dir(ui)
            print ui.uid
            mod = Gcore.getMod('Building_hold', suid)
            print '奴隶的奴隶', mod.getHold()
            for h in mod.getHold():
                ui.SlaveOperand({'typ':2, 'uid':h["UserId"],
                                 'sid':h.get("ServerId", ssid)})
        '''
        recordData = {'uid':self.uid,'ValType':0,'Val':1}#任务
        return Gcore.out(optId, body = {},mission=recordData,achieve=recordData)
    
    @inspector(15123)
    def GetHold(self, param={}):
        '''
        @旧:我的藩国(如果我有主人就显示主人信息): 获取主人和奴隶的信息
        @新:显示我的藩国列表
        '''
        optId = 15123
        
        #holder = self.mod.getHolder()
        #if not holder:
        if True:
            holder = {"hServerId":0, "hUserId":0}
            
            Slaves = self.mod.getHold()
            for Slave in Slaves:
                suid, ssid = Slave['UserId'], Slave.get('ServerId', Gcore.getServerId())
                stat = self.mod.isMyHold(suid, ssid)
                if not stat:
                    Slave['Jcoin'], Slave['Gcoin'] = 0, 0
                else:
                    Slave['Jcoin'], Slave['Gcoin'] = stat
                Slave.setdefault('ServerId', Gcore.getServerId())
        else:
            Slaves = []
 
        return Gcore.out(optId, {'Holder':holder, 'Holds':Slaves})

    @inspector(15124)
    def GetDefeaters(self, param={}):
        '''获取手下败将'''
        optId = 15124
        
        tm = int(time.time())
        RelLst = self.mod.getDefeaters()
        for dic in RelLst:
            peeruid, peersid = dic['PeerUID'], dic['PeerSID']
            holder = self.mod.getHolder(peeruid, peersid)
            if not holder:
                protectTime = self.mod.getProtectHoldTime(peeruid, peersid, tm)
                dic['ProtectHoldTime'] = protectTime    #添加调停保护时间
                dic['Holder'] = {}
            else:
                dic['ProtectHoldTime'] = 0
                dic['Holder'] = holder

        return Gcore.out(optId, body = {'Defeaters':RelLst})   
    
    @inspector(15125)
    def GetHolder(self, param={}):  
        '''获取主人'''
        optId = 15125
        
        holder = self.mod.getHolder()
        holder = holder if holder is not None else {}    
        return Gcore.out(optId, body = {'Holder':holder})
    
    @inspector(15126)
    def GetRevent(self, param={}):
        '''获取反抗次数，反抗进度'''
        optId = 15126
        
        TimeStamp = param['ClientTime']
        stat = self.mod.calcRevent(TimeStamp)
        HolderInfo = self.mod.getHolder()
        if not HolderInfo:
            RetDic = {}
        else:
            hServerId = HolderInfo.get('hServerId')
            hUserId = HolderInfo.get('hUserId')
            RetDic = {}
            RetDic["RevengeCount"] = stat[0]
            RetDic["ProcessTotal"] = stat[1]
            RetDic["MaxRevengeCount"] = 5 #读配置
            RetDic["HolderId"] = hUserId
            RetDic["HolderServerId"] = hServerId
            RetDic["HnickName"] = HolderInfo.get('hNickName')
            Tribute = self.mod.getTotalTribute(hUserId,hServerId)
            RetDic["Jcoin"] = Tribute.get('Jcoin',0)
            RetDic["Gcoin"] = Tribute.get('Gcoin',0)
            
        return Gcore.out(optId, body={'Revenge':RetDic})
    
    def CheckGeneralSoldier(self,param={}):
        '''检查是否有武将上场和兵 by Lizr'''
        optId = 15127
        CanFight = Gcore.getMod('Battle',self.uid)._checkGeneralSoldier()
        return Gcore.out(optId, body={'CanFight':CanFight})
    
    def RefreshHoldState(self,param={}):
        '''自动解除藩国关时前台请求刷新(如果前台在线)'''
        optId = 15128
        BuildingInfo = Gcore.getMod('Building',self.uid).getResourceOutBuilding()
        row = self.mod.db.out_fields('tb_currency', 'Jcoin,Gcoin', 'UserId=%s' % self.uid)
        body = {
                'CoinInfo':{2:row['Jcoin'],3:row['Gcoin']},
                'BuildingInfo':BuildingInfo,
                }
        return Gcore.out(optId,body)
    
    def IfShowRevolt(self):
        '''是否需要显示反抗按键
        @use: 点理藩院建筑时调用
        '''
        optId = 15129
        show = 1 if self.mod.hasHolder() else 0
        return Gcore.out(optId,{'show':show})

#end class Building_holdUI()

def _test():
    '''测试'''
    uid = 44025 #43346
    c = Building_holdUI(uid)

    print c.GetHold() #我的藩国
    #c.IfShowRevolt()
    #print c.GetHolder()
    #print c.GetDefeaters() #手下败将
    #print c.GetRevent() #反抗界面
    
    #print c.SetHold({'SlaveUID':1011, 'SlaveSID':1, 'BuildingId':1968})
    #print c.SlaveOperand({'typ':2,'uid':1006,'sid':2,'SlaveUID':1006, 'SlaveSID':2, 'BuildingId':374})
    
    #c.IsFree() #是否是自由身
    #import time; time.sleep(100)
    #BuildingId = Gcore.getMod('Building',uid).getBuildingIdByType(10) #by Lizr
    #print 'BuildingId = ',BuildingId
    #c.RefreshHoldState()
    
   
    
if '__main__' == __name__:
    _test()