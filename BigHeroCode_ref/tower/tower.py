# -*- coding: utf8 -*-

import copy
import engine.util.my_json as json

import engine.net.trans as net_trans
import engine.daemon as daemon
import engine.net.cookie as cookie
import engine.db.instance as db_ins
import engine.util.simple_timer as timer
import engine.util.common as common

import game_define.message as message
import game_define.error_code as err_code
import game_define.log_info as log_info
import user.instance as user_ins

import battle.config   as battle_cfg
import battle.instance as battle_ins

import drop

import item.config as item_cfg

import state.my_state  as state
import state.config as state_cfg

import quest.config as quest_cfg

import config

import instance
from game_define import event

import item as item_md
import buff.config as buff_cfg

saved_battles = {}

#进入状态
ENTER_STATE_OUTSIDE = 1 #未进入
ENTER_STATE_INSIDE = 2 #已进入

tower_count = 0

class CTower(object):
        def __init__(self, owner):
                global tower_count
                
                tower_count += 1
                
                self._c_owner = owner
                
                self._n_process = -1 #爬塔进度，-1代表没进入，第一次进入的时候会在enter()里面置为0，表示将要打第一层
                
                self._list_active_chapters = [1] #激活的章节
                
                self._n_enter_time = 0 #进入次数
                
                self._b_in_auto_tower = False
                
                self._n_auto_timer = -1
                
                self._n_des_process = -1
                
                self._dict_auto_battle_result = {}
                
                self._max_floor = 0
                
                self._use_dummy_npc = False
                
                self._auto_settle_callback = None
        
                self._auto_settle_reward = None
                
                self._auto_settle_des_process = None
                
                self._enter_state = ENTER_STATE_OUTSIDE
        
        def __del__(self):
                global tower_count
                
                if tower_count:
                        tower_count -= 1
                
        def __my_del__(self):
                if self._n_auto_timer != -1:
                        timer.kill_timer(self._n_auto_timer)
                              
                self._c_owner = None
                
                self._auto_settle_callback = None
        
                self._auto_settle_reward = None
                
                self._auto_settle_des_process = None
        
        def export_data(self, clear = False):
                data = {}
                
                data["process"] = self._n_process
                
                data["active_chapters"] = copy.deepcopy(self._list_active_chapters)
                
                data["enter_time"] = copy.deepcopy(self._n_enter_time)
                
                data["in_auto_tower"] = self._b_in_auto_tower
                
                data["des_process"] = self._n_des_process
                
                data["auto_battle_result"] = copy.deepcopy(self._dict_auto_battle_result)
                
                data["max_floor"] = self._max_floor
                
                return data
        
        def import_data(self, data):
                self._n_process = data["process"]
                if self._n_process >= 0:
                        self._enter_state = ENTER_STATE_INSIDE
                
                del data["process"]
                
                self._list_active_chapters = data["active_chapters"]
                
                del data["active_chapters"]
                
                self._n_enter_time = data["enter_time"]
                
                del data["enter_time"]
                
                self._b_in_auto_tower = data["in_auto_tower"]
                
                del data["in_auto_tower"]
                
                self._n_des_process = data["des_process"]
                
                del data["des_process"]
                
                self._dict_auto_battle_result = data["auto_battle_result"]
                
                del data["auto_battle_result"]
                
                self._max_floor = data["max_floor"]
                
                del data["max_floor"]
                
        #初始化
        def init(self):
                if not self._c_owner.if_from_db():
                        return
                
                result = db_ins.gm_db.do_query("select * from tower where uid = %(uid)s", {"uid" : self._c_owner._uid})
                
                if not len(result):
                        return
                        
                uid, process, active_chapters, auto_tower_info, max_floor = result[0]
                
                self._n_process = process
                if self._n_process >= 0:
                        self._enter_state = ENTER_STATE_INSIDE
                
                self._list_active_chapters = json.loads(active_chapters)
                
                self._max_floor = max_floor
                
                try:
                        self._list_active_chapters.index(1)
                except:
                        self._list_active_chapters.append(1)
                        
                if len(auto_tower_info):
                        auto_tower_info = json.loads(auto_tower_info)
                else:
                        auto_tower_info = {"in_auto_tower":0, "des_process":-1}
                                
                self._b_in_auto_tower = bool(auto_tower_info["in_auto_tower"])
                
                self._n_des_process = auto_tower_info["des_process"]
                
        #更新数据
        def do_update(self):
                return {"tower":{"uid":self._c_owner._uid, "process":self._n_process, 
                                 "active_chapters":json.dumps(self._list_active_chapters),
                                 "auto_tower_info":json.dumps({"in_auto_tower":int(self._b_in_auto_tower),
                                                               "des_process":self._n_des_process}),
                                 "max_floor":self._max_floor
                                }
                        }
                
        #获取NPC
        def get_npc(self):
                resp = {}
                
                npcs = eval(instance.tower_cfg[self._n_process]["npc"])
                
                difficulty_quot = instance.tower_cfg[self._n_process].get("difficulty_quot", -1)
                
                if self._use_dummy_npc:
                        difficulty_quot = 0.01
                
                result = []
                
                for npc in npcs:
                        result.append({"id":npc, \
                                       "type":battle_cfg.FIGHTER_TYPE_NPC, \
                                       "side":battle_cfg.DEFEND_SIDE, \
                                       "difficulty_quot":difficulty_quot})
                
                return result
                
        def get_process(self):
                return self._n_process
                
        #获取最大爬塔数
        def get_max_floor(self):
                return self._max_floor + 1
                
        #开始爬塔战斗
        def start_battle(self):
                if self._c_owner.get_lv() < config.MIN_ENTER_LEVEL:
                        return {"err_code":err_code.ERR_TOWER_ENTER_LEVEL_NOT_ENOUGH}
                
                if self._enter_state != ENTER_STATE_INSIDE: raise Exception
                
                return battle_ins.get_manager().launch_battle_in_tower(self._c_owner._uid, \
                                                                 self.get_npc(), 
                                                                 instance.tower_cfg[self._n_process]["name"])
        
        #生成战斗奖励
        def generate_award(self):
                """战斗结束后掉落物品"""
                droplist_ids = eval(instance.tower_cfg[self._n_process]["drop"])
                
                items = None
                
                if self._c_owner._quest_mgr.check_quest_active(config.TOWER_TECH_QUEST_ID[self._c_owner.get_country()]):
                        items = drop.drop_items(self._c_owner, droplist_ids, 
                                                True, self._n_enter_time, 
                                                (tuple(droplist_ids), 
                                                 config.TOWER_TECH_ITEM_DROP_IDS[0], 
                                                 config.TOWER_TECH_ITEM_DROP_IDS[1]),
                                                log_src = log_info.LOG_ITEM_NEW_TOWER
                                                )
                else:
                        items = drop.drop_items(self._c_owner, droplist_ids, True, self._n_enter_time,
                                                log_src = log_info.LOG_ITEM_NEW_TOWER)        
                
                return items
                
        def _trigger_event_get_item(self, result):
                evt = [event.EVENT_GET_ITEM_IN_TOWER, {event.EP_PLAYER_NAME:self._c_owner.name(),
                                                       event.EP_PLAYER_QUALITY:self._c_owner.get_potentia_quality(),
                                                       event.EP_TOWER_FLOOR:self._n_process}]
                
                for item in result:
                        if item["type"] == item_cfg.EQUIP:
                                item_id = item["equip_id"]
                                item_num = 1
                                quality = item["attr"]["quality"]
                        else:
                                item_id = item["id"]
                                item_num = item["num"]
                                quality = item_md.get_item_attri(item_id, "quality", 0)
                        evt[1][event.EP_QUALITY] = quality
                        evt[1][event.EP_ITEMID] = item_id
                        evt[1][event.EP_COUNT] = item_num
                
                self._c_owner.trigger_event(evt)
                
        #打通章节
        def _trigger_event_floor_clearance(self):
                evt = [event.EVENT_TOWER_FLOOR_CLEARANCE, {event.EP_PLAYER_NAME:self._c_owner.name(),
                                                       event.EP_PLAYER_QUALITY:self._c_owner.get_potentia_quality(),
                                                       event.EP_TOWER_FLOOR:self._n_process}]
                
                
                evt[1][event.EP_COUNT] = 0
                self._c_owner.trigger_event(evt)
        
        #首次打通月光之城
        def _trigger_event_floor_clearance_all(self):
                evt = [event.EVENT_TOWER_FLOOR_CLEARANCE_ALL, 
                       {event.EP_PLAYER_NAME:self._c_owner.name(),
                        event.EP_PLAYER_QUALITY:self._c_owner.get_potentia_quality()
                        }]
                
                self._c_owner.trigger_event(evt)
                
                
                text = u'英雄【%s】威名显赫，首次通过"月光之城"最终关考验，受到诸神认可，获得潜力保护书×1和圣界光芒胸甲×1作为奖励。'
                text = text % self._c_owner.name()
                title = u'首次通关月光之城最终章奖励'
                
                from mail.mail_mgr import g_mail_mgr
                from equip.equip_manager import equip_mgr
                import equip.config as equip_cfg
                from equip.equipment import CEquip
                
                equip_obj = CEquip(12192, self._c_owner._uid, quality = equip_cfg.QUALITY_ORANGE)
                equip_mgr.add_equip(equip_obj)
                equip_obj.do_update(im=True)
                
                items = [{"type" : item_cfg.PET_BOOK,"id" : 17502, "num" : 1, "is_bound": True},
                         {"type" : item_cfg.EQUIP,"id" : equip_obj._hash_id, "num" : 1, "is_bound": True},
                         ]
                g_mail_mgr._send_sys_mail2(-1, self._c_owner.name(), title, text, items = items)
                
        
        #完成进度
        def finish_process(self, battle_detail):
                global saved_battles
                
                """战斗调用接口 - 战斗结束后调用"""
                result = self.generate_award()
                
                #改变任务状态
                self._c_owner._quest_mgr.add_quest_count_after_action(quest_cfg.QUEST_ACTION_FINISH_TOWER)
                        
                #推倒Boss
                if (not (self._n_process + 1)% 10) and (self._n_process != -1):
                        
                        first_kill_uids = []
                        
                        for i in xrange(3):
                                save_key = "tower_" + str(self._n_process) + "_" + str(i)
                                
                                if not saved_battles.has_key(save_key):
                                        #前三名击杀
                                        launcher_id = self._c_owner.uid()
                                        im = battle_detail["im"] #是否为自动战斗
                                        
                                        #如果未位于前三名之列，保存其记录
                                        #自动战斗不保存战报
                                        if launcher_id not in first_kill_uids and not im:
                                                battle_id = battle_detail["ins"].get_id()
                                                
                                                battle_name = battle_detail["name"]
                                                
                                                battle_pack = battle_detail["msg"]["launcher"]["struct"]["pack"]
                                                
                                                saved_battles[save_key] = {"launcher_id":launcher_id, "battle_id":battle_id, "battle_name":battle_name}
                                                
                                                #将战斗相关信息写进文件数据库
                                                #保存映射
                                                db_ins.gm_fdbm.write(save_key, common.my_encode(saved_battles[save_key]))
                                                
                                                #保存战斗信息
                                                db_ins.gm_fdbm.write(str(battle_id), common.my_encode(battle_pack))
                                                
                                                db_ins.sync_fdbm()
                                        
                                        break
                                else:
                                        first_kill_uids.append(saved_battles[save_key]["launcher_id"])
                
                if self._n_process != config.MAX_FLOOR_NUM - 1:
                        if config.FLOOR_CHAPTER_MAP.has_key(self._n_process):
                                chapter_id = config.FLOOR_CHAPTER_MAP[self._n_process]
                                
                                #第一次打通本章
                                if chapter_id not in self._list_active_chapters:
                                        self._list_active_chapters.append(config.FLOOR_CHAPTER_MAP[self._n_process])
                                        self._trigger_event_floor_clearance()
                        
                        if self._n_process > self._max_floor:
                                self._max_floor = self._n_process
                                
                        #进军下一层
                        self._n_process += 1
                        
                        if self._n_process == 5:
                                self._c_owner._quest_mgr.add_quest_count_after_action(quest_cfg.QUEST_ACTION_FINISH_TOWER_5)
                        elif self._n_process == 10:
                                self._c_owner._quest_mgr.add_quest_count_after_action(quest_cfg.QUEST_ACTION_FINISH_TOWER_10)
                        elif self._n_process == 20:
                                self._c_owner._quest_mgr.add_quest_count_after_action(quest_cfg.QUEST_ACTION_FINISH_TOWER_20)
                        elif self._n_process == 35:
                                self._c_owner._quest_mgr.add_quest_count_after_action(quest_cfg.QUEST_ACTION_FINISH_TOWER_35)
                        elif self._n_process == 50:
                                self._c_owner._quest_mgr.add_quest_count_after_action(quest_cfg.QUEST_ACTION_FINISH_TOWER_50)
                        elif self._n_process == 100:
                                self._c_owner._quest_mgr.add_quest_count_after_action(quest_cfg.QUEST_ACTION_FINISH_TOWER_100)
                        elif self._n_process == 200:
                                self._c_owner._quest_mgr.add_quest_count_after_action(quest_cfg.QUEST_ACTION_FINISH_TOWER_200)
                        elif self._n_process == 300:
                                self._c_owner._quest_mgr.add_quest_count_after_action(quest_cfg.QUEST_ACTION_FINISH_TOWER_300)
                        else:
                                pass
                else:
                        if self._n_process > self._max_floor:
                                self._max_floor = self._n_process
                                self._trigger_event_floor_clearance_all()
                                
                        #通关，重新回到入口
                        self._n_process = -1
                        self._enter_state = ENTER_STATE_OUTSIDE
                        
                        self._c_owner._quest_mgr.add_quest_count_after_action(quest_cfg.QUEST_ACTION_FINISH_TOP_TOWER)
                        self._c_owner._quest_mgr.add_quest_count_after_action(quest_cfg.QUEST_ACTION_FINISH_TOWER_300)
                        
                #获得物品，公告
                if len(result):
                        self._trigger_event_get_item(result)
                        
                #向客户端同步高塔信息
                net_trans.send_data(self._c_owner._hid, message.MSG_NET_GET_TOWER_INFO,
                                    self.get_info())
                        
                return result
        
        #设置当前层数, 测试用
        def _set_floor(self, num):
                if not(num >= 1 and num <= 299):
                        raise Exception("num out of range", num)
                
                self._n_process = num
                self._enter_state = ENTER_STATE_INSIDE
                
                if self._n_process > self._max_floor:
                        self._max_floor = self._n_process
                
                self._list_active_chapters = [1]
                keys = config.FLOOR_CHAPTER_MAP.keys()
                keys.sort()
                for k in keys:
                        val = config.FLOOR_CHAPTER_MAP[k]
                        if num-1 > k:
                                self._list_active_chapters.append(val)
                        else:
                                break

        #重置塔，回到塔的入口
        def reset(self):
                self._n_process = -1
                self._enter_state = ENTER_STATE_OUTSIDE
                
                #向客户端同步高塔信息
                net_trans.send_data(self._c_owner._hid, message.MSG_NET_GET_TOWER_INFO,
                                    self.get_info())
        
        #获取信息
        def get_info(self):
                global saved_battles
                
                info = {"process":self._n_process, "active_chapters":self._list_active_chapters, "enter_time":self._n_enter_time}
                
                if self._n_process != -1 and (not (self._n_process + 1) % 10):
                        info["first_kill_info"] = []
                        
                        #Boss层，需获取首杀前3名信息
                        for i in xrange(3):
                                save_key = "tower_" + str(self._n_process) + "_" + str(i)
                                
                                if not saved_battles.has_key(save_key):
                                        break
                                
                                #修正以前错误的数据，有些战斗名为空字符串
                                if not saved_battles[save_key]["battle_name"]:
                                        uid = saved_battles[save_key]["launcher_id"]
                                        cobj = user_ins.get_character_mgr().get_character(uid)
                                        if cobj:
                                                floor_name = instance.tower_cfg[self._n_process]["name"]
                                                battle_name = "[" + cobj.get_name() + "][" + floor_name + "]"
                                                saved_battles[save_key]["battle_name"] = battle_name
                                
                                info["first_kill_info"].append(saved_battles[save_key])
                                
                return info
        
                
        #重置进入次数
        def reset_enter_time(self):
                self._n_enter_time = 0
        
        #获取进入次数
        def get_enter_time(self):
                return self._n_enter_time
                
        #进入章节
        def enter(self, chapter_id):
                resp = {"err_code":err_code.ERR_OK}
                
                last_chapter_id = max(0, chapter_id - 1)
                
                if last_chapter_id and (last_chapter_id not in self._list_active_chapters):
                        resp["err_code"] = err_code.ERR_TOWER_CHAPTER_NOT_ACTIVE
                        
                        return resp
                
                #进度更新为入口进度
                self._n_process = config.CHAPTER_FLOOR_MAP[chapter_id]
                
                #累积进入次数
                self._n_enter_time += 1
                
                self._enter_state = ENTER_STATE_INSIDE
                
                resp["detail"] = chapter_id
                
                #进入成功
                return resp
        
        def battle_end(self, is_win, reward):
                if is_win:
                        #已结束
                        if not self._n_process:
                                curr_process = config.MAX_FLOOR_NUM - 1
                                
                                self._n_auto_timer = -1
                                
                                self._b_in_auto_tower = False
                                
                                self._n_des_process = -1
                        else:
                                #月光之城通关
                                if self._n_des_process == config.MAX_FLOOR_NUM - 1 and self._n_process == -1:
                                        curr_process = config.MAX_FLOOR_NUM - 1
                                else:
                                        curr_process = self._n_process - 1
                                
                        self._dict_auto_battle_result[curr_process] = {"win":is_win, "result":reward}                        
                        
                        if curr_process < self._n_des_process:
                                self._n_auto_timer = timer.set_timer(config.AUTO_TOWER_TIME, \
                                                                     repeat_count=1, \
                                                                     callback=self.auto_battle)
                        else:
                                self._n_auto_timer = -1
                                
                                self._b_in_auto_tower = False
                                
                                self._n_des_process = -1
                else:
                        curr_process = self._n_process
                        
                        # 战斗失败,结束自动战斗
                        self._dict_auto_battle_result[curr_process] = {"win":is_win, "result":reward}
                                      
                        self._n_auto_timer = -1
                        
                        self._b_in_auto_tower = False
                        
                        self._n_des_process = -1
                        
                net_trans.send_data(self._c_owner._hid, message.MSG_NET_AUTO_TOWER_SETTLE, \
                                    self._dict_auto_battle_result)
                                    
                self._dict_auto_battle_result.clear()
                
        def auto_battle(self):
                if self._n_auto_timer == -1:
                        self._b_in_auto_tower = True
                        
                        self._n_auto_timer = timer.set_timer(config.AUTO_TOWER_TIME, \
                                                             repeat_count=1, \
                                                             callback=self.auto_battle)
                else:   
                        #扣钱
                        self._c_owner.change_money(-config.GOLD_PER_FLOOR, item_cfg.MONEY_YUANBAO, log_info.LOG_MONEY_CHG_AUTO_TOWER)
                        
                        curr_process = self._n_process   
                        
                        #需动态检测格子数
                        check_resp = self._c_owner._bag.check_grid_enough(config.FREE_BAG_GRID_NUM)
                
                        if check_resp["err_code"] != err_code.ERR_OK:
                                #背包剩余格子数不够, 结束自动战斗
                                self._dict_auto_battle_result[curr_process] = {"win":False,
                                                                               "result":{},
                                                                               "bag_grid":[self._c_owner._bag.get_free_grid_num(), check_resp["detail"]]}
                                
                                self._n_auto_timer = -1
                                self._b_in_auto_tower = False
                                net_trans.send_data(self._c_owner._hid, message.MSG_NET_AUTO_TOWER_SETTLE,\
                                                    self._dict_auto_battle_result)
                                
                                self._dict_auto_battle_result.clear()
                                
                                return
                        
                        battle_ins.get_manager().auto_launch_battle_in_tower(self._c_owner._uid,\
                                                                             self.get_npc(),\
                                                                             instance.tower_cfg[self._n_process]["name"],\
                                                                             self.battle_end)

                return {"process":self._n_process}
        
        def auto_battle_end(self):
                if self._n_auto_timer == -1:
                        return
                
                timer.kill_timer(self._n_auto_timer)
                
                self._n_auto_timer = -1
                
                self._b_in_auto_tower = False
                
                self._n_des_process = -1
                
        def kill_auto_timer(self):
                if self._n_auto_timer == -1:
                        return
                        
                timer.kill_timer(self._n_auto_timer)
                
                self._n_auto_timer = -1
        
        def fight(self):
                self._c_owner.change_money(-config.GOLD_PER_FLOOR, item_cfg.MONEY_YUANBAO, log_info.LOG_MONEY_CHG_AUTO_TOWER)
                
                # 战斗,不需要发送战斗消息,返回战斗结果
                battle_ins.get_manager().auto_launch_battle_in_tower(self._c_owner._uid,\
                                                                     self.get_npc(),\
                                                                     instance.tower_cfg[self._n_process]["name"],\
                                                                     self.settle_battle_end)
                                                                     
        def settle_battle_end(self, is_win, reward):
                curr_process = self._n_process
                
                if reward.has_key("exp"):
                        self._auto_settle_reward["exp"] += reward["exp"]
                        
                for item in reward["item"]:
                        if item["type"] == item_cfg.EQUIP:
                                self._auto_settle_reward["item"].append(item)
                        else:
                                exist = False
                                
                                for titem in self._auto_settle_reward["item"]:
                                        if titem["type"] == item["type"] and \
                                           titem["id"]   == item["id"]:
                                                titem["num"] += item["num"]
                                                
                                                exist = True
                                                
                                                break
                                                
                                if not exist:
                                        self._auto_settle_reward["item"].append(item)
                                        
                has_money = self._c_owner.get_money_by_type(item_cfg.MONEY_YUANBAO) >= config.GOLD_PER_FLOOR
                
                if (not is_win) or (not curr_process) or \
                   curr_process == self._n_des_process + 1 or \
                   curr_process == self._auto_settle_des_process + 1 or not has_money:
                        #挂机停止
                        if (not is_win) or (not curr_process) or \
                           curr_process == self._n_des_process + 1\
                           or not has_money:
                                self._b_in_auto_tower = False

                        if self._auto_settle_callback:
                                self._auto_settle_callback({"is_win":is_win, 
                                                            "process":curr_process, 
                                                            "reward":self._auto_settle_reward})
                        
                        self._auto_settle_callback = None
        
                        self._auto_settle_reward = None
                        
                        self._auto_settle_des_process = None
                        
                        return
                
                self.fight()
                
        #登陆
        def auto_settle(self, callback = None):
                if not self._b_in_auto_tower:
                        if callback:
                                callback(None)
                                
                        return
                
                curr_process = self._n_process
                
                if not curr_process:
                        if callback:
                                callback(None)
                                
                        return
                
                logout_timestamp = self._c_owner.get_logout_timestamp()
                
                if not logout_timestamp:
                        if callback:
                                callback(None)
                                
                        return
                
                curr_timestamp = int(common.now())
                
                pass_time = curr_timestamp - logout_timestamp
                
                des_process = curr_process + pass_time * 1000 / config.AUTO_TOWER_TIME
                
                if des_process == curr_process:
                        if callback:
                                callback(None)
                                
                        return
                  
                total_reward = {"exp":0, "item":[]}
                                               
                if self._c_owner.get_money_by_type(item_cfg.MONEY_YUANBAO) >= config.GOLD_PER_FLOOR:
                        self._auto_settle_callback = callback
        
                        self._auto_settle_reward = total_reward
                        
                        self._auto_settle_des_process = des_process
                
                        self.fight()
                elif callback:
                        callback(None)
        
        def login(self):
                pass
                
        def logout(self):
                self.kill_auto_timer()
                
        #自动爬塔
        def auto_tower(self, des_process, money_type):
                resp = {"err_code":err_code.ERR_OK}
                
                change_money = True
                
                if self._enter_state != ENTER_STATE_INSIDE: raise Exception
                
                if self._c_owner.get_lv() < config.MIN_ENTER_LEVEL:
                        return {"err_code":err_code.ERR_TOWER_ENTER_LEVEL_NOT_ENOUGH}
                
                if self._b_in_auto_tower:
                        if self._n_auto_timer != -1:
                                resp["err_code"] = err_code.ERR_IN_AUTO_TOWER
                                return resp
                        
                        change_money = False
                
                if des_process <= self._n_process or des_process > config.MAX_FLOOR_NUM:
                        resp["err_code"] = err_code.ERR_NO_NEED_TO_AUTO_TOWER
                        return resp
                        
                self._n_des_process = des_process
                
                floor_num = des_process - self._n_process
                
                cost = 0
                
                if change_money:
                        cost = floor_num * config.GOLD_PER_FLOOR
                        
                        if not self._c_owner.has_money(cost, money_type):
                                resp["err_code"] = err_code.ERR_NO_ENOUGH_MONEY
                                resp["detail"] = money_type
                                return resp
                                
                check_resp = self._c_owner._bag.check_grid_enough(config.FREE_BAG_GRID_NUM)
        
                if check_resp["err_code"] != err_code.ERR_OK:
                        return check_resp
                
                if not buff_cfg.vip_extra[buff_cfg.VIP_AUTO_TOWER][self._c_owner.get_vip_lv()]:
                        resp["err_code"] = err_code.ERR_VIP_ONLY
                        return resp
                        
                #开始自动战斗
                resp["detail"] = self.auto_battle()
                
                return resp
        
        def auto_tower_end(self):
                self.auto_battle_end()
                
                return {"err_code":err_code.ERR_OK}
                        
        def get_auto_tower_info(self):
                if self._enter_state != ENTER_STATE_INSIDE:
                        self._b_in_auto_tower = False
                        
                        self._n_process = -1
                        
                        self._n_des_process = -1
                        
                return {"in_auto_tower":self._b_in_auto_tower,
                        "tower_process":self._n_process, 
                        "tower_des_process":self._n_des_process}
                                
        def in_auto_tower(self):
                return self._b_in_auto_tower
                        
#获取高塔信息
def get_tower_info(hid, content):
        resp = {"close" : False, "content" : None}
                
        pid = cookie.get_cookie(hid, "pid")
        cobj = user_ins.get_character_mgr().get_character(pid)
        
        resp["content"] = cobj._tower.get_info()
        
        return resp

#进入高塔
def enter_tower(hid, content):
        resp = {"close" : False, "content" : None}
                
        pid = cookie.get_cookie(hid, "pid")
        cobj = user_ins.get_character_mgr().get_character(pid)
        
        resp["content"] = cobj._tower.enter(content["chapter_id"])
        
        return resp
        
#开始高塔战斗        
def start_tower_battle(hid, content):
        resp = {"close" : False, "content" : None}
                
        pid = cookie.get_cookie(hid, "pid")
        cobj = user_ins.get_character_mgr().get_character(pid)
        
        resp["content"] = cobj._tower.start_battle()
        
        return resp
        
#重置高塔
def reset_tower(hid, content):
        resp = {"close" : False, "content" : None}
                
        pid = cookie.get_cookie(hid, "pid")
        cobj = user_ins.get_character_mgr().get_character(pid)
        
        cobj._tower.reset()
        
        return resp

#自动爬塔
def auto_tower(hid, content):
        resp = {"close" : False, "content" : None}
                
        pid = cookie.get_cookie(hid, "pid")
        cobj = user_ins.get_character_mgr().get_character(pid)
        
        resp["content"] = cobj._tower.auto_tower(content["des_process"], content["money_type"])
        
        return resp

#终止自动爬塔
def auto_tower_end(hid, content):
        resp = {"close" : False, "content" : None}
                
        pid = cookie.get_cookie(hid, "pid")
        cobj = user_ins.get_character_mgr().get_character(pid)
        
        resp["content"] = cobj._tower.auto_tower_end()
        
        return resp
          
#初始化
def init():
        global saved_battles
        
        daemon.register_msg_handler(message.MSG_NET_GET_TOWER_INFO,     get_tower_info)
        daemon.register_msg_handler(message.MSG_NET_ENTER_TOWER,        enter_tower)
        daemon.register_msg_handler(message.MSG_NET_START_TOWER_BATTLE, start_tower_battle)
        daemon.register_msg_handler(message.MSG_NET_RESET_TOWER,        reset_tower)
        daemon.register_msg_handler(message.MSG_NET_AUTO_TOWER,         auto_tower)
        daemon.register_msg_handler(message.MSG_NET_AUTO_TOWER_END,     auto_tower_end)
        
        state.register_opt(message.MSG_NET_START_TOWER_BATTLE, [state_cfg.OPT_JOIN_BATTLE,])
        
        state.register_opt(message.MSG_NET_ENTER_TOWER, [state_cfg.OPT_MANUAL_TOWER,])
        state.register_opt(message.MSG_NET_RESET_TOWER, [state_cfg.OPT_MANUAL_TOWER,])
        
        state.register_opt(message.MSG_NET_AUTO_TOWER, [state_cfg.OPT_AUTO_TOWER,])
        
        #导出各层首杀信息
        for process in xrange(config.MAX_FLOOR_NUM):
                if not (process + 1) % 10:
                        for i in xrange(3):
                                save_key = "tower_" + str(process) + "_" + str(i)
                                
                                if not db_ins.gm_fdbm.has_key(save_key):
                                        break
                                
                                try:
                                        saved_battles[save_key] = common.my_decode(db_ins.gm_fdbm.read(save_key))
                                except:
                                        pass
                                        
#停止
def stop():
        daemon.unregister_msg_handler(message.MSG_NET_GET_TOWER_INFO)
        daemon.unregister_msg_handler(message.MSG_NET_ENTER_TOWER)
        daemon.unregister_msg_handler(message.MSG_NET_START_TOWER_BATTLE)
        daemon.unregister_msg_handler(message.MSG_NET_RESET_TOWER)
        daemon.unregister_msg_handler(message.MSG_NET_AUTO_TOWER)
        daemon.unregister_msg_handler(message.MSG_NET_AUTO_TOWER_END)
        
        state.unregister_opt(message.MSG_NET_START_TOWER_BATTLE)
        
        state.unregister_opt(message.MSG_NET_ENTER_TOWER)
        state.unregister_opt(message.MSG_NET_RESET_TOWER)
        
        state.unregister_opt(message.MSG_NET_AUTO_TOWER)