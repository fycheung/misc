# -*- coding:utf-8 -*-
# author:Lijs
# date:2013-4-23
# 主线任务

import time
from sgLib.core import Gcore
from sgLib.base import Base


class TaskMod(Base):
    '''主线任务'''
    def __init__(self,uid):
        Base.__init__(self, uid)
        self.uid = uid
    
    #------------------------------START模块内部接口-------------------------------
    
    def getUserTaskInfo(self,fields=['*'],state=None,userId=None):
        '''@summary:得到玩家任务信息
        @param state: None得到所有任务，0未完成任务
        '''
        if not userId:
            userId = self.uid
        where = 'UserId=%s '%self.uid
        if state is not None:
            where +='AND TaskWortState=%s'%state
        where += ' ORDER BY CreateTime DESC'
        return self.db.out_rows('tb_task t,tb_cfg_task ct',fields,where)
    
    def getTaskInfo(self,fields=['*'],state=None):
        '''得到任务信息'''
        where = 'ct.TaskId=t.TaskId AND UserId=%s'%self.uid
        if state is not None:
            where +='AND TaskWortState=%s'%state
            
        return self.db.out_fields('tb_cfg_task ct,tb_task t',fields,where)
    
    def getCfgTask(self,userLevel,preTaskId=0):
        '''@summary:得到任务
        '''
        where = 'UserLevel=%s AND PreTaskId=%s'%(userLevel,preTaskId)
        
        return self.db.out_field('tb_task',['TaskId'],where)
    
    def getTaskDialog(self,taskId):
        '''得到玩家对话'''
        where = 'UserId=%s AND TaskId=%s ORDER BY DialogIndex'%(self.uid,taskId)
        return self.db.out_rows('tb_cfg_dialog',['DialogId','DialogContent'],where)
    
    
    def delTask(self,taskId):
        '''@summary:删除任务
          @return:
          False；系统错误
          >0：删除成功
          =0：对应任务不存在
        '''
        sql = "SELECT IF((TaskStatus AND GetDialog)==1,1,0) AS CanDel FROM \
            tb_task WHERE UserId=%s AND TaskId=%s"%(self.uid,taskId)
        row = self.db.fetchone(sql)
	if not row:
	    return False
        if row["CanDel"]:
            where = "UserId=%s AND TaskId=%s"%(self.uid,taskId)
            return self.db.delete("tb_task",where)
    
    def addTask(self):
        '''添加任务'''
        playerMod = Gcore.getMod('Player',self.uid)
        userLevel = playerMod.getUserBaseInfo(['UserLevel'])
    
        tasks = self.getTask(['PreTaskId','TaskDialog1'])
        if tasks:
            task = tasks[0]
            taskId = self.getCfgTask(userLevel, task['PreTaskId'])
        else:
            taskId = self.getCfgTask(userLevel)
        
        if taskId:
            data = {}
            data['UserId'] = self.uid
            data['TaskId'] = taskId
            data['CreateTime'] = time.time()
            dialogs = self.getTaskDialog(taskId)
            if dialogs:
                dialog = dialogs[0]
                data['NextDialogId']= dialog['DialogId'] #那不得完成一次对话就得触发一次更新tb_task表
            self.db.insert('tb_task',data) 
        
    
    def initTask(self):
        '''初始化玩家任务
        '''
        self.addTask()
        #玩家登陆
        #完成一次任务 前台传什么参数来 怎么知道该任务完成
        #升级一次 
        
    
def _test():
    uid = 1002
    t = TaskMod(uid)


if __name__ == "__main__":
    _test()
    