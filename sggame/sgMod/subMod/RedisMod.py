#coding:utf8
#author:zhoujingjiang
#date:2013-5-13
#redis操作

#import sys;sys.path.insert(0,'/data1/sggame/s1testsg')
from sgLib.core import Gcore
from sgLib.base import Base
'''Redis 键值列表 :
1) "sgCoin"  #库存
2) "sgUser"  #用户资料
3) "sgProtect" #保护
4) "sgPredictOut" #预计产出
5) "sgTech" #科技
6) "sgGeneralOnEmbattle" #布阵的武将
7) "sgDefense" #防御工事
8) "sgGeneralOnDefense" #布防的武将
'''
class RedisMod(Base):
    def __init__(self, uid ,ServerId=None):
        '''@para: ServerId 测试用'''
        self.uid = uid
        self.serverid = ServerId if ServerId else Gcore.getServerId()
        self.encode = Gcore.common.json_encode
        Base.__init__(self, uid)
        
    def __del__(self): #清理缓存
        '''析构函数'''
    
    
    def serverStopCache(self):
        '''服务器停止,缓存在线用户'''
        for UserId in self.db.out_list('tb_user', 'UserId',"Online=1" ):
            c = RedisMod(UserId)
            c.offCacheAll()
        
        self.db.update('tb_user',{'Online':0},'1')
    
    # 用户下线时调用:分服总服各一份
    # + begin
    def offCacheAll(self):
        '''玩家下线的时候调用所有的缓存'''
        print 'Redis.offCacheAll()'
        print 'self.offCacheCoin()'
        self.offCacheCoin()
        
        print 'self.offCacheGeneral()'
        self.offCacheGeneral()
        
        print 'self.offCacheWallDefense()'
        self.offCacheWallDefense()
        
        print 'self.cacheSoldierTech()'
        self.cacheSoldierTech()
        
        print 'self.offCachePredictOut()'
        self.offCachePredictOut()
        
        print 'self.cacheUserInfo()'
        self.cacheUserInfo()
        
    
    def offCacheCoin(self):
        '''缓存货币'''
        coin = self.db.out_fields('tb_currency', ['Jcoin', 'Gcoin'],\
                           'UserId=%s'%self.uid)
        Gcore.redisL.hset('sgCoin', '%s.%s'%(self.serverid,self.uid), self.encode(coin) )
        Gcore.redisM.hset('sgCoin', '%s.%s'%(self.serverid,self.uid), self.encode(coin) )
    
    def offCachePredictOut(self):
        '''缓存预计每小时产量   {2: 25200, 3: 21600}'''
        dictPredictOut = Gcore.getMod('Building_resource', self.uid).predictOutValue()
        Gcore.redisL.hset('sgPredictOut', '%s.%s'%(self.serverid,self.uid), self.encode(dictPredictOut) )
        Gcore.redisM.hset('sgPredictOut', '%s.%s'%(self.serverid,self.uid), self.encode(dictPredictOut) )
        
    def offCacheWallDefense(self):
        '''缓存防御工事 Wall.getAllDefenseInfo()'''
#        table = self.tb_wall_defense(self.uid)
#        fields = '*'
#        where = 'UserId=%s' % self.uid
#        
#        WallDefenses = self.db.out_rows(table, fields, where)
#        RetDic = {}
#        for WallDefense in WallDefenses:
#            WallDefense.pop('MakeCost')
#            RetDic[WallDefense['WallDefenseId']] = WallDefense
        key = '%s.%s'%(self.serverid,self.uid)
        DefenseInfo = Gcore.getMod('Wall', self.uid).getAllDefenseInfo()
        import copy
        TrapInfo = {}
        for k,v in copy.deepcopy(DefenseInfo).iteritems():
            if v.get('SoldierType')>300:
                TrapInfo[k] = DefenseInfo.pop(k)
        
        CacheValue = Gcore.redisL.hget('sgDefense',key)
        if self.encode(DefenseInfo) != CacheValue and (DefenseInfo or CacheValue): #有变化才更新
  
            Gcore.redisL.hset('sgDefense', key, self.encode(DefenseInfo) )
            Gcore.redisM.hset('sgDefense', key, self.encode(DefenseInfo) )
        else:
            print '%s defense no need to cache'%self.uid
            
        CacheValue = Gcore.redisL.hget('sgTrap',key)
        if self.encode(TrapInfo) != CacheValue and (TrapInfo or CacheValue): #有变化才更新
  
            Gcore.redisL.hset('sgTrap', key, self.encode(TrapInfo) )
            Gcore.redisM.hset('sgTrap', key, self.encode(TrapInfo) )
        else:
            print '%s trap no need to cache'%self.uid
    # + end
    
    def offCacheGeneral(self): #布防的武将
        '''缓存布防的武将'''
        WallGenerals = self.db.out_rows('tb_wall_general', '*', \
                         'UserId=%s'%self.uid)
        RetDic = {}
        if WallGenerals: #没有布防，直接返回。
            modGeneral = Gcore.getMod('General', self.uid)
            WallGeneralList = [g["GeneralId"] for g in WallGenerals]
            fields = ['GeneralId', 'GeneralType', 'GeneralLevel', 'ForceValue', \
                      'WitValue', 'LeaderValue', 'SpeedValue', 'TakeTypeDefense','TakeType','ExpValue']
            #获取武将的最新信息
            Generals = modGeneral.getLatestGeneralInfo(GeneralIds=WallGeneralList)
            
            for General in Generals:
                for WallGeneral in WallGenerals:
                    if General['GeneralId'] == WallGeneral['GeneralId']:
                        General['x'] = WallGeneral['x'] 
                        General['y'] = WallGeneral['y']
                        General.pop('ExpValue',None)
                        RetDic[General['GeneralId']] = General
        
        Gcore.redisL.hset('sgGeneralOnDefense', '%s.%s'%(self.serverid,self.uid), self.encode(RetDic) )
        Gcore.redisM.hset('sgGeneralOnDefense', '%s.%s'%(self.serverid,self.uid), self.encode(RetDic) )
        
    # 用户进入竞技场时调用:缓存到总服
    # + begin
    def OnCacheGenerals(self):
        '''缓存最新的武将信息
        @布阵需要缓存的信息:
        ['GeneralId','PosId','TakeType','TakeNum','GeneralType','GeneralLevel','ForceValue','WitValue','SpeedValue','LeaderValue']
        '''
        modGeneral = Gcore.getMod('General', self.uid)
        fields=['GeneralId', 'GeneralType', 'GeneralLevel', 'ForceValue', 'PosId',
                'WitValue', 'LeaderValue', 'SpeedValue', 'TakeType', 'TakeNum']
        Generals = modGeneral.getLatestGeneralInfo()
        GeneralsOnEmbattle = []
        for General in Generals:
            if General['PosId'] != 0:
                GeneralsOnEmbattle.append(General)
        return Gcore.redisM.blockhset('sgGeneralOnEmbattle', \
                          '%s.%s'%(self.serverid, self.uid), \
                          self.encode(GeneralsOnEmbattle) )
    def OnCacheFriends(self):
        '''缓存好友信息'''
        table = 'tb_friend'; fields = ['FriendUserId', 'Favor']
        where = 'UserId=%s AND FriendStatus=%d' % (self.uid, 2)
        friends = self.db.out_rows(table, fields, where)
        friends_format = {}
        for friend in friends:
            friends_format['%s'%(friend['FriendUserId'], )] \
                = friend['Favor']
        return Gcore.redisM.blockhset('sgFriend', 
                                      '%s.%s'%(self.serverid, self.uid),
                                      self.encode(friends_format))      
        
    def onCacheAll(self):
        '''缓存所有信息'''
        self.OnCacheGenerals()
        self.OnCacheFriends()
        self.cacheSoldierTech(False)
        self.cacheUserInfo(False)
    # + end
    
    # 公用
    # + start
    def cacheSoldierTech(self, flag=True):
        '''缓存兵种科技'''
        modBook = Gcore.getMod('Book', self.uid)
        SoldierTechs = modBook.getTechsLevel(1)
        print 'SoldierTechs', SoldierTechs
        if flag: #是否在本服缓存
            Gcore.redisL.hset('sgTech', '%s.%s'%(self.serverid,self.uid), self.encode(SoldierTechs) )
        return Gcore.redisM.blockhset('sgTech', '%s.%s'%(self.serverid,self.uid), self.encode(SoldierTechs) )


    def cacheUserInfo(self, flag=True):
        '''缓存用户的信息'''
        fields = ['AccountId','UserId', 'UserLevel', 'UserIcon', 'NickName',
                  'UserLevel', 'VipLevel', 'UserHonour', 'UserCamp']
        UserInfo = self.db.out_fields('tb_user', fields, 'UserId="%s"'%self.uid)
        if flag:
            Gcore.redisL.hset('sgUser', '%s.%s'%(self.serverid, self.uid),self.encode(UserInfo) )
        Gcore.redisM.blockhset('sgUser', '%s.%s'%(self.serverid, self.uid),self.encode(UserInfo) )
    # + end
#end class Cache2Redis

def _test():
    '''模块内测试'''
    r = RedisMod(1032)
    print r.OnCacheFriends()
    db = Gcore.getNewDB()
    for UserId in db.out_list('tb_user', 'UserId',"UserId=1001 or 1" ): # OR 1
        print db.sql
        c = RedisMod(UserId)
        #print c.offCacheAll() #下线
        #print c.onCacheAll()  #上线
        
        #print c.offCacheWallDefense()
        #c.offCacheGeneral()
        #c = RedisMod(UserId,2)
        
        #c.offCacheWallDefense()
        #c.cacheUserInfo()
        #c.offCacheGeneral()
    Gcore.runtime() 
    
    import time
    time.sleep(5)
if '__main__' == __name__:
    #print Gcore.redisL.hget('sgPredictOut','1.1030')
    _test()