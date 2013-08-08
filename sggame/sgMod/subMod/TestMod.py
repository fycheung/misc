# -*- coding:utf-8 -*-
# author:Lizr
# date:2012-12-21
# 游戏内部接口,模型层(被*UI调用)

from sgLib.core import Gcore
from sgLib.base import Base

class TestMod(Base):
    """docstring for ClassName模板"""
    def __init__(self, uid):
        '''注释'''
        Base.__init__(self, uid)
        self.uid = uid
        #print self.getUserInfo('NickName')
#        print Gcore.getMod('Template',uid)
#        print Gcore.getMod('Template',uid)
#        print Gcore.getMod('Template',uid)
#        print Gcore.getMod('Template',uid)
        print '---- end TestMod.__init__'
    

    def test(self):
        '''测试方法'''
        #print 555
        #print self.db.out_field('tb_user','count(1)','1')
        

    def updateCoin(self,con):
        con = int(con)
        data = {'GoldCoin':con}
        res = self.db.update('tb_user',data,"UserId="+str(self.uid))
        print "TempMod.updateCoin > ",self.db.sql,res
        return res


if __name__ == '__main__':
    uid = 1001
    c = TestMod(uid)
    #c.test()
