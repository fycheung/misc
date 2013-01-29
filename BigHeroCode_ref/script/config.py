# -*- coding: utf8 -*-
#全局配置文件

import engine.util.common as common

import engine.net.config as net_cfg
import engine.db.config  as db_cfg

app_cfg = common.parse_xml("../server_cfg/application.conf")

#初始化网络配置
net_cfg.config_port(app_cfg["net"]["int_port"], app_cfg["net"]["ext_port"])

#初始化数据库配置
db_cfg.config_gm_db("127.0.0.1", 3306, None, None, app_cfg["db"]["username"], app_cfg["db"]["password"], app_cfg["db"]["db_name"])