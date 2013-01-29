# -*- coding: utf8 -*-

import MySQLdb

import engine.util.my_json as json

import engine.db.instance as db_ins

g_dict_user_data = {}

#接受用户数据，待所有用户数据完整以后，再调用数据库进行更新
def recv_user_data(hid, content):
        global g_dict_user_data
        
        uid = content["uid"]
        
        if not g_dict_user_data.has_key(uid):
                g_dict_user_data[uid] = ""
                
        data_len = content["data_len"]
        
        data = content["data"]
        
        #追加数据
        g_dict_user_data[uid] += data
        
        if len(g_dict_user_data[uid]) < data_len:
                return
        
        #数据已接受完毕
        full_data = g_dict_user_data[uid]
        
        g_dict_user_data[uid] = ""
        
        db_contents = json.loads(full_data)
        
        if db_contents.has_key("character_att"):
                #更新用户属性数据
                work_update_character_att(hid, db_contents["character_att"])
        
        if db_contents.has_key("equips"):
                #更新用户装备信息
                for equip in db_contents["equips"]:
                        work_update_user_equips(hid, equip)
        
        if db_contents.has_key("bag"):
                #更新背包属性数据
                work_update_bag(hid, db_contents["bag"])
        
        if db_contents.has_key("depot"):
                #更新仓库属性数据
                work_update_depot(hid, db_contents["depot"])
                
        if db_contents.has_key("dragon"):
                #更新屠龙属性数据
                work_update_dragon(hid, db_contents["dragon"])
        
        if db_contents.has_key("dungeons"):
                #更新副本数据
                for dungeon in db_contents["dungeons"]:
                        work_update_dungeon(hid, dungeon)
        
        if db_contents.has_key("pets"):
                #更新宠物数据
                for pet in db_contents["pets"]:
                        work_update_pet(hid, pet)
        
        if db_contents.has_key("quests"):      
                #更新任务数据
                for quest in db_contents["quests"]:
                        work_query_update_quest(hid, quest)
                        
        if db_contents.has_key("quest_done"):
                #更新任务完成数据
                work_query_update_quest_done(hid, db_contents["quest_done"])
        
        if db_contents.has_key("target"):
                #更新目标数据
                work_query_update_target(hid, db_contents["target"])
                
        if db_contents.has_key("user_skills"):
                #更新技能数据
                work_update_user_skills(hid, db_contents["user_skills"])
        
        if db_contents.has_key("task"):
                #更新佣兵任务数据
                work_query_update_task(hid, db_contents["task"])
        
        if db_contents.has_key("friends"):
                #更新好友数据
                work_query_update_friends(hid, db_contents["friends"])
                
        if db_contents.has_key("tower"):
                #更新高塔数据
                work_update_tower(hid, db_contents["tower"])
        
        if db_contents.has_key("guarder"):
                #更新守护数据
                work_update_guarder(hid, db_contents["guarder"])
                
        if db_contents.has_key("army"):
                #更新佣兵团数据
                work_update_army(hid, db_contents["army"])
        
        if db_contents.has_key("online_stat"):        
                #更新在线数据
                work_update_login_time(hid, db_contents["online_stat"])