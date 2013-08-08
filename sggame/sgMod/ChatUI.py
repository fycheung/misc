# -*- coding:utf-8 -*-
# author:
# date:2013-1-
# 游戏外部接口模板


from sgLib.core import Gcore,inspector


class ChatUI(object):
    """测试 ModId:11 """
    def __init__(self, uid):
        '''注释'''
        self.uid = uid
        self.mod = Gcore.getMod('Chat',uid)
        print self.mod

    def test(self,para={}):
        '''测试方法'''
        print 333
    
    @inspector(11001,['Channel','Content'])
    def Say(self,para={}):
        '''发送聊天信息
        @para : Channel => int 聊天类型：1，世界。2，势力。3，军团。4，私聊。5，系统。6，喇叭。 
                7， 系统公告（用于GM发布系统公告用）。8，活动。9，广播
        @para : Content => string 消息体
        @para : ToName => int or str 消息接受者（用于私聊）
        @note : 需要注意前玩家在游戏中 改变军团(退出或加入)时要更新Gcore.StorageUser['club']
        '''
        optId = 11001
        #print 'say',para
        channel=para.get('Channel')
        content=para.get('Content')
        toName=para.get('ToName')
        #re=1
        re=self.mod.say(optId, channel,content,toName)
        if re==-1:
            return Gcore.error(optId,-11001001)#聊天间隔限制
        elif re==-2:
            return Gcore.error(optId,-11001002)#消息未通过验证
        elif re==-3:
            return Gcore.error(optId,-11001003)#发送对象不在线
        elif re==-4:
            return Gcore.error(optId,-11001004)#喇叭使用条件不足
        elif re==-5:
            return Gcore.error(optId,-11001999)#聊天类型错误
        elif re==-6:
            return Gcore.error(optId,-11001005)#不能私聊自己
        elif re==-7:
            return Gcore.error(optId,-11001006)#权限不足
        elif re==-8:
            return Gcore.error(optId,-11001007)#被禁言
        else:
            #return Gcore.out(optId,{'Result':re})
            return Gcore.out(optId)

    

        


def test():
    import time
    uid = 1012
    #uid = 43400
    Gcore.resetRuntime()
    c = ChatUI(uid) 
    #p = {'Channel':1,'Content':'fuckyou'}
    import chardet
    
    #s = u"*\uff65\u309c\uff9f\uff65*:.\uff61..\uff61.:*\uff65'(*\uff9f\u25bd\uff9f*)'\uff65*:.\uff61. .\uff61.:*\uff65\u309c\uff9f\uff65*"
    #print s.encode('utf8') #Content": "*･゜ﾟ･*:.｡..｡.:*･'(*ﾟ▽ﾟ*)'･*:.｡. .｡.:*･゜ﾟ･*
    
    #p = {"Content": "asdasd", "ClientTime": 1371108139, "Channel": 4,"ToName":'孟蓝'}
    p = {"Content": "hhh", "ClientTime": 1371780923, "Channel": 1}
    for _ in range(2):
        print '================='
        print c.Say(p)
        print '================='
        time.sleep(1)
        
    
    Gcore.runtime()
    #Gcore.printd(d)

if __name__ == '__main__':
    test()
