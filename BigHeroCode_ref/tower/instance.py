# -*- coding: utf8 -*-
#高塔实例模块

tower_cfg = None

def init():
        global tower_cfg
        
        import engine.util.common as common
        
        import config
        import tower
        
        tower_cfg = common.parse_xml(config.TOWER_CFG_PATH)["floor"]
        
        tower.init()
        
def stop():
        import tower
        
        tower.stop()