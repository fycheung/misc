# -*- coding:utf-8 -*-
# author:
# date:2013-1-
# 游戏内部接口,模型模板

from sgLib.core import Gcore
from sgLib.base import Base

class TemplateMod(Base):
    """docstring for ClassName模板"""
    def __init__(self, uid):
        '''注释'''
        Base.__init__(self,uid)
        self.uid = uid
        #print self.db #数据库连接类

    def test(self):
        '''测试方法'''
        

        


if __name__ == '__main__':
    uid = 1001
    c = TemplateMod(uid)
    c.test()