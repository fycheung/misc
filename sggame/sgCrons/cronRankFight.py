# -*- coding:utf-8 -*-
# author:Lizr
# date:2013-8-8
# 比武排名快照，用于发奖励，每天10点运行

import time
from os.path import dirname,abspath

system_root = dirname(dirname( abspath( __file__ ) ) ) #定义上层目录为根目录 
import sys;sys.path.insert(0,system_root)  #把项目根目录加入默认库路径 

curtime = time.time()
from sgLib.core import Gcore

#=====Content Begin=======

db = Gcore.getDB()
sql = 'INSERT INTO tb_rank_fight_last (RankId,UserId) SELECT RankId,UserId FROM tb_rank_fight ON DUPLICATE KEY UPDATE UserId = VALUES(UserId)'
db.execute(sql)

sql = 'UPDATE tb_rank_fight_last SET Rewarded=0,RewardTime=NOW()'
db.execute(sql)

runtime = time.time()-curtime
print 'Finish at:',Gcore.common.now()
print 'Total Runtime:', runtime
