# -*- coding:utf-8 -*-
# author:zhanggh
# date:2013-3-8
# 模块说明

import sys
import time
from sgLib.core import Gcore

'''协议号定义
1         心跳(预留)
101~999   推送(预留)
1001~9999 系统(预留)

10001~10019 登录
10021~10029 登录后
13051-13059 主角：VIP
15061-15069 主角：背包
11001~11999 聊天

建筑:
15006~15008 招贤馆
15010~15019 点将台  (15010-15019)
15020~15029 祭坛
15030~15049 兵营、工坊、佣兵处
15050~15059 书院
15060~15089 外史院(军团)
15090~15099 武馆
15100~15109 校场
15110~15119 将军府
15120-15129 演武场
15130-15139 招贤馆 - 名将坊

16000~16999 装备系统
18000~18999 邮件系统
19001~19999 好友系统
20001~20999 道具系统
21001~21999 拜访系统
22001~22999 任务系统
23001~23999 活动系统
24001~24999 比武系统 - 演武场
30001~30999 缓存

战斗
90001~90999 战斗动作
91001~91999 战役信息
92001~92999 布防
93001~93999 攻城
94001~94999 比武
98001~98999 竞技


'''
#格式：协议号:('UI名称','方法名称')
class proManager(object):
    
    mappingDict = {
       #登录接口，暂时
#       10091:('Login','Register'),#注册
#       10092:('Login','AccountLogin'),#账号切换
#       10093:('Login','MainLogin'),#切换分服登录
#       10094:('Login','GetServerList'),#服务器列表
#       10095:('Login','CheckValid'),#检查账号是否可用

       10021:('Login','LoginInfo'), #登录后获取信息汇总
       10022:('Login','FirstLogin'), #不再是新号,选完军师之后前台访问
       
       11001:('Chat','Say'), #聊天
       
       #主角
       13001:('Player','WorkerExpand'), #购买工匠
       13002:('Player','GetHonRanking'), #荣誉值排行榜
       13003:('Player','GetBaseInfo'), #用户信息
       13004:('Player','GetPlayerInfo'), #获取主角登录信息
       13005:('Player','SetArmyAdviserId'), #记录玩家所选军师
       13006:('Player','SetGuideProcessId'), #记录玩家指引进度
       
       #主角：VIP充值
       13051:('Player','PayForGold'),#充值
       13052:('Player','GetVipInfo'),#获取Vip信息
       #主角：背包
       13061:('Bag','GetGoods'),#查看背包物品
       13062:('Bag','MoveGoods'),#调整物品位置
       13063:('Bag','ExpandBag'),#扩展背包格仔数
       
       #地图
       14001:('Map','getScene'),#地图：获取场景
       14002:('Map','BuyMap'), #地图：购买地图
       
       #建筑通用
       15001:('Building','CreateBuilding'),#建筑创建建筑
       15002:('Building','UpgradeBuilding'),#建筑升级
       15003:('Building','CancelBuilding'),#建筑取消
       15004:('Building','SpeedupProcess'),#加速建造
       15901:('Building','MoveBuilding'),#移动建筑
       
       #招贤馆
       15006:('Building_pub','GetInviteUI'),#招贤馆:招募界面
       15007:('Building_pub','InviteGenerals'),#招贤馆:招募武将
       15008:('Building_pub','SpeedupInvite'),#招贤馆:黄金加速刷新
       
       15131:('Building_pub','ExchangeGeneralCard'),#名将坊:兑换武将
       15132:('Building_pub','GetPatchNum'),#名将坊:主界面
       15133:('Building_pub','ConvertGeneralCard'),#招贤馆:将武将卡转换成晶石
       
       
       #军需所，铸币厂
       15005:('Building_resource','CollectCoin'), #军需所，铸币厂: 收集资源
       15009:('Building_resource','GetStorage'), #军需所，铸币厂：获取数量
       
       #点将台
       15010:('Building_train','TrainGeneral'),#点将台: 培养武将
       15011:('Building_train','SaveTrain'),#点将台：保留培养的属性
       15012:('Building_train','DeleteGeneral'),#点将台：遣散武将
       15013:('Building_train','GetGenerals'),#点将台：获取武将信息
       15014:('Building_train','GetTrainNum'),#点将台：获取武将信息
       15015:('Building_train','ChangeEquip'),#点将台：给武将穿装备或更换武将装备
       15016:('Building_train','StripEquip'),#点将台：将武将某个部位的装备脱下来
       
       #祭坛
       15020:('Building_altar','GetLotteryCnt'),#获取天坛或地坛某天的抽奖次数
       15021:('Building_altar','Lottery'),#抽奖
       15022:('Building_altar','GetAltarRank'),#获取幸运榜
       15023:('Building_altar','GetLotteryLog'),#获取抽奖记录
       15024:('Building_altar','GetNextLoterryPay'),#获取下次抽奖花费
       
       #兵营，工坊，佣兵处
       #15030:('Building_camp','GetSpawnInfo'), # 兵营：获取征兵信息 
       #                                        # + 或 工坊：获取制造信息
       #15031:('Building_camp','SetCurNum'), # 兵营：设置征兵数量
       #                                     # + 工坊：设置器械数量
       #15032:('Building_camp','SpeedUpTraining'), # 兵营：加速征兵 
       #                                           # + 或 工坊：加速制造
       #                                           # + 或 佣兵处：雇佣
       #15035:('Building_camp','GetHireNum'),#兵营：获取当天雇佣数量
       
       
       15030:('Building_camp','GetSpawnNum'), # 兵营
       15031:('Building_camp','FullAddSoldier'), # 兵营
       15032:('Building_camp','ExchangeSoldier'), # 兵营
       15033:('Building_camp','HireSoldier'), # 兵营
       15034:('Building_camp','GetHireNum'),#兵营

       
       #书院
       15050:('Book','GetUpgradingTech'),#书院：查询正在学习中的科技
       15051:('Book','GetMyTech'),#书院：获取我学习的所有科技
       15052:('Book','UpgradeTech'),#书院：学习科技
       15053:('Book','SpeedUpTech'),#书院：加速科技
       
       #校场
       15100:('Building_school','GetSchoolInfo'),#校场:获取校场信息
       15102:('Building_school','MoveGeneral'),#校场：移动物降
       15103:('Building_school','ChangeSoldierNum'),#校场：改变武将带兵数量
       
       #将军府
       15110:('Building_home','GetInters'),#查询内政影响
       15111:('Building_home','GetAchievements'),#查询我的成就
       15112:('Building_home','GetReward'),#领取成就奖励
       

    
       #武馆
       15090:('Building_ground','PractiseGeneral'),#武馆，训练武将
       15091:('Building_ground','SpeedUpPractise'),#武馆，加速训练
       15092:('Building_ground','GetPractiseInfo'),#武馆，获取训练信息
       15093:('Building_ground','RapidPractise'),
       15094:('Building_ground','SpeedRapidPractise'),
       
       #外史院 
       15060:('Building_club','CreateClub'),#创建军团
       15061:('Building_club','Devote'),#贡献
       15062:('Building_club','GetMyClub'),#获取我的军团信息
       15063:('Building_club','GetClubList'),#获取可加入军团列表
       15064:('Building_club','ApplyClub'),#申请加入
       15065:('Building_club','ModifyClub'),#修改军团信息
#       15066:('Building_club','GetMemberList'),#获取军团成员列表
       15067:('Building_club','SetClubLeader'),#任命团长
       15068:('Building_club','DismissMember'),#开除成员
#       15069:('Building_club','GetApplyList'),#获取申请列表
       15070:('Building_club','AgreeApply'),#同意申请
       15071:('Building_club','RefuseApply'),#拒绝申请
       15072:('Building_club','ExitClub'),#退出军团
       15073:('Building_club','GetCrewList'),#获取组内/申请列表
       15075:('Building_club','GetClubTechs'),#获取军团科技等级
       15076:('Building_club','UpgradeClubTech'),#升级军团科技
       15080:('Building_club','CheckClubExist'),#检查军团是否存在
       15082:('Building_club','OpenBox'),#开宝箱
       15083:('Building_club','GetBoxLogs'),#开宝箱获奖记录
       15084:('Building_club','GetDevoteLogs'),#开宝箱获奖记录
       
       #理藩院
       #15120:('Building_hold', 'SetBattleRecord'), #设置战斗记录
       15121:('Building_hold', 'SlaveOperand'), #对藩国进行操作-纳贡或释放
       15122:('Building_hold', 'SetHold'), #设置藩国
       15123:('Building_hold', 'GetHold'), #获取藩国
       15124:('Building_hold', 'GetDefeaters'), #获取手下败将
       15125:('Building_hold', 'GetHolder'), #获取主人
       15126:('Building_hold', 'GetRevent'), #获取反抗次数，反抗进度
       15127:('Building_hold', 'CheckGeneralSoldier'), #检查是否有武将上场和兵
       15128:('Building_hold', 'RefreshHoldState'), #自动解除藩国关时前台请求刷新
       15129:('Building_hold', 'IfShowRevolt'), #是否需要显示反抗按钮
       
       #铁匠铺
       16000:('Equip','GetStrengthNum'),#获取强化次数
       16001:('Equip','EquipStrengthen'),#装备强化
       16002:('Equip','BuyEquip'),#铁匠铺：购买装备
       16003:('Equip','BuyMyEquip'),#铁匠铺：回购装备
       16004:('Equip','SaleEquip'),#铁匠铺：出售装备
       16005:('Equip','GetShopEquips'),#铁匠铺：获取可回购装备
       16006:('Equip','DivertEquip'),# 装备传承
       16007:('Equip','HighEquipStrengthen'),#兵书宝物升级
       
       #邮件系统
       18001:('Mail','ListRelatedUser'),#返回玩家好友及军团成员数据
       18002:('Mail','DelMail'), #删除邮件
       18003:('Mail','MailList'), #收件箱/发件箱列表
       18004:('Mail','MailInfo'), #收件箱/发件箱中某邮件内容
       18005:('Mail','ReceiveAttachments'),#将附件添加到玩家背包中
       18006:('Mail','InsMessage'), #写邮件
       18007:('Mail','CountUnReadNum'), #获取未读邮件数
       
       #好友系统
       19001:('Friend','FriendList'),#获取好友列表
       19002:('Friend','ApplyList'),#获取好友申请列表
       19003:('Friend','HandleApply'),#处理好友申请
#       19004:('Friend','ApplyFriend'),#通过ID申请好友
       19005:('Friend','GetUserByRank'),#获取随即用户
       19006:('Friend','DeleteFriend'),#删除好友
       19007:('Friend','CheckFriend'),#查看好友
       19008:('Friend','CheckGeneral'),#查看武将
#       19009:('Friend','VisitFriend'),#访问好友
       19010:('Friend','ApplyFriendByName'),#通过昵称申请好友
       19011:('Friend','CountApply'),#获取好友申请数量
       19012:('Friend','CountFriendGeneral'),#获取好友的武将数
       
       #道具系统
       20001:('Item','Exchange'),#兑换货币
       20002:('Item','BuyResource'),#按购买资源
#        20003:('Item','SaleItem'),#出售道具
       20004:('Item','UseItem'),#使用道具
#        20005:('Item','UseFlower'),#使用鲜花
       20006:('Item','BuyItemEquip'),#购买道具&装备
       
       #拜访系统
       21001:('Visit','Visit'),#拜访玩家
       21002:('Visit','OpenBox'),#开宝箱
       21003:('Visit','GeneralInteract'), #武将交流
       21004:('Visit','SendFlowers'),#送花
       21005:('Visit','GetGeInteractLog'),#获取武将交流记录和奖励
#       21006:('Visit','GetGeInteractAward'),#获取武将交流奖励
       
       #任务系统
       22001:('Mission','GetMissionList'),#获取任务列表
       22002:('Mission','CheckMission'),#察看任务
       22003:('Mission','GetReward'),#获取任务奖励
       22004:('Mission','EventTrigger'),#任务事件触发
       22005:('Mission','CheckMissionStatus'),#检查任务状态
       
       #活动系统
       23001:('Activity','GetActivitiesUI'),#获取已开通活动
       23002:('Activity','GiftList'),#获取通用礼包记录
       23003:('Activity','GetGift'),#领取通用礼包奖励
       23004:('Activity','GetRechargeUI'),#获取首冲奖励信息
       23005:('Activity','GetRechargeReward'),#领取首冲奖励
       23006:('Activity','GetSignInLog'),#获取签到日志
       23007:('Activity','SignIn'),#补签 操作
       23008:('Activity','Lucky'),#鸿运当头活动抽奖
       23009:('Activity','GetLuckyLog'),#获取鸿运当头活动抽奖记录
       23010:('Activity','ShowLottory'),#显示在线奖励信息
       23011:('Activity','OnlineLottory'),#在线奖励抽奖
       23012:('Activity','GetActiveLog'),#活跃度奖励
       23013:('Activity', 'GetValidGift'),#可领取的礼物数量
       
       #比武-演武场
       24001:('RankFight','RankFightInfo'), #演武场主界面
       24002:('RankFight','SpeedupFightTime'), #加速比武冷却时间
       24003:('RankFight','GainRankReward'), #领取奖励

       #缓存
       30001:('Redis', 'OnCacheAll'), #缓存武将信息
       
       #战斗
       91001:('War','WarInfo'), #剧情(将弃)
       91002:('War','WarSweep'), #扫荡
       91003:('War','WarInfoAll'), #剧情(新)
       91004:('War','BuyActPoint'), #购买行动力
       91005:('War','WarSweepNew'), #新扫荡
       91006:('War','StopSweep'), #停止扫荡
       91007:('War','GetPointNum'), #获取行动点数
       
       #城墙 布防
       92001:('Wall','CreateWallDefense'), #创建防御工事
       92002:('Wall','MoveElement'), #批量移动元素
       92003:('Wall','DeleteWallDefense'), #拆除工事
       92004:('Wall','DefenseInfo'), #进入布防界面
       92005:('Wall','GeneralList'), #武将列表
       92006:('Wall','SetGeneral'), #布置武将上场
       92007:('Wall','RemoveGeneral'), #移除武将
       92008:('Wall','ChangeTypeGeneral'), #更换武将带兵类型
       92009:('Wall','BattleReport'), #战报
       92010:('Wall','GetWallDefenseNum'), #获取防御工事数量
       92011:('Wall','RepairWallDefense'), #修复防御工事
       92012:('Wall','CleanWallDefense'), #回收防御工事
       
       #测试
       99001:('Test','test'),  #测试1
       99002:('Test','test2'), #测试2 
       99003:('Test','test3'), #测试3
       99004:('Test','test4'), #测试4
       99005:('Test','test5'), #测试5
       
       #添加更多协议号,注添加协议号时应该按UI分组  并从小到大排列  
    }
    @staticmethod
    def checkOpt(uid,optId,para):
        '''将协议号定位于功能'''
        #global runtime_logger
        #global exception_logger
        print ' --> ps proManager.checkOpt',uid,optId
        if optId not in proManager.mappingDict:
            return Gcore.error(optId,-11111111) #协议号未定义,或程序未更新 
        try:
            startTime = time.time()
            mapInfo = proManager.mappingDict.get(optId)
            calledMethod = getattr(Gcore.getUI(mapInfo[0],uid),mapInfo[1])
            response = calledMethod(para)
            
            #if Gcore.TEST and Gcore.IsServer: #调试计时
            if True and optId not in [91005,99001,99002,99003,99004,99005,99006]: #扫荡不计 因为一次gevent.sleep(3.5) 
                try:
                    runtime = time.time() - startTime
                    #print '-------before log runtime---------'
                    db = Gcore.getNewDB()
                    row = {
                             'UserId':uid,
                             'OptId':optId,
                             'CallMethod':'%s.%s'%(mapInfo[0],mapInfo[1]),
                             'Param':Gcore.common.json_encode(para),
                             'Response':Gcore.common.json_encode(response),
                             'Runtime':runtime,
                             'RecordTime':Gcore.common.datetime(),
                             }
                    db.insert('temp_runtime_log', row, isdelay=True)
                    db.close()
                    #print '-------end log runtime---------'
                    #runtime_logger.info("%s\t%s\t%s\t%s\t%s\t%s\t%s" % map(str, [uid, optId, str((mapInfo[0],mapInfo[1])),
                    #                                                             Gcore.common.json_encode(para),
                    #                                                             Gcore.common.json_encode(response),
                    #                                                             runtime,
                    #                                                             Gcore.common.datetime()]))
                except:
                    pass
                
            
            return response
        except Exception,e:
            print '==Exception==',e
            mapInfo = proManager.mappingDict.get(optId)
            #if Gcore.TEST and Gcore.IsServer:
            if Gcore.IsServer:
                import traceback
                strExcept = traceback.format_exc()
                print >>sys.stderr, 'Time:' + time.strftime('%Y-%m-%d %H:%M:%S') + '\n' \
                        + 'UserId:' + str(uid) + '\n' \
                        + 'OptId:' + str(optId) + '\n' \
                        + 'Para:' + str(para) + '\n' \
                        + strExcept
                sys.stderr.flush()
                
                #strExcept = str(mapInfo[0])+'.'+str(mapInfo[1])+' >> '+str(e)+'\n'
                #strExcept = strExcept+('\n'.join(traceback.format_exc().splitlines()[-3:]))#最后三行traceback
                body = {'Exception':strExcept}
                #print '-------before log excetion---------'
                db = Gcore.getNewDB()
#                row = {
#                         'UserId':uid,
#                         'OptId':optId,
#                         'CallMethod':'%s.%s'%(mapInfo[0],mapInfo[1]),
#                         'Param':Gcore.common.json_encode(para),
#                         'Exception':strExcept,
#                         'RecordTime':Gcore.common.datetime(),
#                         }
#                db.insert('temp_exception_log', row, isdelay=True)
#                print 'db.sql',db.sql
                
                #OptId,Exception 为唯一 
                RecordTime = Gcore.common.datetime()
                CallMethod = '%s.%s'%(mapInfo[0],mapInfo[1])
                Param = Gcore.common.json_encode(para)
                strExcept = db.escape_string(strExcept)
                sql = "INSERT INTO temp_exception_log (OptId,Exception,RecordTime,CallMethod,UserId,Param)"
                sql += " VALUES ('%s','%s','%s','%s','%s','%s') ON DUPLICATE KEY UPDATE UserId='%s',ApearTimes=ApearTimes+1,RecordTime='%s'" \
                %(optId,strExcept,RecordTime,CallMethod,uid,Param,uid,RecordTime) 
                db.execute(sql,None,True)
                #print '-------end log excetion---------'
                #exception_logger.exception("%s\t%s\t%s\t%s\t%s\%s\t%s\t%s" % map(str, [optId,strExcept,RecordTime,CallMethod,uid,Param,uid,RecordTime])) 
            else:
                body = {}
                
#            if Gcore.TEST or True:
#                time.sleep(1)
#                raise  

            return Gcore.error(optId,-22222222,body) #程序运行错误


if __name__ == '__main__':
    """调试"""
    para = {}
    uid =  1003
    optId = 22002
    #Gcore.resetRuntime()
    proManager.checkOpt(uid,optId,{'MID':1005})
    #import time;time.sleep(3)
    import time;time.sleep(1)
