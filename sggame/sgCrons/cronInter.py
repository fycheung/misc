#coding:utf8
import time
from os.path import dirname,abspath

system_root = dirname(dirname( abspath( __file__ ) ) ) #定义上层目录为根目录 
print 'system_root',system_root
import sys;sys.path.insert(0,system_root)  #把项目根目录加入默认库路径 

curtime = time.time()
from sgLib.core import Gcore
Gcore.getMod('Inter',1).updateInterGeneral()

runtime = time.time()-curtime
print 'Finish at:',Gcore.common.now()
print 'Total Runtime:', runtime
