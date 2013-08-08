#coding:utf8
#author:zhoujingjiang
#date:2013-5-9
#竞技场模型

####################################
#将进入竞技场的等待队列比喻成进入房间#
#将竞技场的战斗比喻成在竞技场内               #
####################################

import time
import random
import uuid
import itertools
import weakref
import math

import gevent
from gevent_zeromq import zmq
from getfreeport import getfreeport

import config
import common
import pvp_common
from CfgReader import cr
import RabbitMod
import HonourMod

class PvpMod(common.Singleton): #单例模式
    _inited = False
    def __init__(self):
        if not self.__class__._inited:
            self.arena_metadata_init()
            self.__class__._inited = True

    def arena_metadata_init(self):
        '''初始化竞技场元数据'''
        self._arena_started = 0 #竞技场：0未开始，非0开始
        self._grep_let = None #匹配协程
        self._arena_members = [{}, {}, {}, {}] # 竞技场的三个房间
                            # + （第一个字典没用，目的是使房间类型与索引相同）
        self._arena_objs = {} #战斗对象集合
                            # + 例子：{(userid, serverid):战斗对象,...}
    def is_in_arena(self, uid, sid):
        '''是否在竞技场'''
        # 不在，返回False；在，返回战斗对象的弱引用
        try:
            return weakref.ref(self._arena_objs.get((uid, sid)))
        except Exception:
            return False

    def leave_arena(self, uid, sid):
        '''退出竞技场'''
        if (uid, sid) in self._arena_objs:
            self._arena_objs[(uid, sid)].leave_fight(uid, sid)
            del self._arena_objs[(uid, sid)] #删除战斗对象的引用
            return True
        return False #不在竞技场中
    
    def leave_room(self, uid, sid):
        '''退出房间'''
        #在房间中则退出，不在返回False。
        for room in self._arena_members:
            if (uid, sid) in room: #在房间中
                del room[(uid, sid)]
                return True
        return False #不房间中
    
    def is_in_room(self, uid, sid):
        '''是否在房间'''
        return (uid, sid) in itertools.chain(*self._arena_members)
    
    # uid - 玩家ID，sid - 服务器ID，lv - 玩家等级，et - 进竞技场的时间，
    # + typ - 竞技场类型，info - 包含武将，科技，用户信息的字典
    def enter_room(self, uid, sid, lv, et, friends, typ, info):
        '''进入房间'''
        if not self._arena_started:
            return -1 #竞技场尚未开始
        self.leave_arena(uid, sid) #如果在其他房间中，先退出。
        try:
            assert isinstance(info, dict) and \
                    isinstance(info.get('User'), dict) and \
                    isinstance(info.get('Generals'), (list, tuple)) and \
                    isinstance(info.get('Techs'), dict), \
                    '%s' % str(info)
            assert typ in [1, 2, 3], 'typ = %s' % typ
            self._arena_members[typ][(uid, sid)] = {'UserLevel':lv, 'EnterTime':et, 
                                                    'info':info, 'Friends':friends}
            return 1
        except Exception, e:
            print '进入竞技场失败：', e
            return -2 #进入房间失败
        
    def arena_start(self):
        self.arena_metadata_init()
        self._arena_started = 1
        #开起匹配循环
        self._grep_let = gevent.spawn(self.grep_users)
    
    def arena_end(self): #关闭竞技场
        if hasattr(self._grep_let, 'kill'):
            self._grep_let.kill()
        self.arena_metadata_init()

    def best_choice(self, user, group1, group2, typ):
        '''尝试选出好友，如果没有，随机选择'''
        candidate = sorted([(k, self._arena_members[typ][user]['Friends'][str(k[0])]) 
         for k in self._arena_members[typ] 
         if k[1]==user[1] and 
         str(k[0]) in self._arena_members[typ][user]['Friends']
         and k not in group1 + group2], key=lambda t:t[1], reverse=True)
        if candidate:
            elected = candidate[0][0]
            group1.append(elected)
        else: #没有好友在竞技场，随机选出一个
            elected = [u for u in self._arena_members[typ] 
                       if u not in group1 + group2]
            elected = random.choice(elected)
            group1.append(elected)
        return elected
    
    def best_choice_with_level(self, user, group1, group2, diff, typ):
        '''加上等级限制'''
        for ind in [5, 10, 15]: #先尝试从好友里选满足等级的
            candidate = sorted([(k, self._arena_members[typ][user]['Friends'][str(k[0])]) 
                        for k in self._arena_members[typ] 
                        if k[1]==user[1] and 
                        str(k[0]) in self._arena_members[typ][user]['Friends'] 
                        and diff -ind <= self._arena_members[typ][k]['UserLevel'] <= diff +ind
                        and k not in group1 + group2],
                        key=lambda t:t[1], reverse=True
                       )
            if candidate:
                group2.append(candidate[0][0])
                return group1 + group2
        for ind in [5, 10, 15]: #没有则找满足等级的
            candidate = [user for user in self._arena_members[typ] 
                         if diff -ind <= self._arena_members[typ][user]['UserLevel'] <= diff + ind
                         and user not in group1 + group2]
            if candidate:
                group2.append(candidate[0])
                return group1 + group2
        return False
            
    #在调用之前，保证房间中至少有 2*typ 个玩家。        
    def choice_users(self, typ): #typ - 房间类型:1,2,3
        '''随机选择用户，生成匹配组'''
        self.rm_expire_users() #先将过期玩家删除了
        if typ == 1: #1v1
            user1 = random.choice(self._arena_members[typ].keys()) #先随机选出一个
            diff = self._arena_members[typ][user1]['UserLevel']
            for ind in [5, 10, 15]:
                elected = [user for user in self._arena_members[typ] 
                           if diff - ind <= self._arena_members[typ][user]['UserLevel'] 
                            <= diff + ind and user != user1]
                if elected:
                    return [elected[0], user1]
            return False
        
        group1 = []; group2 = []
        #先随机选出两个
        first_pair = random.sample(self._arena_members[typ], 2)
        group1.append(first_pair[0]); group2.append(first_pair[1])
        
        if typ == 2: #2v2
            #尝试从好友中选组内的其他成员
            elected = self.best_choice(first_pair[0], group1, group2, typ)
            #1组的两位的级别的和 与 二组的唯一的一位的差
            lv1 = sum([self._arena_members[typ][user]['UserLevel'] for user in group1])
            lv2 = sum([self._arena_members[typ][user]['UserLevel'] for user in group2])
            diff = lv1 - lv2
            return self.best_choice_with_level(first_pair[1], group1, group2, diff, typ)
        if typ == 3: #3v3
            #尝试找好友
            elected = self.best_choice(first_pair[0], group1, group2, typ)
            elected = self.best_choice(elected, group1, group2, typ)
                
            elected = self.best_choice(first_pair[1], group2, group1, typ)
            #计算第一组的三位的级别的和 与 第二组的两位的级别的和的差            
            lv1 = sum([self._arena_members[typ][user]['UserLevel'] for user in group1])
            lv2 = sum([self._arena_members[typ][user]['UserLevel'] for user in group2])
            diff = lv1 - lv2
            return self.best_choice_with_level(elected, group1, group2, diff, typ)

    def rm_expire_users(self):
        '''将过期用户从房间删除'''
        curtime = time.time()
        
        for room in self._arena_members:
            expire_users = []
            for user in room:
                if curtime - room[user]['EnterTime'] > 30 * 60: #等待时长 ##读配置
                    expire_users.append(user) 
            for expire_user in expire_users:
                del room[expire_user]
        
    def grep_users(self):
        '''匹配用户，生成战斗对象。'''
        while self._arena_started: #竞技场开放
            try:
                gevent.sleep(0) #避免hog cpu，切换协程。
                typ = random.choice([1, 2, 3]) #三种类型房间中，随机选一个。
                #如果房间人数小于（2 * 类型），人数不足。
                if len(self._arena_members[typ]) < 2 * typ:
                    continue
                
                all_fighters = self.choice_users(typ) #匹配结果
                if all_fighters == False: #匹配失败
                    continue
            except Exception, e:
                print str(e)
                print '程序运行错误'
            else: #生成战斗对象
                print '所有参加战斗的人', all_fighters
                print '生成一场战斗%s vs %s' % (str(all_fighters[0:typ]), str(all_fighters[typ:]))
                print '战斗类型是', typ, 'vs', typ
                
                ArmyInfo = {}
                UserInfo = {}
                PosId = 1
                
                for ind, pair in enumerate(all_fighters):
                    gid = 1 if ind < typ else 2
                    uid, sid = pair
                    Generals = self._arena_members[typ][pair]['info']['Generals']
                    Techs = self._arena_members[typ][pair]['info']['Techs']
                    
                    army = pvp_common.getArmyInfo(typ, sid, uid, gid, PosId, Generals, Techs)
                    ArmyInfo.update(army)                    
                    
                    UserInfo[pair] = self._arena_members[typ][pair]['info']['User']
                    UserInfo[pair]['BeginX'] = cr.get_cfg('tb_cfg_pvp_pos', (typ, PosId), 'BeginX')
                    UserInfo[pair]['BeginY'] = cr.get_cfg('tb_cfg_pvp_pos', (typ, PosId), 'BeginY')
                    UserInfo[pair]['GroupId'] = gid
                    
                    PosId += 1

                ao = ArenaObj(typ, ArmyInfo, UserInfo) #生成一个公共的战斗对象
                for pair in all_fighters:
                    self._arena_objs[pair] = ao #这场战斗的参战人员，可以操作这个战斗对象。
                    del self._arena_members[typ][pair] #从房间中移除
#end class ArenaMod

class ArenaObj(object):
    '''竞技场对象'''
    __zmq_ctx = zmq.Context() #初始化zmq

    def __init__(self, typ, armyinfo, userinfo):
        self._typ = typ #类型
        self._armyinfo = armyinfo #部队信息
        self._userinfo = userinfo #用户信息
        self._duration = self.get_time_by_type(typ) #战斗时长
        self._id = str(uuid.uuid1()) #战斗唯一标识符
        self.leavers = [] #离开战斗的人
        self.army_avg_lv = self.army_level_avg()
        print '平均等级', self.army_avg_lv
        self.__zmq_sock = self.__class__.__zmq_ctx.socket(zmq.PUB) #生成zmq socket
        while 1:
            try:
                self.freeport = getfreeport() #获取一个随机未被占用的端口
                self.__zmq_sock.bind("tcp://%s:%s"%(config.ZMQ_SERVER_HOST, self.freeport)) #绑定
            except Exception, e:
                print e
            else:
                print 'zmq服务器启动成功@PORT:%s' % self.freeport
                break #退出循环
        self._starttime = int(time.time()) #战斗对象生成时间
        
        #组播给客户端：战斗初始信息。
        body = {}
        body["armyInfo"] = armyinfo
        body['userInfo'] = {}
        for uid, sid in userinfo:
            body['userInfo'][uid] = {}
            body['userInfo'][uid].update(userinfo[(uid, sid)])
            body['userInfo'][uid]['ServerId'] = sid
        body['startTime'] = self._starttime
        body['duration'] = self._duration
        body['mapId'] = self._typ #战斗类型 与 地图类型相同
        body['channelId'] = 1
        body['zmqIP'] = config.ZMQ_SERVER_HOST
        body['zmqPort'] = self.freeport
        body['armyNum'] = len(self._armyinfo) #参战的军队数量
        content = common.out(98006, body) #战斗匹配成功的协议号98006
        print '开始组播战斗开始信息'
        self.sock_multicast(0, content)
        
    def zmq_sock_close(self):
        '''关闭zmq端口'''
        if hasattr(self.__zmq_sock, 'close'):
            self.__zmq_sock.close()
    
    def __del__(self):
        '''析构函数'''
        self.zmq_sock_close() #释放端口
        
    def leave_fight(self, uid, sid):
        '''将玩家军队信息删除'''
        self.leavers.append((uid, sid))
        
    def is_fight_over(self):
        '''是否已分胜负'''
        #如果胜负未分，返回0。胜负已分，返回胜利的GroupId（1或2）。
        group1_tag = group2_tag = True
        for army in self._armyinfo:
            if str(army).strip().startswith('1') and \
                self._armyinfo[army].get("cur_armyLife", None) != 0:
                print '1有士兵没死光'
                group2_tag = False #1组军队没全部死掉，则2组没取得胜利。
            elif str(army).strip().startswith('2') and \
                self._armyinfo[army].get("cur_armyLife", None) != 0:
                print '2有士兵没死光'
                group1_tag = False #2组军队没全部死掉，则1组没取得胜利。
            else: pass
        return (1 if group1_tag else (2 if group2_tag else 0))
        
    def is_time_out(self):
        '''是否超时'''
        #超时返回True，否则返回False。
        return (True if time.time() > 
        self._starttime + self._duration else False)
        
    def soldier_lose(self):
        '''计算士兵损失'''
        soldier_lose = {}
        for army in self._armyinfo:
            army_life = self._armyinfo[army].get("armyLife", 0)
            cur_army_life = self._armyinfo[army].get("cur_armyLife", 0)
            soldier_num = self._armyinfo[army].get("soldierNum", 0)
            userid = self._armyinfo[army].get("armyUserId")
            soldier_type = self._armyinfo[army].get("soldierType")
            if not userid or not soldier_type:
                continue
            lose = soldier_lose.setdefault(userid, {})
            lose[soldier_type] = lose.get('soldier_type', 0) \
                + int(math.ceil((army_life-cur_army_life)/(army_life+0.0) * soldier_num))
        return soldier_lose
    
    def user_level_diff(self):
        '''两组的等级差''' #1组 - 2组。
        total_group1_level = [self._userinfo[user]['UserLevel'] for user in self._userinfo \
                              if self._userinfo[user]["GroupId"] == 1]
        total_group2_level = [self._userinfo[user]['UserLevel'] for user in self._userinfo \
                              if self._userinfo[user]["GroupId"] == 2]
        return sum(total_group1_level) - sum(total_group2_level)
    
    def army_level_avg(self):
        '''计算武将的平均等级和士兵的平均等级'''
        general_level = {0:0.0,1:0.0,2:0.0} #0-双方的平均等级
        soldier_level = {0:0.0,1:0.0,2:0.0}
        group1_member_num = group2_member_num = 0
        for army in self._armyinfo:
            if str(army).strip().startswith('1'):
                general_level[1] += self._armyinfo[army]['generalLevel']
                soldier_level[1] += self._armyinfo[army]['soldierLevel'] + 1
                group1_member_num += 1
            else:
                general_level[2] += self._armyinfo[army]['generalLevel']
                soldier_level[2] += self._armyinfo[army]['soldierLevel'] + 1
                group2_member_num += 1
            general_level[0] += self._armyinfo[army]['generalLevel']
            soldier_level[0] += self._armyinfo[army]['soldierLevel'] + 1
        
        print 'general_level', general_level
        print 'soldier_level', soldier_level
        general_level[0] = general_level[0] / (group1_member_num + group2_member_num)
        soldier_level[0] = soldier_level[0] / (group1_member_num + group2_member_num)
        general_level[1] = general_level[1] / group1_member_num
        soldier_level[1] = soldier_level[1] / group1_member_num
        general_level[2] = general_level[2] / group2_member_num
        soldier_level[2] = soldier_level[2] / group2_member_num
        
        return {'general_avg_level':general_level, 'soldier_avg_level':soldier_level}
    
    def gain_honour(self, groupid):
        '''计算获得的荣誉'''
        if not groupid in [1, 2]:
            return False
        diff = self.user_level_diff()
        diff = diff if groupid == 1 else -diff
        print 'diff', diff
        base_honour = cr.get_cfg('tb_cfg_honour', diff, 
                                 'P%sv%s'%(self._typ, self._typ))
        print 'P%dv%d'%(self._typ, self._typ)
        print 'base_honour', base_honour
        modify = self.army_avg_lv['general_avg_level'][groupid] / \
                    self.army_avg_lv['general_avg_level'][0] * \
                    self.army_avg_lv['soldier_avg_level'][groupid] / \
                    self.army_avg_lv['soldier_avg_level'][0]
        honour = base_honour * (2 - modify)
        return 2 if honour <= 2 else honour

    def fight_over(self):
        '''战斗结束'''
        curstate = self.is_fight_over()
        #if not curstate and not self.is_time_out():
        #    return False #战斗既未分胜负，又未超时。
        print '胜利者是', curstate
        honour = self.gain_honour(curstate)
        if not curstate:
            honour = 0 #双方失败，获得的荣誉是0。

        ret_dic = {}
        loses = self.soldier_lose()
        for user in loses:
            serverid, userid = map(int, user.split('.'))
            if (userid, serverid) in self.leavers:
                continue
            ret_dic[(userid, serverid)] = {}
            ret_dic[(userid, serverid)]['UserId'] = userid
            ret_dic[(userid, serverid)]['ServerId'] = serverid
            ret_dic[(userid, serverid)]["soldierLoses"] = loses[user]
            groupid = self._userinfo[(userid, serverid)]['GroupId']
            
            ret_dic[(userid, serverid)]['gainHonour'] = honour
            if groupid == curstate:
                ret_dic[(userid, serverid)]['isWinner'] = True
            else:
                ret_dic[(userid, serverid)]['isWinner'] = False
                ret_dic[(userid, serverid)]['gainHonour'] = 0
        return ret_dic
    
    def fight_end(self, fight_result): #内部用
        '''战后处理'''
        # 1，将战果广播给客户端
        # 2，将战果分发给各分服
        # 3，更新总服的荣誉表
        from core import Gcore
        for user in fight_result:
            Gcore.multicast(user, common.out(98005, fight_result[user]))
            RabbitMod.rm.send(98005, user[1], fight_result[user])
            HonourMod.addHonour(user[0], user[1], 
                                fight_result[user]['gainHonour'], time.time())
        self.zmq_sock_close() #释放端口

    def sock_multicast(self, frm, content):
        '''用socket组播战斗信息'''
        from core import Gcore
        
        #0表示发起者是服务器：对该战斗对象的所有成员进行广播
        if frm == 0:
            print '服务器发起的信息'
            return Gcore.multicast(self._userinfo.keys(), content)
        elif frm in self._userinfo: #发布者本人不广播
            users = [user for user in self._userinfo if user != frm]
            return Gcore.multicast(users, content)
        else: #不是战斗成员，广播失败
            return False 
    
    def zmq_muticast(self, body):
        '''用zmq组播战斗信息'''
        try: #1表示战斗
            snd_str = '1'+ ' ' + common.str2unicode(body)
            print 'zmq snd_str', snd_str
            self.__zmq_sock.send_unicode(snd_str)
            print 'zmq send end!'
        except TypeError, e:
            print 'zmq组播战斗信息，程序运行错误', str(e)
            return -1 #参数不正确
        except Exception, e:
            # 报警:发邮件
            # + todo
            print 'zmq组播战斗信息，发布失败', str(e)
            return -2 #zmq分发消息失败
        else:
            return 1 #成功
        
    def get_time_by_type(self, typ):
        '''获取战斗时长'''
        if typ == 1:
            return config.TIME_1V1
        elif typ == 2:
            return config.TIME_2V2
        else:
            return config.TIME_3V3
#end class ArenaObj

pm = PvpMod() #单例
