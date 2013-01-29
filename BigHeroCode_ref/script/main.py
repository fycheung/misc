# -*- coding: utf8 -*-
#程序入口

import traceback

import engine.util.my_json as json

import engine.daemon as daemon
import engine.db.instance as db_ins
import engine.net.config as net_cfg
import engine.net.trans  as net_trans

import config

import message
import db_handler

def init():
        #注册账户系统相关处理
        daemon.register_msg_handler(message.MSG_DB_UPDATE_USER_GLOBAL, db_handler.work_update_user_global)
        daemon.register_msg_handler(message.MSG_DB_UPDATE_USER_SUMMARY, db_handler.work_update_user_summary)
        
        #注册用户系统相关处理
        daemon.register_msg_handler(message.MSG_DB_INSERT_USER_CHARACTER, db_handler.work_insert_user_character)
        daemon.register_msg_handler(message.MSG_DB_UPDATE_CHARACTER_ATT, db_handler.work_update_character_att)
        
        #注册宠物系统相关处理
        daemon.register_msg_handler(message.MSG_DB_DELETE_PET, db_handler.work_delete_pet)
        
        #注册任务系统相关处理
        daemon.register_msg_handler(message.MSG_DB_DELETE_QUEST, db_handler.work_query_delete_quest)
        
        #注册竞技场系统相关处理
        daemon.register_msg_handler(message.MSG_DB_UPDATE_ARENA, db_handler.work_update_arena)
        daemon.register_msg_handler(message.MSG_DB_INSERT_ARENA, db_handler.work_insert_arena)
        daemon.register_msg_handler(message.MSG_DB_REMOVE_FROM_ARENA, db_handler.work_remove_from_arena)
        
        #注册装备系统相关处理
        daemon.register_msg_handler(message.MSG_DB_UPDATE_EQUIPS, db_handler.work_update_user_equips)
        daemon.register_msg_handler(message.MSG_DB_DEL_EQUIPS, db_handler.work_del_equips)
        
        #注册邮件系统相关处理
        daemon.register_msg_handler(message.MSG_DB_SAVE_MAILS, db_handler.work_update_mails)
        
        #注册用户数据接受处理
        daemon.register_msg_handler(message.MSG_DB_RECV_USER_DATA, db_handler.recv_user_data)
        
        #注册邮件数据接受处理
        daemon.register_msg_handler(message.MSG_DB_RECV_MAIL_DATA, db_handler.recv_mail_data)
        
        #注册国家数据接收处理
        daemon.register_msg_handler(message.MSG_DB_RECV_COUNTRY_DATA, db_handler.recv_country_data)
        
        #注册拍卖系统数据接收处理
        daemon.register_msg_handler(message.MSG_DB_ADD_AUCTION_DATA, db_handler.recv_auction_add_items)
        daemon.register_msg_handler(message.MSG_DB_DEl_AUCTION_DATA, db_handler.recv_auction_del_items)
        
        #注册交易系统数据接受处理
        daemon.register_msg_handler(message.MSG_DB_UPDATE_TRADE_DATA, db_handler.recv_trade_update_items)
        daemon.register_msg_handler(message.MSG_DB_DEL_TRADE_DATA, db_handler.recv_trade_del_items)
        
        #注册交易新手礼包接受处理
        daemon.register_msg_handler(message.MSG_DB_RECV_NEWBIE_GIFT_DATA, db_handler.recv_newbie_data)
        
        #注册充值数据接受处理
        daemon.register_msg_handler(message.MSG_DB_NEW_ORDER, db_handler.recv_new_order)
        daemon.register_msg_handler(message.MSG_DB_SETTLE_ORDER, db_handler.recv_settle_order)

        #联盟数据
        daemon.register_msg_handler(message.MSG_DB_UNION_UPDATE, db_handler.recv_union_update)
        daemon.register_msg_handler(message.MSG_DB_UNION_DELETE, db_handler.recv_union_delete)
        daemon.register_msg_handler(message.MSG_DB_UNION_USERINFO_UPDATE, db_handler.recv_union_userinfo_update)
        
        
        #活跃时间统计
        daemon.register_msg_handler(message.MSG_DB_LOGIN_TIME_UPDATE, db_handler.recv_login_time_update)
        
        def would_close_handler(hid, content):
                #向主游戏进程发送即将关闭确认的信息
                net_trans.direct_send_data(hid, json.dumps({"msg_id":message.MSG_DB_WOULD_CLOSE,"content":{}, "from":net_cfg.RECV_FROM_DATABASE}))
                
                daemon.signal_handle(10, None)
                
        daemon.register_msg_handler(message.MSG_DB_WOULD_CLOSE, would_close_handler)

def stop():
        #注销账户系统相关处理
        daemon.unregister_msg_handler(message.MSG_DB_UPDATE_USER_GLOBAL)
        daemon.unregister_msg_handler(message.MSG_DB_UPDATE_USER_SUMMARY)
        
        #注销用户系统相关处理
        daemon.unregister_msg_handler(message.MSG_DB_INSERT_USER_CHARACTER)
        daemon.unregister_msg_handler(message.MSG_DB_UPDATE_CHARACTER_ATT)
        
        #注销宠物系统相关处理
        daemon.unregister_msg_handler(message.MSG_DB_DELETE_PET)
        
        #注销任务系统相关处理
        daemon.unregister_msg_handler(message.MSG_DB_DELETE_QUEST)
        
        #注销竞技场系统相关处理
        daemon.unregister_msg_handler(message.MSG_DB_UPDATE_ARENA)
        daemon.unregister_msg_handler(message.MSG_DB_INSERT_ARENA)
        daemon.unregister_msg_handler(message.MSG_DB_REMOVE_FROM_ARENA)
        
        #注销装备系统相关处理
        daemon.unregister_msg_handler(message.MSG_DB_UPDATE_EQUIPS)
        daemon.unregister_msg_handler(message.MSG_DB_DEL_EQUIPS)
        
        #注销邮件系统相关处理
        daemon.unregister_msg_handler(message.MSG_DB_SAVE_MAILS)
        
        #注销用户数据接受处理
        daemon.unregister_msg_handler(message.MSG_DB_RECV_USER_DATA)
        
        #注销邮件数据接受处理
        daemon.unregister_msg_handler(message.MSG_DB_RECV_MAIL_DATA)
        
        #注销国家数据接受处理
        daemon.unregister_msg_handler(message.MSG_DB_RECV_COUNTRY_DATA)
        
        #注销充值数据接受处理
        daemon.unregister_msg_handler(message.MSG_DB_NEW_ORDER)
        daemon.unregister_msg_handler(message.MSG_DB_SETTLE_ORDER)
               
####主程序入口函数
def run():
        #应用程序初始化
        daemon.hook_signal()
        daemon.init()
        
        try:
                init()
        except Exception, e:
                daemon.dlog("init error")
                daemon.dlog("%s", traceback.format_exc())
        
        ######################################################################
        try:
                daemon.main_loop()
        except Exception, e:
                daemon.dlog("game loop error")
                daemon.dlog("%s", traceback.format_exc())
        
        stop()
        
        #应用程序退出
        daemon.stop()