# -*- coding:utf-8 -*-
# author:Lizr
# date:2012-12-21
# 游戏外部接口,控制层 (以游戏逻辑为主,尽量不要数据库的查询)

from sgLib.core import Gcore
import time
#print 'in ExmapleUI,Gcore',Gcore,id(Gcore),Gcore.started
class TestUI(object):
    """测试 ModId:99 """
    def __init__(self, uid):
        '''注释'''
        self.uid = uid
        self.mod = Gcore.getMod('Test',uid)

    def test(self,p={}):
        '''测试获取当前缓存的用户信息'''
        optId = 99001
        Gcore.getUserData(1001, 'UserLevel')
        body = { 'Gcore.StorageUser': str(Gcore.StorageUser) }
        print 'body',body
        return Gcore.out(optId,body)
    
    def test2(self,p={}):
        '''测试方法2'''
        optId = 99002
        modEquip = Gcore.getMod('Equip',self.uid)
        building = modEquip.getSmithyInfo()
        if building is None:
            return Gcore.error(optId,-16005901)#建筑不存在
        result = modEquip.getSaleGoods()
        result['Sale'] = Gcore.common.list2dict(result['Sale'],offset=0)

        bagMod = Gcore.getMod('Bag',self.uid)
        bagGoods = bagMod.getGoods(3)
        bag = {}
        bag['GS'] = Gcore.common.list2dict(bagGoods, offset=0)
        bag['Size'] = bagMod.getBagSize()
        result['Bag'] = bag
        return Gcore.out(optId,result)
    
    def test3(self,p={}):
        '''测试方法3'''
        optId = 99003
        #2签到3成长4活跃
        actmod = Gcore.getMod('Activity', 43763)
        #actmod.insertGifts(2, 3005)
        #actmod.insertGifts(2, 3009)
        for i in range(3001, 3013):
            actmod.insertGifts(2, i)
        for i in range(1, 30):
            actmod.insertGifts(2, i)
        #for i in range(1, 17):
        #    actmod.insertGifts(3, i)
        for i in range(1, 5):
            if i == 3:
                continue
            actmod.insertGifts(4, i)
        num = actmod.pushGiftNum()
        #Gcore.push(109, 43568, {"GiftNum": num})
        return Gcore.out(optId,{'GiftNum': num})
    
    def test4(self, p={}):
        '''给玩家重新命名后对战斗tb_battle_record,tb_battlle_report两张表进行更新'''
        optId=99004
        pMod = Gcore.getMod('Player', 1001)
        userlist = pMod.db.out_rows('tb_user u, tb_battle_report b', ['u.UserId', 'NickName', 'FighterName'], 'b.FighterId = u.UserId')
        for user in userlist:
            row = {'FighterName': user['NickName']}
            where = 'FighterId=%s'%user['UserId']
            pMod.db.update('tb_battle_report', row, where)

        userlist = pMod.db.out_rows('tb_user u, tb_battle_record b', ['u.UserId', 'NickName', 'PeerName'], 'b.PeerUID = u.UserId')
        for user in userlist:
            row = {'PeerName': user['NickName']}
            where = 'PeerUID=%s'%user['UserId']
            pMod.db.update('tb_battle_report', row, where)
            
        return Gcore.out(optId, {'Content': []})
    
    def test5(self):
        '''重新生成玩家昵称'''
        optId = 99005
        pMod = Gcore.getMod('Player', 1001)
        player_rows = pMod.db.out_rows('tb_user', ['UserId', 'NickName', 'UserIcon'])
        userlist = []
        for player in player_rows:
            nickName = self.randomName(player['UserIcon'])
            userlist.append(nickName)
            row = {'NickName': nickName}
            where = 'UserId=%s'%player['UserId']
            pMod.db.update('tb_user', row, where)

        return Gcore.out(optId, {'UserList': userlist})
    
    def randomName(self, icon):
        '''随机名称  '''
        SelectNum = 30
        if icon > 2:
            sex = 2
        else:
            sex = 1
        
        pMod = Gcore.getMod('Player', 1001)

        lastnameList = Gcore.getCfg('tb_cfg_nickname').get(0)
        firstnameList = Gcore.getCfg('tb_cfg_nickname').get(sex)
        lastnameList = random.sample(lastnameList,SelectNum)
        firstnameList = random.sample(firstnameList,SelectNum)

        nicknames=[]
        for i in xrange(SelectNum):
            nickname = lastnameList[i]+firstnameList[i]
            nicknames.append(nickname)

        where = pMod.db.inWhere('NickName',nicknames)
        rows = pMod.db.out_rows('tb_user','NickName',where)
        existNickNames = [r['NickName'] for r in rows]
        notExistNickNames = list(set(nicknames)-set(existNickNames))
        
        NickNames = []
        for NickName in notExistNickNames:
            if Gcore.common.filterInput(NickName,2,16)<0:
                pass #过滤敏感词的名称
            else:
                NickNames.append(NickName)
        
        return NickNames[0]
        
        
      
        




if __name__ == '__main__':
    Gcore.start()
    uid = 1001
    c = TestUI(uid)
    #c.test3()
    #c.test4()
    c.test()
