# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-5-4
# 登录模型
import time
from sgLib.core import Gcore, inspector

class LoginUI(object):
    
    def __init__(self,uid):
        self.uid = uid
    
    def LoginInfo(self,p={}):
        '''登录用需要获得的信息汇总
        "opt_id":    15051
        "opt_id":    15050
        "opt_id":    18007
        "opt_id":    19011
        "opt_id":    13061
        '''
        startTime = time.time()
        optId = 10021
        #15051
        soldierTechs = Gcore.getMod('Book',self.uid).getTechs(1)#兵种科技
        interTechs = Gcore.getMod('Book',self.uid).getTechs(2)#内政科技     
        re = {}

        #15051 科技信息
        re['TechInfo'] = {'SoldierTechs':soldierTechs,'InterTechs':interTechs}
        
        #15050 科技升级信息
        tech = Gcore.getMod('Book',self.uid).getUpgradingTech()
        flag = 1 if tech else 0
        re['UpdateTechInfo'] =  {'IsUpgrading':flag,'Tech':tech}
        
        #18007 未读邮件
        re['UnReadNum'] = Gcore.getMod('Mail',self.uid).countUnReadNum()
        
        #19011 好友申请
        applyNum= Gcore.getMod('Friend',self.uid).countApply()
        re['ApplyNum'] = applyNum
        
        #13061 查看背包物品
        bagSize = Gcore.getMod('Bag',self.uid).getBagSize()#背包容量
        goods = Gcore.getMod('Bag',self.uid).getGoods(0)#背包物品
        goods = Gcore.common.list2dict(goods, offset=0)
        re['BagInfo'] = {'GS':goods,'Size':bagSize}
        #-----------------------------------
        runtime = time.time() - startTime
        if Gcore.TEST: #调试计时
            row = {
                     'UserId':self.uid,
                     'OptId':10021,
                     'CallMethod':'LoginUI.LoginInfo',
                     'Param':'',
                     'Response':'--skip',
                     'Runtime':runtime,
                     'RecordTime':Gcore.common.datetime(),
                     }
            Gcore.getDB(0).insert('temp_runtime_log', row)
        #-------------------------------------
        return Gcore.out(optId,re)
        
    def AlreadyLogin(self):
        '''不再是新号,选完军师之后前台访问'''
        optId = 10022
        Gcore.getMod('login',self.uid).alreadyLogin()
        return Gcore.out(optId)
        
        
'''帐户切换全部已改为直接访问总服   by Lizr '''
#    def Register(self,p={}):
#        '''注册登录'''
#        optId = 10091
#        userAccount = p.get('UserAccount')
#        userPWD = p.get('UserPWD')
#        macAddress = p.get('MacAddress')
#        
#        result = {
#                  'IP':'10.1.1.18',
#                  'Port':8082,
#                  'BPort':8082,
#                  'UID':1011,
#                  }
#        return Gcore.out(optId,result)
#        
#    def AccountLogin(self,p={}):
#        '''账号登录,切换'''
#        optId = 10092
#        userAccount = p.get('UserAccount')
#        userPWD = p.get('UserPWD')
#        macAddress = p.get('MacAddress')
#        
#        result = {
#                  'IP':'10.1.1.18',
#                  'Port':8082,
#                  'BPort':8082,
#                  'UID':1011,
#                  'Status':1,
#                  }
#        return Gcore.out(optId,result)
#
#    def MainLogin(self,p={}):
#        '''登录'''
#        optId = 10093
#        macAddress = p.get('MacAddress')
#        userId = p.get('UserId')#切换服务器时候必传
#        serverId = p.get('ServerId')#切换服务器时候必传
#        
#        result = {
#                  'IP':'10.1.1.18',
#                  'Port':8082,
#                  'BPort':8082,
#                  'UID':1011,
#                  }
#        return Gcore.out(optId,result)
#    
#    def GetServerList(self,p={}):
#        '''获取服务器列表'''
#        optId = 10094
#        macAddress = p.get('MacAddress')
#        
#        #服务器状态：1:新服,2:热门,3:推荐,4:拥挤,5:不可进入,6:良好
#        serverList = [{'ServerId':1,'ServerName':'群魔乱舞','ServerStatus':3,'Logined':1},
#                      {'ServerId':2,'ServerName':'英雄联盟','ServerStatus':2,'Logined':0},
#                      {'ServerId':3,'ServerName':'三百回合','ServerStatus':1,'Logined':0},
#                      {'ServerId':4,'ServerName':'去打老虎','ServerStatus':4,'Logined':0},
#                      {'ServerId':5,'ServerName':'暴乱精英','ServerStatus':5,'Logined':0},
#                      {'ServerId':6,'ServerName':'三国城管','ServerStatus':6,'Logined':1},]
#        userInfo = {'UserId':1,'UserName':'HGJ','UserPWD':'HJJ'}
#        
#        result = {
#                  'Account':userInfo,
#                  'IsBinded':1,
#                  'ServerList':serverList,
#                  }        
#        return Gcore.out(optId,result)
#    
#    def CheckValid(self,p={}):
#        optId = 10095
#        userAccount = p.get('UserAccount')
#        return Gcore.out(optId,{'ISV':1})
    
if __name__ == '__main__':
    '''调试'''
    c = LoginUI(1005)
    c.LoginInfo()