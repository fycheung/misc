#-*- coding:utf-8 -*-
#author:Lizr
#date:2012-12-21
#游戏模型基类

import time
from sgLib.core import Gcore

tbnum = Gcore.config.TBNUM
class Base(object):
    """模型基类"""
    def __init__(self, uid, CacheAll=True):
        '''当别的地方调用的 Cache 为False 如mqManager拿tb_*表'''
        assert uid>0
        self.uid = uid
        self.db = Gcore.getDB(uid)
            
    def getHomeLevel(self):
        '''获取将军府等级 '''
        return Gcore.getMod('Building',self.uid).getHomeLevel()
    
    #常用的用户资料查询 到时候考虑做缓存
    def getUserCamp(self):
        '''获取我的阵营,#@todo使用缓存'''
        #return self.db.out_field('tb_user','UserCamp','UserId=%s'%self.uid)
        return Gcore.getUserData(self.uid, 'UserCamp')
        
    def getUserLevel(self):
        '''获取主角等级'''
        #return self.db.out_field('tb_user','UserLevel','UserId=%s'%self.uid)
        return Gcore.getUserData(self.uid, 'UserLevel')

    def getUserInfo(self,fields=[]):
        '''获取用户信息 (考虑拆分缓存和非缓存部分)'''
        if type(fields) is list:
            return self.db.out_fields('tb_user',fields,'UserId=%s'%self.uid)
        else:
            return self.db.out_field('tb_user',fields,'UserId=%s'%self.uid)
        
    def tb_building(self,UserId=None):
        '''获取我的建筑表'''
        if not UserId:
            UserId = self.uid
        i = UserId%tbnum
        table = 'tb_building%s'%i
        return table
    
    def tb_equip(self,UserId=None):
        '''获取我的装备表'''
        if not UserId:
            UserId = self.uid
        i = UserId%tbnum
        table = 'tb_equip%s'%i
        return table
    
    def tb_general(self,UserId=None):
        '''获取我的武将表'''
        if not UserId:
            UserId = self.uid
        i = UserId%tbnum
        table = 'tb_general%s'%i
        return table
    
    def tb_wall_defense(self,UserId=None):
        '''获取我的布防防御工事表'''
        if not UserId:
            UserId = self.uid
        i = UserId%tbnum
        table = 'tb_wall_defense%s'%i
        return table
    
    def tb_bag(self,UserId=None):
        '''获取我的背包表'''
        if not UserId:
            UserId = self.uid
        i = UserId%tbnum
        table = 'tb_bag%s'%i
        return table
    
    def tb_log_login(self):
        '''获取用户登录表'''
        curMon = time.strftime('%Y%m',time.localtime(time.time()))
        loginTB = 'tb_log_login%s'%curMon
        tbs = self.db.query("SHOW tables LIKE '%s'"%loginTB)
        if len(tbs):
            return loginTB
        else:
            sql = """
                CREATE TABLE `%s` (
                  `logId` int(11) NOT NULL AUTO_INCREMENT COMMENT '自增主键',
                  `UserId` int(11) NOT NULL COMMENT '角色ID',
                  `UserType` tinyint(4) NOT NULL COMMENT '用户类型',
                  `LoginTime` int(11) NOT NULL COMMENT '登录时间',
                  `LogoutTime` int(11) NOT NULL DEFAULT '0' COMMENT '下线时间',
                  `OnlineTime` int(11) NOT NULL DEFAULT '0' COMMENT '在线时长',
                  `LoginModel` smallint(5) NOT NULL COMMENT '玩家登陆的方式(1:Iphone 2:Ipad 3:安卓)',
                  `LoginIP` varchar(16) NOT NULL COMMENT '登录IP',
                  PRIMARY KEY (`logId`),
                  KEY `LoginTime` (`LoginTime`,`OnlineTime`)
                ) ENGINE=MyISAM AUTO_INCREMENT=161 DEFAULT CHARSET=utf8 COMMENT='登录记录表(%s)'"""%(loginTB,curMon)
            self.db.execute(sql)
            return loginTB
        return loginTB

    #书写高级 但开发时Eclipse的提示没有了，不是很方便，以后再考虑恢复
#    def __getattr__(self, t):
#        '''获取分表表名'''
#        tables = ['tb_building', 'tb_general', 'tb_equip', 'tb_wall_defense','tb_bag']
#        num = 10 
#        if Gcore.TEST == 1: #开发
#            num = 2
#        if t in tables:
#            return lambda u=None : '%s%s' % (t, self.uid % num if not u else u % num)
        
if __name__ == '__main__':
    '''测试'''
    c = Base(1001) #1001
#    print dir(c.__getattr__.__hash__)
    #print c.tb_building(1008)
#    print c.tb_equip()
#    print c.tb_general()
    #print c.tb_building()
#    print c.tb_general()
#     print c.tb_bag(1008)
    print c.getUserIcon()
    
    
