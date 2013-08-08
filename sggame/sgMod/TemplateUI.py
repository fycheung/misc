# -*- coding:utf-8 -*-
# author:
# date:2013-1-
# 游戏外部接口模板


from sgLib.core import Gcore,inspector


class TemplateUI(object):
    """测试 ModId:99 """
    def __init__(self, uid):
        '''注释'''
        self.uid = uid
        self.mod = Gcore.getMod('Template',uid)
        print self.mod

    @inspector(00001,['xxx'])
    def test(self,para={}):
        '''测试方法'''
        print 333


def test():
    uid = 1001
    c = TemplateUI(uid)
    Gcore.printd(d)

if __name__ == '__main__':
    test()
