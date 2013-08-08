#-*- coding:utf-8 -*-
#author:Lijs
#date:2013-3-28
#游戏外部接口:邮件系统
from __future__ import division
import math
import sys
from sgLib.core import Gcore,inspector
from sgLib.common import filterInput

def escapeSplit(s, sep=';'):
    '''@param string sep 分隔符'''
    strs = s.split('%s'%sep)
    return [n.strip() for n in strs if n.strip()]


class MailUI(object):
    '''邮件系统外部接口'''

    def __init__(self, uid):
        self.mod = Gcore.getMod('Mail', uid)
        self.uid = uid
    
    
    @inspector(18001)
    def ListRelatedUser(self,param = {}):
        '''
                    返回玩家好友及军团成员数据
        '''
        optId = 18001
        friends,clubMembers = self.mod.getRelatedUsers()
        body = {'friends':friends,'clubMembers':clubMembers}
        return Gcore.out(optId, body = body)
    
    
    @inspector(18002, ['MailIds', 'MailType'])
    def DelMail(self, param = {}):   
        '''删除邮件'''
        optId = 18002
        
        mailIds = param['MailIds'] 
        listType = param['MailType']
        mids = []
        if listType == 1:
            for i in range(0, len(mailIds)):
                re = self.mod.hasAttachment(mailIds[i])
                if re == 0:
                    mids.append(mailIds[i])
        elif listType == 2:#发信箱不做是否有附件检查
            mids = mailIds
        result = 0
        if mids:
            result = self.mod.delMail(listType, mids)
        result = result if result else 0
        body = {'result': result}
        return Gcore.out(optId, body = body)
    
    
    @inspector(18003, ['MailType', 'Page'])
    def MailList(self, param = {}):   
        '''
                    收件箱/发件箱列表
        @param param['MailType']=1 表示收件箱
               param['MailType']=2 表示发件箱 
        '''
        optId = 18003
        mailType = int(param['MailType'])
        page = int(param['Page']) #页码
        if not page: #默认为第一页
            page = 1
        if mailType not in (1,2):
            return Gcore.error(optId,-18003999)   #MailType值不对
        mailCfg = Gcore.loadCfg(Gcore.defined.CFG_MAIL)
        pagePerNum  = int(mailCfg['MailShowPerPageMax'])  #每页的邮件数
        mailCount = int(self.mod.mailCountByType(mailType)) #收件箱/发件箱中邮件总数
        mailDatas = self.mod.getMailList(mailType, page, pagePerNum)   #每页显示的邮件数据

        subjShowMax  = mailCfg['SubjectShowMax'] #邮件主题显示最大长度
        self.mod.finMailDatas(mailDatas, subjShowMax)
        totalPage = int(math.ceil(1.0*mailCount/pagePerNum))
        
        body = {'mailDatas': mailDatas, 'page': page, 'mailCount': mailCount, 'totalpage': totalPage}
        return Gcore.out(optId, body = body)
    
    
    @inspector(18004, ['MailType', 'MailId'])
    def MailInfo(self, param = {}):   
        '''收件箱/发件箱中某邮件内容
        @param param['MailType']= 1 表示收件箱
               param['MailType']= 2 表示发件箱 
               param['MailId']表示邮件id
        '''
        optId = 18004
        
        mailId = param['MailId'] 
        if param['MailType'] not in (1, 2):
            return Gcore.error(optId, -18004999)   #MailType值不对
        if not isinstance(mailId, (int, long)):     #为数字
            return Gcore.error(optId, -18004999)  
        
        mailInfoDict = self.mod.getMailInfo(mailId)   
        self.mod.updateReadStatus(mailId)
        
        body = {'mailInfoDict': mailInfoDict}
        return Gcore.out(optId, body = body)
    
    
    @inspector(18005, ['MailId'])
    def ReceiveAttachments(self, param = {}):
        '''领取附件 param['MailId']邮件ID'''
        optId = 18005
        classMethod = '%s,%s'%(self.__class__.__name__,sys._getframe().f_code.co_name)
        mailId = param['MailId']
        if not mailId:
            return Gcore.error(optId, -18005999)
        if not self.mod.hasAttachment(mailId):
            return Gcore.error(optId, -18005002) #该邮件没有附件
        
        result = self.mod.receiveAttachment(mailId, optId, classMethod, param)
        if not result and type(result) == list:
            return Gcore.error(optId, -18005001)#背包已满了  待优化
        elif result == 0:    #并发时返回空
            result = []
        
        return Gcore.out(optId, {'Result': result})
    
    
    @inspector(18006, ['ToUserNickNames', 'Subject', 'Content'])
    def InsMessage(self, param = {}):
        '''
                    发送邮件
        '''
        import sys;
        reload(sys);sys.setdefaultencoding('utf8')
        
        optId = 18006
        
        toUserNickNames = param['ToUserNickNames']     #收件人昵称字符串
        subject = param['Subject']
        content = param['Content']
        toUserNickNames = escapeSplit(toUserNickNames) #解析昵称字符串
        if not subject or (not content) or (not toUserNickNames):
            return Gcore.error(optId, -18006003)       #邮件信息不完整
        
        mailCfg = Gcore.loadCfg(Gcore.defined.CFG_MAIL)
        subjectMin = mailCfg['SubjectMin'] #主题最小字符数
        subjectMax = mailCfg['SubjectMax'] #主题最大字符数
        contentMin = mailCfg['ContentMin']
        contentMax = mailCfg['ContentMax']
        toUserMax = mailCfg['MailSendMax'] #同时发送邮件最大数量
        
        toUserIds = self.mod.getToUserId(toUserNickNames) #根据昵称，得到玩家id
        if not toUserIds:
            return Gcore.error(optId, -18006004) #输入玩家昵称有误
        
        #最多同时发送邮件给五个玩家,最少一个
        numToUserId = len(toUserIds)
        if numToUserId > toUserMax:
            #不能超过5个玩家
            return Gcore.error(optId, -18006001)
        if self.uid in toUserIds:
            return Gcore.error(optId, -18006002)#不能发信息给自己
        
        #过滤主题和邮件内容
        subject = filterInput(subject, subjectMin, subjectMax, b_Replace = True, b_chat = True)
        if subject == -1:
            return Gcore.error(optId, -18006993)#长度不符合要求
        if subject == -2:
            return Gcore.error(optId, -18006991)#特殊字符
        content = filterInput(content, contentMin, contentMax, b_Replace = True, b_chat = True)
        if content == -1:
            return Gcore.error(optId, -18006993)#长度不符合要求
        if content == -2:
            return Gcore.error(optId, -18006991)#特殊字符
           
        param['ToUserIds'] = toUserIds
        result = self.mod.sendMail(toUserIds, subject, content, 2)        
        body = {'result': result}
        
        recordData = {'uid': self.uid, 'ValType': numToUserId, 'Val': 1}#成就,任务记录
        return Gcore.out(optId, body = body, mission = recordData)
    
    def CountUnReadNum(self, param = {}):
        optId = 18007
        num = self.mod.countUnReadNum()
        return Gcore.out(optId, {'UnReadNum': num})
    
#end class MailUI

def _test():
    '''测试'''
    uid = 44495
    c = MailUI(uid)
    #c.ReceiveAttachment({'MailId':10100})
#    print c.ListRelatedUser()
#    data={'ToUserNickNames':'NickName1011','Subject':'你好毛泽东','Content':'S大 S'}
#    print c.InsMessage(data)
#    print c.DelMail({'MailIds':[3544,3545],'MailType':1})
#    print c.MailList({'MailType':1,'Page':1})
#    print c.MailInfo({'MailType':1,'MailId':3315})
#    print c.CountUnReadNum()


if __name__ == '__main__':
    _test()    
