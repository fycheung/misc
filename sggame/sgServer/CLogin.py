# -*- coding:utf-8 -*-
# author:zhanggh
# date:2012-12-21
# 帐户登录

import time
from sgLib.defined import *
from sgLib.core import Gcore
from sgLib.common import filterInput
import random
class Login(object):
    """用户登录类 """
    def __init__(self):
        self.db = Gcore.getNewDB()
    
    #optId = 10001 .
    def LoginAccount(self,para={}):
        '''登录 参数来源于总服php
        $arr_TokenInfo['LoginVersion'] = $i_Version;                                    //玩家登陆的版本(前台版本)
        $arr_TokenInfo['LoginMode'] = $i_LoginMode;                                        //玩家登陆的方式(1:Iphone  2:Ipad  3:安卓 4:网页);
        $arr_TokenInfo['TotalServiceId'] = $arr_UserInfo['UserId'];                        //平台ID
        $arr_TokenInfo['PlayerId'] = (int)$i_PLayerId;                                    //分服的ID
        $arr_TokenInfo['Lan'] = (int)$i_Lan;                                            //语言包类型
        $arr_TokenInfo['UserName'] = $arr_UserInfo['UserName'];                            //平台帐户名
        '''
        uid = para.get('uid')
        aId = para.get('TotalServiceId')
        flag=False #是否是第一次
        if uid:
            UserId = uid
            print 'LoginAccount Developer login uid:',uid
        else:
            if aId is None:
                return -10001999 #Gcore.error(opt_id,-10001001) #参数错误
            
            #获取用户信息
            UserId = self.getUserIdByAccount(aId)
            #print 'getUserId,UserId',UserId
            if not UserId:#没有用户要求注册一个
                return -10001001 #先注册

        try:
            mod_play = Gcore.getMod('Player', UserId) #此处会为用户获取新的连接
            userData = mod_play.PlayerInfo()
            if not userData.get('BindAccount') and  para.get('UserName'):  #by Lizr 0626
                mod_play.db.update('tb_user',{'BindAccount':1},'UserId=%s'%UserId)
        except Exception, e:
            print 'UserId',UserId
            print 'Login Fail >> ,', e
            if Gcore.TEST:
                raise
            userData = {}

            return -10001002 #登录失败
        if flag:
            userData['IsFirstLogin'] = True
        #print 'userData', userData
        #print 'end LoginAccount()'
        return userData
    
    #optId = 10002
    def CreateRole(self,p={}):
        '''注册用户 by zhanggh'''
        AccountId = p.get('TotalServiceId') 
        nickName = p.get('NickName')
        camp = p.get('UserCamp')
        userIcon = p.get('UserIcon')
        OldAccount = p.get('OldAccount') #是否老用户

        
        if (not AccountId) or (not nickName) or (not camp) or (not userIcon):
            return -10002999 #参数错误
        
        PlayerCfg = Gcore.loadCfg(Gcore.defined.CFG_PLAYER)
        nickNameMin = PlayerCfg.get('NickNameMin')
        nickNameMax = PlayerCfg.get('NickNameMax')
        
        flag=filterInput(nickName,nickNameMin,nickNameMax)
        if flag==-1:
            return -10002993#字数字数限制
        elif flag==-2:
            return -10002991#特殊字符
        elif flag==-3:
            return -10002992#敏感字
        
        if camp not in [1,2,3]:
            return -10002004#阵营不正确
        
        if userIcon not in [1,2,3,4,5]:
            return -10002005#头像不正确
        
        print 'CheckNickName',flag
        
        #获取用户ID,暂时没有角色UserId才能注册
        UserId = self.getUserIdByAccount(AccountId)
        if not UserId:#没有用户注册一个，建立AccountId与Uid关系，创建用户
            #验证用户昵称
            hasSameName = self.db.out_field('tb_user','Count(1)',"NickName='%s'"%nickName)
            if hasSameName:
                return -10002001#用户昵称已存在
            UserId = self.CreateUser(p)
            if not UserId:
                return -10002002#注册失败

        try:
            mod_play = Gcore.getMod('Player', uid=UserId) 
            userData = mod_play.PlayerInfo()
            
            try:
                Gcore.getMod('Request', UserId).CreatedPlayer(AccountId)
            except Exception,e:
                print '通知总服已创建号失败',e
            
        except Exception, e:
            userData = {}
            print '登陆失败,', e
            return -10002003
        
        #print 'userData', userData
        return userData
    
    #optId=10003
    def randomName(self,para={}):
        '''随机名称  Lizr'''
        optId=10003
        SelectNum = 30
        sex = int(para.get('sex',2)) #1男 2女

        lastnameList = Gcore.getCfg('tb_cfg_nickname').get(0)
        firstnameList = Gcore.getCfg('tb_cfg_nickname').get(sex)
        lastnameList = random.sample(lastnameList,SelectNum)
        firstnameList = random.sample(firstnameList,SelectNum)

        nicknames=[]
        for i in xrange(SelectNum):
            nickname = lastnameList[i]+firstnameList[i]
            nicknames.append(nickname)

        where = self.db.inWhere('NickName',nicknames)
        rows = self.db.out_rows('tb_user','NickName',where)
        existNickNames = [r['NickName'] for r in rows]
        notExistNickNames = list(set(nicknames)-set(existNickNames))
        
        #---------------------随机名称出敏感词 by lizr-----------------------
        NickNames = []
        for NickName in notExistNickNames:
            if Gcore.common.filterInput(NickName,2,16)<0:
                pass #过滤敏感词的名称
            else:
                NickNames.append(NickName)
                
        #--------------------------- 推荐阵营 ---------------------------
        userNum=self.db.out_field('tb_user','count(1)','1=1')/3
        # 推荐阵营算法 add by Yew
        if userNum>=20:
            for uc in range(1,4):
                ucNum=self.db.out_field('tb_user','count(1)','UserCamp=%s'%uc)
                if ucNum<userNum*0.8:
                    return Gcore.out(optId,{'RN':NickNames,'RC':uc,'RCKey':uc})
                
        uc = random.randint(1,3) #1:魏,2:蜀,3:吴
        #---------------------------------------------------------------
        
        return Gcore.out(optId,{'RN':NickNames,'RC':uc,'RCKey':uc})
        #return notExistNickNames
    
    #optId=10004
    def getRecCamp(self,optId):
        '''推荐阵营by zhanggh (将弃 by Lizr)'''
        userNum=self.db.out_field('tb_user','count(1)','1=1')/3
        
        # 推荐阵营算法 add by Yew
        if userNum>=20:
            for uc in range(1,4):
                ucNum=self.db.out_field('tb_user','count(1)','UserCamp=%s'%uc)
                if ucNum<userNum*0.8:
                    return Gcore.out(optId,{'RC':uc,'RCKey':uc})
        import random
        uc = random.randint(1,3) #1:魏,2:蜀,3:吴
        result = {'RC':uc,'RCKey':uc}
        return Gcore.out(optId,result)
    
    #optId=10005
    def checkNickNameValid(self,p={}):
        '''验证昵称合法性'''
        optId = 10005
        nickName = p.get('NickName')
        PlayerCfg = Gcore.loadCfg(Gcore.defined.CFG_PLAYER)
        nickNameMin = PlayerCfg.get('NickNameMin')
        nickNameMax = PlayerCfg.get('NickNameMax')
        
        flag=filterInput(nickName,nickNameMin,nickNameMax)
        if flag==-1:
            return Gcore.error(optId,-10005993)#字数字数限制
        elif flag==-2:
            return Gcore.error(optId,-10005991)#特殊字符
        elif flag==-3:
            return Gcore.error(optId,-10005992)#敏感字
        #验证用户昵称
        hasSameName = self.db.out_field('tb_user','Count(1)',"NickName='%s'"%nickName)
        if hasSameName:
            return Gcore.error(optId,-10005001)#用户昵称已存在
        return Gcore.out(optId,{})
        
    def getUserIdByAccount(self,aId):
        '''根据平台用户Id查主角ID by zhanggh'''
        return self.db.out_field('tb_user','UserId','AccountId=%s'%aId) #order by logintime limit 0,1

#     def getUserId(self,mac):
#         UserId =  self.db.out_field('temp_tb_mac','UserId',"Mac='"+mac+"'")
#         #print self.db.sql
#         if UserId:
#             self.uid = UserId
#         return UserId
 
#     def RegisterUser(self,mac,para={'NickName':'','UserCamp':1,'UserIcon':1}):
#         print 'RegisterUser'
#         data = {"Mac":mac}
#         MacId = self.db.insert('temp_tb_mac',data)
#         UserId = self.CreateUser(para)
# 
#         self.db.update('temp_tb_mac',{"UserId":UserId},"MacId="+str(MacId))
#         print self.db.sql
#         return UserId
    
    def CreateUser(self,para={'NickName':'','UserCamp':0}): 
        '''创建用户默认数据
        #**param获取用户自定义的昵称，阵营等信息
        '''
        import random
        optId = 10002
        buildCfg = Gcore.loadCfg(CFG_BUILDING)
        userCamp = para['UserCamp']
        if userCamp==0:
            userCamp = random.randint(1,3) #1:魏,2:蜀,3:吴
        
        ctime = Gcore.common.datetime()
        data = {'CreateTime':ctime,'GoldCoin':buildCfg['InitGoldCoin'],\
                'WorkerNumber':buildCfg['InitWorkerNum'],'UserHonour':0,\
                'VipLevel':0,'NickName':para['NickName'],\
                'UserCamp':userCamp,'UserIcon':para.get('UserIcon',1),\
                'AccountId':para.get('TotalServiceId',0),\
                'OldAccount':para.get('OldAccount'),
                'ProtectEndTime':time.time()-5
                }
        UserId = self.db.insert('tb_user',data)
        self.uid = UserId
        playerMod = Gcore.getMod('Player', UserId)#此处会为用户获取新的连接
        playerMod.initUser() 
        
        #是否选择推荐阵营
        if userCamp==int(para.get('RCKey',0)):
            playerMod.sendCampGift(optId,userCamp)#发放奖励

        return UserId
    
    

    
    
if __name__ == '__main__':
    c = Login()
    #userNum=c.db.out_field('tb_user','count(1)','1=1')/3
    #print '========================='
    #print userNum
    #uid = c.getUserIdByAccount('72')

#     tokenDict = {u'TotalServiceId': u'47', u'LoginMode': 2, u'PlayerId': 0, u'LoginVersion': u'101', u'Lan': 1, u'LockTime': 1370345148}
#     uid = c.getUserIdByAccount(tokenDict.get('TotalServiceId'))
#     print 'uid',uid
#    print c.getUserInfo(10132)
#    print c.LoginAccount({'uid':1011})
#    print c.LoginAccount({"TotalServiceId":"55"})
    #buildingCfg = Gcore.loadCfg(CFG_BUILDING)
    #print buildingCfg
#    print c.LoginAccount({"AccountId":9999,'uid':43262})
#    print c.getRecCamp(12333)
#    print c.LoginAccount({"mac":"C1DSScS"})
#    print c.LoginAccount({"mac":"E1DSScS"})
#    print c.LoginAccount({"mac":"Y1DSScS"})
#    print c.LoginAccount({"mac":"L1DSScS"})
#    print c.LoginAccount({"mac":"P1DSScS"})
#    print c.LoginAccount({"mac":"U1DSScS"})
#    print c.LoginAccount({"mac":"ADSScS"})
#    print c.LoginAccount({"uid":1006})
#    d = c.PlayerInfo(1001)
#    print d
#     print c.CreateUser()
#    print c.CreateRole({'TotalServiceId':9999,'NickName':'sx999','UserCamp':1,'UserIcon':2})
#    for key in c.randomName({'sex':'2'}):
#        print key
#optId = 10002
    c.randomName()

#    p = {'TotalServiceId':1,'NickName':'nnnnn4','UserCamp':1,'UserIcon':1}
#     print c.checkNickNameValid(p)
# 
#    print c.CreateUser(p)

                            
