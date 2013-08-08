# -*- coding:utf-8 -*-
# author:Lizr
# date:2013-5-20
# 总服URL请求 模型

from sgLib.core import Gcore
from sgLib.base import Base
from sgLib.pyMcrypt import TokenDecode
import urllib2
import json

class RequestMod(Base):
    """docstring for ClassName模板"""
    def __init__(self, uid):
        '''注释'''
        Base.__init__(self,uid)
        self.uid = uid
        #print self.db #数据库连接类
    
    def CreatedPlayer(self,accountId):
        try:
            url =  Gcore.loadCoreCfg('PlatformUrl')
            Post = {}
            Post['ServerId'] = Gcore.getServerId()
            Post['LOCKKEY'] = TokenDecode().makeLockKey()
            Post['FUNC'] ="FindUI.CreatedPlayer" 
            Post['PARAM'] ={
                            'FromServerId':Gcore.getServerId(),
                            'AccountId':accountId,
                            }
            
            url+='?MSG='+json.dumps(Post)
            #print 'findOutFighter>>',url
            req = urllib2.Request(url)
            f = urllib2.urlopen(req)
            response = f.read()
            lis = response.split('@.@')
            return json.loads(lis[1])
        except:
            pass

    def findOutFighter(self,num=10,rowUser=None):
        '''跨服查找可攻城对象'''
        #print ' --- findOutFighter ---'
        try:
            if not rowUser:
                rowUser = self.getUserInfo(['UserCamp','UserLevel'])
            url =  Gcore.loadCoreCfg('PlatformUrl')
            Post = {}
            Post['ServerId'] = Gcore.getServerId()
            Post['LOCKKEY'] = TokenDecode().makeLockKey()
            Post['FUNC'] ="FindUI.FindFighter" 
            Post['PARAM'] ={
                            'FromServerId':Gcore.getServerId(),
                            'UserCamp':rowUser['UserCamp'],
                            'UserLevel':rowUser['UserLevel'],
                            'GetNum':num,
                            }
            
            url+='?MSG='+json.dumps(Post)
            #print 'findOutFighter>>',url
            req = urllib2.Request(url)
            f = urllib2.urlopen(req)
            response = f.read()
            lis = response.split('@.@')
            return json.loads(lis[1])
        except:
            return []
        

        


if __name__ == '__main__':
    uid = 1001
    c = RequestMod(uid)
    #c.test()
    print c.findOutFighter(2)