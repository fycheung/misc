# -*- coding: UTF-8 -*- 
# 通讯协议配置 字典
# 系统编号3位 + 方法编号3位

#ProCfg = {}
"""外部调用"""
#100帐号登录、安全验证模块
#ProCfg[10001] = "AccountUI.Login"          #验证登录


#分布配置
#PROCFG = {}
#PROCFG["200"] = "self.mapProxy"
#PROCFG["300"] = "self.battleProxy"

# #200地图模块
# ProCfg["200001"] = "self.mapRun"               #玩家跑动
# ProCfg["200002"] = "self.mapLoad"              #获取坐标可视范围的玩家信息
# ProCfg["200003"] = "self.mapSwitch"            #地图场景切换通知

# #300战斗模块
# ProCfg["300000"] = "self.ConnectGateway"           #主动发起战斗
# ProCfg["300001"] = "self.battleCall"           #主动发起战斗
# ProCfg["300002"] = "self.battleAccept"         #接受技能选择


#内部调用
'''
selfCallCfg = {}
selfCallCfg["STATECHANGE"] = "100002"       #角色上线下线通知
selfCallCfg["SENCECHANGE"] = "200004"       #场景切换
selfCallCfg["BATTLEOK"] = "300003"          #触发播放战斗动画
'''