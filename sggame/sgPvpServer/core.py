#coding:utf8
#author:zhoujingjiang
#date:2013-5-9
#核心

#导入自定义模块
import PvpUI
import PvpMod

import RedisMod
import MySQLMod
import RabbitMod
import HonourMod
import McryptMod
import CfgReader
import MailSender

import common
import config
import pvp_common

class Gcore(object):
    PVP = PvpMod.pm #保存引用
    Redis = RedisMod.rm #保存引用
    MySQL = MySQLMod.mp #保存引用
    Cfg = CfgReader.cr #保存引用
    Mail = MailSender.ms #保存已用
    Pvp_common = pvp_common #保存引用
    Rabbit = RabbitMod.rm #保存引用
    clients = {} #保存在线用户的引用
    
    @staticmethod
    def start():
        '''开启游戏核心'''
        Gcore.Rabbit.start() #开启Rabbit
        Gcore.Redis.start() #开启Redis
    
    @staticmethod
    def log_out(uid, sid):
        '''用户下线处理'''
        #从竞技场房间中退出来
        Gcore.PVP.leave_room(uid, sid)
        #从竞技场中退出
        Gcore.PVP.leave_arena(uid, sid)
    
    @staticmethod
    def end():
        '''关闭游戏核心'''
        #关闭RabbitMQ
        Gcore.Rabbit.kill()
        #关闭Redis
        Gcore.Redis.kill()
    
    @staticmethod
    def multicast(users, content=None):
        '''组播'''
        #users - (userid, serverid) or [(userid1, serverid1), ...]
        try:
            if isinstance(users, tuple):
                users = [users]

            print '要发送的用户', users
            snd_cnt = 0 #发送的客户端个数
            content = common.encodePacket(content) #对封包发送前的处理，在此处。
            assert isinstance(content, basestring), '发送的内容应是字符串'
            for user in users:
                if user in Gcore.clients:
                    Gcore.clients[user]['channel']._send(content)
                    print 'send to', user, 'content', content
                    print '-' * 20
                    snd_cnt += 1
            return snd_cnt #返回发送的客户端数量
        except Exception:
            return False #组播失败，返回False。

    @staticmethod
    def arena_start(sn=None, fo=None):
        '''启动竞技场'''
        print 'arena_start'
        Gcore.PVP.arena_start()
    
    @staticmethod
    def arena_end(sn=None, fo=None):
        '''关闭竞技场'''
        print 'arena_end'
        Gcore.PVP.arena_end()
        
    @staticmethod    
    def reload_userdefined_mod(sn=None, fo=None):
        '''reload自定义模块'''
        print 'reload_userdefined_mod'
        try:
            reload(PvpMod)
            reload(RedisMod)
            reload(MySQLMod)
            reload(common)
            reload(config)
            reload(CfgReader)
            reload(MailSender)
            reload(PvpUI)
            reload(pvp_common)
            reload(RabbitMod)
            reload(McryptMod)
            reload(HonourMod)
            return True
        except Exception, e:
            print str(e)
            return False

    @staticmethod
    def pro_manager(uid, sid, optId, para):
        '''协议管理'''
        try:
            if optId == 98001: #进入房间
                return PvpUI.EnterRoom(optId, uid, sid, **para)
            elif optId == 98002: #离开房间
                return PvpUI.LeaveRoom(optId, uid, sid, **para)
            elif optId == 98003: #离开竞技场
                return PvpUI.LeaveArena(optId, uid, sid, **para)
            elif optId == 98004: #广播战斗信息
                return PvpUI.MultiCastOpt(optId, uid, sid, **para)
            elif optId == 98005: #战斗结束
                return PvpUI.ArenaEnd(optId, uid, sid, **para)
            elif optId == 98007: #获取本周所得荣誉
                return PvpUI.GetWeekHonour(optId, uid, sid, **para)
            
            elif optId == 98997: #重载自定义模块
                stat = Gcore.reload_userdefined_mod()
                if not stat: #重载自定义模块发生异常
                    return common.error(optId, -98997001)
                else: #成功重载自定义模块
                    return common.out(optId)
            elif optId == 98996: #开启竞技场
                Gcore.arena_start()
                return common.out(optId)
            elif optId == 98995: #关闭竞技场
                Gcore.arena_end()
                return common.out(optId)
            else: #未定义的协议号
                return common.error(98998, -98998001)
        except Exception, e: #运行程序时，出现异常。
            print e
            return common.error(98999, -98999001)
        finally:pass
#end class Gcore

Gcore.arena_start()
