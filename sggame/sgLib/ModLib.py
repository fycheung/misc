#-*-coding:utf-8-*-  
#author:Lizr
#date:2012-03-29
#引入游戏所有模型  测试

#重载模块
def modReload():
    #-------------- Cfg -------------
    import sgCfg.config
    import sgLib.defined
    #-------------- Lib -------------
    #sgLib.base 不能重载 否则：TypeError: unbound method __init__() must be called with Base instance as first argument (got BattleMod instance instead)
    import sgLib.common
    import sgLib.lang_message
    import sgLib.coord
    import sgLib.FightOver
    import sgLib.formula
    import sgLib.mqManager
    import sgLib.ModLib
    import sgLib.proManager
    import sgLib.pyCache
    #import sgLib.pyDB  不能重载，因为已保存连接池
    import sgLib.pyMcrypt
    import sgLib.pyPusher
    import sgLib.pyRabbit
    import sgLib.pyRedis
    import sgLib.pySystem
    import sgLib.setting
    #-------------- UI --------------
    import sgMod.TemplateUI
    import sgMod.TestUI
    import sgMod.MapUI
    import sgMod.BuildingUI
    
    import sgMod.Building_altarUI
    import sgMod.Building_pubUI
    import sgMod.Building_resourceUI
    import sgMod.Building_trainUI
    import sgMod.Building_campUI
    import sgMod.Building_groundUI
    import sgMod.Building_clubUI
    import sgMod.Building_holdUI
    
    import sgMod.BookUI
    import sgMod.EquipUI
    import sgMod.WarUI
    import sgMod.WallUI
    import sgMod.MailUI
    import sgMod.ItemUI
    import sgMod.PlayerUI
    import sgMod.FriendUI
    import sgMod.BagUI
    import sgMod.VisitUI
    import sgMod.LoginUI#temp
    import sgMod.MissionUI
    import sgMod.ChatUI
    import sgMod.RedisUI
    import sgMod.ActivityUI
    import sgMod.RankFightUI
    
    #-------------- Mod --------------
    import sgMod.subMod.TestMod
    import sgMod.subMod.TemplateMod
    import sgMod.subMod.BookMod
    import sgMod.subMod.BuildingMod
    import sgMod.subMod.building.Building_pubMod
    import sgMod.subMod.building.Building_resourceMod
    import sgMod.subMod.building.Building_schoolMod
    import sgMod.subMod.building.Building_campMod
    import sgMod.subMod.building.Building_trainMod
    import sgMod.subMod.building.Building_altarMod
    import sgMod.subMod.building.Building_clubMod
    import sgMod.subMod.building.Building_groundMod
    import sgMod.subMod.building.Building_homeMod
    import sgMod.subMod.building.Building_holdMod

    import sgMod.subMod.CoinMod
    import sgMod.subMod.EquipMod
    import sgMod.subMod.GeneralMod
    import sgMod.subMod.MapMod
    import sgMod.subMod.PlayerMod
    #import sgMod.subMod.SoldierMod
    import sgMod.subMod.InterMod
    import sgMod.subMod.WarMod
    import sgMod.subMod.WallMod
    import sgMod.subMod.MailMod
    import sgMod.subMod.ItemMod
    import sgMod.subMod.BagMod
    import sgMod.subMod.FriendMod
    import sgMod.subMod.BattleMod
    import sgMod.subMod.RewardMod
    import sgMod.subMod.InteractMod
    import sgMod.subMod.MissionMod
    import sgMod.subMod.ChatMod
    import sgMod.subMod.RedisMod
    import sgMod.subMod.ActivityMod
    import sgMod.subMod.EventMod
    import sgMod.subMod.LoginMod
    import sgMod.subMod.RankFightMod
    
    #重载
    reload(sgCfg.config)
    reload(sgLib.defined)
    reload(sgLib.proManager)
    
    reload(sgLib.common)
    reload(sgLib.lang_message)
    reload(sgLib.coord)
    reload(sgLib.FightOver)
    reload(sgLib.formula)
    reload(sgLib.mqManager)
    reload(sgLib.ModLib)
    reload(sgLib.pyCache)
    #reload(sgLib.pyDB)
    reload(sgLib.pyMcrypt)
    reload(sgLib.pyPusher)
    reload(sgLib.pyRabbit)
    reload(sgLib.pyRedis)
    reload(sgLib.pySystem)
    reload(sgLib.setting)
    
    reload(sgMod.TemplateUI)
    reload(sgMod.TestUI)
    reload(sgMod.MapUI)
    reload(sgMod.BuildingUI)
    
    reload(sgMod.Building_altarUI)
    reload(sgMod.Building_pubUI)
    reload(sgMod.Building_resourceUI)
    reload(sgMod.Building_trainUI)
    reload(sgMod.Building_campUI)
    reload(sgMod.Building_groundUI)
    reload(sgMod.Building_clubUI)
    reload(sgMod.Building_holdUI)
    reload(sgMod.BookUI)
    reload(sgMod.EquipUI)
    reload(sgMod.WarUI)
    reload(sgMod.WallUI)
    reload(sgMod.MailUI)
    reload(sgMod.ItemUI)
    reload(sgMod.PlayerUI)
    reload(sgMod.FriendUI)
    reload(sgMod.BagUI)
    reload(sgMod.VisitUI)
    reload(sgMod.LoginUI)#temp
    reload(sgMod.MissionUI)
    reload(sgMod.ChatUI)
    reload(sgMod.RedisUI)
    reload(sgMod.ActivityUI)
    reload(sgMod.RankFightUI)
    
    reload(sgMod.subMod.TestMod)
    reload(sgMod.subMod.TemplateMod)
    reload(sgMod.subMod.BookMod)
    reload(sgMod.subMod.BuildingMod)
    reload(sgMod.subMod.building.Building_pubMod)
    reload(sgMod.subMod.building.Building_resourceMod)
    reload(sgMod.subMod.building.Building_schoolMod)
    reload(sgMod.subMod.building.Building_campMod)
    reload(sgMod.subMod.building.Building_trainMod)
    reload(sgMod.subMod.building.Building_altarMod)
    reload(sgMod.subMod.building.Building_clubMod)
    reload(sgMod.subMod.building.Building_groundMod)
    reload(sgMod.subMod.building.Building_homeMod)
    reload(sgMod.subMod.building.Building_holdMod)
    
    reload(sgMod.subMod.CoinMod)
    reload(sgMod.subMod.EquipMod)
    reload(sgMod.subMod.GeneralMod)
    reload(sgMod.subMod.MapMod)
    reload(sgMod.subMod.PlayerMod)
    #reload(sgMod.subMod.SoldierMod)
    reload(sgMod.subMod.InterMod)
    reload(sgMod.subMod.WarMod)
    reload(sgMod.subMod.WallMod)
    reload(sgMod.subMod.MailMod)
    reload(sgMod.subMod.ItemMod)
    reload(sgMod.subMod.FriendMod)
    reload(sgMod.subMod.BagMod)
    reload(sgMod.subMod.BattleMod)
    reload(sgMod.subMod.RewardMod)
    reload(sgMod.subMod.InteractMod)
    reload(sgMod.subMod.MissionMod)
    reload(sgMod.subMod.ChatMod)
    reload(sgMod.subMod.RedisMod)
    reload(sgMod.subMod.ActivityMod)
    reload(sgMod.subMod.EventMod)
    reload(sgMod.subMod.LoginMod)        
    reload(sgMod.subMod.RankFightMod)        
            
#引入UI模块
def getDictUI():
    try:
        from sgMod.TemplateUI import TemplateUI
    except:
        TemplateUI = None
        
    try:
        from sgMod.TestUI import TestUI
    except:
        TestUI = None
        
    try:
        from sgMod.MapUI import MapUI
    except:
        MapUI = None
    try:
        from sgMod.BuildingUI import BuildingUI
    except:
        BuildingUI = None
    
    try:
        from sgMod.Building_pubUI import Building_pubUI
    except:
        Building_pubUI = None
    
    try:
        from sgMod.Building_resourceUI import Building_resourceUI
    except:
        Building_resourceUI = None
        
    try:
        from sgMod.Building_trainUI import Building_trainUI
    except:
        Building_trainUI = None
    
    try:
        from sgMod.Building_altarUI import Building_altarUI
    except:
        Building_altarUI = None
        
        
    try:
        from sgMod.Building_campUI import Building_campUI
    except:
        Building_campUI = None
    
    try:
        from sgMod.Building_schoolUI import Building_schoolUI
    except:
        Building_schoolUI = None
    
    try:
        from sgMod.Building_groundUI import Building_groundUI
    except:
        Building_groundUI = None
    try:
        from sgMod.Building_homeUI import Building_homeUI
    except:
        Building_homeUI = None
    
    try:
        from sgMod.Building_holdUI import Building_holdUI
    except:
        Building_holdUI = None
    
    try:
        from sgMod.BookUI import BookUI
    except:
        BookUI = None
    
    try:
        from sgMod.EquipUI import EquipUI
    except:
        EquipUI = None
    
    try:
        from sgMod.WarUI import WarUI
    except:
        WarUI = None
        
    try:
        from sgMod.WallUI import WallUI
    except:
        WallUI = None
    
    try:
        from sgMod.Building_clubUI import Building_clubUI
    except:
        Building_clubUI = None
    
    try:
        from sgMod.MailUI import MailUI
    except:
        MailUI = None
    
    try:
        from sgMod.FriendUI import FriendUI
    except:
        FriendUI = None
        
    try:
        from sgMod.PlayerUI import PlayerUI
    except:
        PlayerUI = None
        
    try:
        from sgMod.ItemUI import ItemUI
    except:
        ItemUI = None
    
    try:
        from sgMod.BagUI import BagUI
    except:
        BagUI = None
        
    try:
        from sgMod.VisitUI import VisitUI
    except:
        VisitUI = None
    
    try:
        from sgMod.LoginUI import LoginUI
    except:
        LoginUI = None
    try:
        from sgMod.MissionUI import MissionUI
    except:
        MissionUI = None
    try:
        from sgMod.ChatUI import ChatUI
    except:
        ChatUI=None
        
    try:
        from sgMod.RedisUI import RedisUI
    except:
        RedisUI = None
    
    try:
        from sgMod.ActivityUI import ActivityUI
    except:
        ActivityUI = None
        
    try:
        from sgMod.RankFightUI import RankFightUI
    except:
        RankFightUI = None
        
    dictUI = {
             #'Template':TemplateUI,
             #'Test':TestUI,
             'Map':MapUI,
             
             'Building':BuildingUI,
             'Building_pub':Building_pubUI,
             'Building_resource':Building_resourceUI,
             'Building_train':Building_trainUI,
             'Building_altar':Building_altarUI,
             'Building_camp':Building_campUI,
             'Building_school':Building_schoolUI,
             'Building_ground':Building_groundUI,
             'Building_club':Building_clubUI,
             'Building_home':Building_homeUI,
             'Building_hold':Building_holdUI,
             'Book':BookUI,
             'Equip':EquipUI,
             'War':WarUI,
             'Wall':WallUI,
             'Mail':MailUI,
             'Friend':FriendUI,
             'Player':PlayerUI,
             'Item':ItemUI,
             'Bag':BagUI,
             'Visit':VisitUI,
             'Login':LoginUI,
             'Mission':MissionUI,
             'Chat':ChatUI,
             'Redis':RedisUI,
             'Activity':ActivityUI,
             'RankFight':RankFightUI,
            }
    return dictUI

#引入模型模块
def getDictMod():
    try:
        from sgMod.subMod.TestMod import TestMod
    except:
        TestMod = None
        
    try:
        from sgMod.subMod.TemplateMod import TemplateMod
    except:
        TemplateMod = None
    try:
        from sgMod.subMod.BookMod import BookMod
    except:
        BookMod = None
    
    try:
        from sgMod.subMod.BuildingMod import BuildingMod
    except:
        BuildingMod = None
    try:
        from sgMod.subMod.building.Building_pubMod import Building_pubMod
    except:
        Building_pubMod = None
    try:
        from sgMod.subMod.building.Building_resourceMod import Building_resourceMod
    except:
        Building_resourceMod = None
    try:
        from sgMod.subMod.building.Building_schoolMod import Building_schoolMod
    except:
        Building_schoolMod = None
    try:
        from sgMod.subMod.building.Building_campMod import Building_campMod
    except:
        Building_campMod = None
    try:
        from sgMod.subMod.building.Building_trainMod import Building_trainMod
    except:
        Building_trainMod = None
    try:
        from sgMod.subMod.building.Building_altarMod import Building_altarMod
    except:
        Building_altarMod = None
    try:
        from sgMod.subMod.building.Building_clubMod import Building_clubMod
    except:
        Building_clubMod = None
    try:
        from sgMod.subMod.building.Building_groundMod import Building_groundMod
    except:
        Building_groundMod = None
    
    try:
        from sgMod.subMod.building.Building_homeMod import Building_homeMod
    except:
        Building_homeMod = None
    
    try:
        from sgMod.subMod.building.Building_holdMod import Building_holdMod
    except:
        Building_holdMod = None
    
    try:
        from sgMod.subMod.CoinMod import CoinMod
    except:
        CoinMod = None
    try:
        from sgMod.subMod.EquipMod import EquipMod
    except:
        EquipMod = None
    
    try:
        from sgMod.subMod.GeneralMod import GeneralMod
    except:
        GeneralMod = None
    try:
        from sgMod.subMod.MapMod import MapMod 
    except:
        MapMod = None
    try:
        from sgMod.subMod.PlayerMod import PlayerMod
    except:
        PlayerMod = None
    '''
    try:
        from sgMod.subMod.SoldierMod import SoldierMod
    except:
        SoldierMod = None
    '''
    try:
        from sgMod.subMod.InterMod import InterMod
    except:
        InterMod = None
        
    try:
        from sgMod.subMod.WarMod import WarMod
    except:
        WarMod = None
        
    try:
        from sgMod.subMod.WallMod import WallMod
    except:
        WallMod = None
        
    try:
        from sgMod.subMod.MailMod import MailMod
    except:
        MailMod = None
    
    try:
        from sgMod.subMod.FriendMod import FriendMod
    except:
        FriendMod = None
        
    try:
        from sgMod.subMod.ItemMod import ItemMod
    except:
        ItemMod = None
    
    try:
        from sgMod.subMod.BagMod import BagMod
    except:
        BagMod = None
        
    try:
        from sgMod.subMod.BattleMod import BattleMod
    except:
        BattleMod = None
        
    try:
        from sgMod.subMod.RewardMod import RewardMod
    except:
        RewardMod = None   
        
    try:
        from sgMod.subMod.InteractMod import InteractMod
    except:
        InteractMod = None
    
    try:
        from sgMod.subMod.MissionMod import MissionMod
    except:
        MissionMod = None  
    try:
        from sgMod.subMod.ChatMod import ChatMod
    except:
        ChatMod = None  
    
    try:
        from sgMod.subMod.RedisMod import RedisMod
    except:
        RedisMod = None
    
    try:
        from sgMod.subMod.ActivityMod import ActivityMod
    except:
        ActivityMod = None
    
    try:
        from sgMod.subMod.EventMod import EventMod
    except:
        EventMod = None
    
    try:
        from sgMod.subMod.RankFightMod import RankFightMod
    except:
        RankFightMod = None
    
    
    dictMod = {
             #'Example':TestMod,
             #'Template':TemplateMod,
             
             'Building':BuildingMod,
             'Building_pub':Building_pubMod,
             'Building_resource':Building_resourceMod,
             'Building_school':Building_schoolMod,
             'Building_camp':Building_campMod,
             'Building_train':Building_trainMod,
             'Building_altar':Building_altarMod,
             'Building_club':Building_clubMod,
             'Building_ground':Building_groundMod,
             'Building_home':Building_homeMod,
             'Building_hold':Building_holdMod,
             
             'Book':BookMod,
             'Coin':CoinMod,
             'Equip':EquipMod,
             'General':GeneralMod,
             'Map':MapMod,
             'Player':PlayerMod,
#             'Soldier':SoldierMod,
             'Inter':InterMod, #内政模型
             'War':WarMod, #战役模型
             'Wall':WallMod, #城墙模型
             'Mail':MailMod, #邮件模型
             'Friend':FriendMod, #好友模型
             'Interact':InteractMod,#交互模型
             'Item':ItemMod, #道具模型
             'Bag':BagMod, #背包模型
             'Battle':BattleMod, #战斗模型
             'Reward':RewardMod, #奖励模型
             'Mission':MissionMod, #任务模型
             'Chat':ChatMod,#聊天模型
             'Redis':RedisMod,#缓存模型
             'Activity':ActivityMod,
             'Event':EventMod,# 事件模型
             'RankFight':RankFightMod, #比武模型
            }
    return dictMod
if __name__ == '__main__':
    modReload()
    #print getDictMod()