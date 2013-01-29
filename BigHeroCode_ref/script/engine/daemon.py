# -*- coding: utf8 -*-

import sys
import os, signal
import time
import traceback
import gc

import engine.util.my_json as json

#加载公共库
import util.msg_object    as msg_object
import util.timer_manager as timer_manager
import util.common        as common

#加载网络模块
import net.config as net_cfg
import net.trans  as net_trans
import net.cookie as cookie

#加载数据库模块
import db.instance  as db_ins

import config
import instance
import util.cglog as cglog

def exeTime(func):
    def newFunc(*args, **args2):
        t0 = time.time()
        cglog.getlogger().debug("@%s, {%s} start" % (time.strftime("%X", time.localtime()), func.__name__))
        back = func(*args, **args2)
        cglog.getlogger().debug("@%s, {%s} end" % (time.strftime("%X", time.localtime()), func.__name__))
        cglog.getlogger().debug("@%.3fs taken for {%s}" % (time.time() - t0, func.__name__))
        return back
    return newFunc
    
#对linux一些信号进行捕获
def hook_signal():
        if os.name != "nt":
                signal.signal(signal.SIGBUS,signal_handle)
                signal.signal(signal.SIGTERM, signal_handle)
                signal.signal(signal.SIGUSR1, signal_handle)
                signal.signal(signal.SIGUSR2, signal_handle)
                #屏蔽与终端控制有关的信号
                signal.signal(signal.SIGTTOU,signal.SIG_IGN)
                signal.signal(signal.SIGTTIN,signal.SIG_IGN)
                signal.signal(signal.SIGTSTP,signal.SIG_IGN)
                signal.signal(signal.SIGHUP ,signal.SIG_IGN)

#linux信号处理函数
def signal_handle(sign_num, frame):
        import signal
        if sign_num == signal.SIGBUS:
                pack_count_info = net_trans.get_pack_count_info()
                sys.exit(-1)
        elif sign_num == signal.SIGTERM:
                global daemon
                daemon.log("Server Terminal.")
                daemon.stop_service()
        elif sign_num == signal.SIGHUP:
                pass
        elif sign_num == signal.SIGUSR1:  #用户发送停止服务的指令
                daemon.log("Stop Service.")
                daemon.stop_service()
        elif sign_num == signal.SIGUSR2:
                #print "filename=%s;func_name=%s;line=%s" %(frame.f_lineno, frame.f_code.co_filename, frame.f_code.co_name)
                pass

#Daemon主类
class CDaemon(msg_object.CMsgObject):
        def __init__(self):
                super(CDaemon, self).__init__()
                self._func_stop = None
                
                self._is_running = False #是否正在执行主循环
                
                self._n_conn_count = 0 #连接计数
                
        #初始化
        def init(self):
                instance.init()
                
                net_trans.init()
                
                db_ins.init()
                
        def dlog(self, msg, *args):
                cglog.getlogger().debug(msg, *args)

        def log(self, msg, *args):
                cglog.getlogger().info(msg, *args)
        
        def get_conn_count(self):
                return self._n_conn_count
                
        def stop_service(self):
                #if self._n_conn_count > 0:
                #        return
                
                self._is_running = False
        
        #停止
        def stop(self):
                if self._func_stop:
                        self._func_stop()
                
                instance.stop()

                db_ins.stop()
                
                net_trans.stop()
                
        def set_stop(self, func):
                self._func_stop = func
                
        #主循环
        def main_loop(self):
                self._is_running = True
                
                self._n_conn_count = 0
                
                while self._is_running:
                        try:
                                net_trans.process()
                                
                                #新连接到达
                                new_conn_list = net_trans.get_new_conn_lst()
                                for new_conn_tuple in new_conn_list:
                                        conn = new_conn_tuple[0]
                                        type = new_conn_tuple[1]
                                        
                                        self._n_conn_count += 1
                                                
                                #只处理数据接收即可
                                recv_conn_list = net_trans.get_recv_conn_lst()
                                
                                for recv_conn in recv_conn_list:
                                        data = net_trans.recv_data(recv_conn)
                                        
                                        if not data:
                                                continue
                                        
                                        for detail in data:
                                                msg_id  = detail["msg_id"]
                                                content = detail["content"]
                                                
                                                #如未注册消息ID
                                                if not self._dict_msg_form.has_key(msg_id):
                                                        continue
                                                        
                                                try:
                                                        self._dict_msg_form[msg_id](recv_conn, content)
                                                except Exception, e:
                                                        if net_trans.msg_id_need_log(msg_id):
                                                                #仅出现错误时打印日志
                                                                dlog("[recv_msg] - msg_id:%s, content:%s", str(msg_id), json.dumps(content))
                                                            
                                                        dlog("%s", traceback.format_exc())
                                
                                #关闭连接
                                closed_conn_lst = net_trans.get_closed_conn_lst()
                                
                                for closed_conn in closed_conn_lst:
                                        self._n_conn_count -= 1
                                
                                self._n_conn_count = max(0, self._n_conn_count)
                                           
                                timer_manager.run()
                                
                                time.sleep(0.01)
                        except:
                                dlog("%s", traceback.format_exc())
                                
                                if __debug__:
                                        break
                                
                                        
                
daemon = CDaemon()

init = daemon.init

log = daemon.log

dlog = daemon.dlog

stop = daemon.stop

main_loop = daemon.main_loop

register_msg_handler = daemon.register_msg_handler

unregister_msg_handler = daemon.unregister_msg_handler

set_stop = daemon.set_stop
