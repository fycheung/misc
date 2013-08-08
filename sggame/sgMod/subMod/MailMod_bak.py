# -*- coding:utf-8 -*-
# author:Lijs
# date:2013-3-28
# 游戏内部接口:邮件系统

import time

from sgLib.core import Gcore
from sgLib.base import Base

#邮件模块对应的ID
OptId2MailType = {
    '19003'  : 'YJ001',    #好友申请被拒绝邮件,参数需要加上拒绝方的名字
    '15071'  : 'YJ002',    #军团申请被拒绝邮件，参数需要加上军团的名字
    '15068'  : 'YJ003',    #被军团请出邮件，无需参数
    '15067'  : 'YJ004',    #军团任命邮件，参数需要加上原团长的名字和军团的名字
    '15070'  : 'YJ005',    #加入军团邮件，参数需要加上军团的名字
    '15064'  : 'YJ005',    #成功加入不需要审核的军团
    '10000'  : 'YJ006',    #背包已满
    '13051'  : 'YJ007',    #充值邮件，参数需要加上充值后得到的黄金值
    '1'      : 'YJ008',    #设为藩国
    '2_1'    : 'YJ009',    #解除藩国关系时发送给自己的邮件
    '2_2'    : 'YJ010',    #解除藩国关系时发送给占领者的邮件
}

def formatContent(optId, **param):
    '''通过optId获取邮件内容模板'''
    subopt = param.get('subopt', 0)
    if subopt:
        optId = str(optId) + '_' + str(subopt)
    else:
        optId = str(optId)
    mailId = OptId2MailType.get(optId, '')
    if not mailId:
        mailId = OptId2MailType.get('10000')
    otherparam = param.get('other', [])
    if type(otherparam) not in (list, tuple):
        otherparam = [otherparam,]
    content = map(str, otherparam)
    content.insert(0, mailId)
    return ';'.join(content)
    

def inString(field,values):
    '''
    @param string field 查询的字段
    @param string values 查询用到的数据
    @return string
    @author Lijs
    '''
    length = len(values)
    inStr = '0'
    if length:
        inStr = "%s in ("%field
        for v in values:
            inStr += "'%s',"%v
        inStr = inStr[:-1]+ ")"
    return inStr

class MailMod(Base):
    '''邮件系统'''
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
    

    #--------------------- 发附件邮件-------------
    def sendSystemMail(self, toUserId, goods, optId, **param):
        '''
           toUserId: 收件人ID
           goods:  {‘GoodsType’:type, 'GoodsId': id, 'GoodsNum': num}组成的列表,没有附件则[]
           optId:  操作ID，用于查找邮件模板的ID
           param:  字典，格式如：{'subopt': subopt, 'other':[]}如果一个协议有两个操作，则需要用到subopt
           return: 返回邮件ID
        '''
        content = formatContent(optId, **param)
        if not content or not toUserId:
            return 0
        mailConId = self.insMailCon(content)
        timeStamp = int(time.time())
        data = {
                'FromUserId': 0,
                'Subject': content,
                'ToUserId': toUserId,
                'MailConId': mailConId,
                'CreateTime': timeStamp,
                'MailUserType': 1,}
            
        mailId = self.db.insert('tb_mail', data)
        
        if goods != []:
            for adict in goods:
                adict['MailId'] = mailId        
            self.db.insertmany('tb_attachment', goods)
        Gcore.push(101, toUserId)
        
        return mailId
     
    def sendSetHoldMail(self, **kw):
        '''设置为潘国时发送系统邮件
            kw: {'ToUserId': userid, 'HolderName': xxx, 'GiveRatio': 0.05}
        '''
        toUserId = kw.get('ToUserId')
        holderName = kw.get('HolderName')
        giveRatio = kw.get('GiveRatio')*100
        return self.sendSystemMail(toUserId, [], 1, other = [holderName, giveRatio])
    
    def sendFreeHoldMail(self, **kw):
        '''解除潘国关系时发送系统邮件
            kw: {'ToUserId': HoldUserId, 'HolderName': nickname}
                                解除关系时会发两封邮件，一封给占领者，一封给自己, ToUserId只需对方的就好
            return: 发送的两封邮件ID列表
        '''
        holderId = kw.get('ToUserId')
        holderName = kw.get('HolderName')
        userName = self.getUserInfo('NickName')
        #发送给占领者的邮件
        hmailId = self.sendSystemMail(holderId, [], 2, subopt = 2, other = [userName, ])
        #发送给自己的邮件
        umailId = self.sendSystemMail(self.uid, [], 2, subopt = 1, other = [holderName, ])
        
        return [umailId, hmailId]
        
        
    def sendAttachment(self,toUserId,goods=[],subject='system',content='system award'):
        '''
                      发带有附件的邮件 
        toUserId:单人UserId 
        goods元素 {'GoodsType':,'GoodsId':,'GoodsNum':}
        @return 返回邮件ID
        '''
        sysId=0
        timeStamp=int(time.time())
        mailConId=self.insMailCon(content)
        date={'FromUserId':sysId,
              'Subject':subject,
              'ToUserId':toUserId,
              'MailConId':mailConId,
              'CreateTime':timeStamp,
              'MailUserType':1}
        mailId=self.db.insert('tb_mail',date)
        
        if goods!=[]:
            for adict in goods:
                adict['MailId']=mailId        
            self.db.insertmany('tb_attachment',goods)
        Gcore.push(101,toUserId)
        
        return mailId
    
    #============================================== 内部接口 ==============================================
    def sendMail(self,toUserIds,subject,content,mailUserType=2):
        '''
                     发送邮件
        @param toUserIds:发送对象Id，列表类型
        @param subject:标题
        @param content:内容
        @param mailUserType:邮件类型1为系统邮件，2为私人邮件
        @return 返回成功发送个数
        '''

        if mailUserType==1:
            fromUserId=0
        else:
            fromUserId=self.uid
        timeStamp=int(time.time())
        mailConId=self.insMailCon(content)
        result=0
        if len(toUserIds) and mailConId:
            #fields=['FromUserId','ToUserId','Subject','MailConId','CreateTime','MailUserType']
            vals=[]
            for toId in toUserIds:
                v = {}
                v['FromUserId'] = fromUserId
                v['ToUserId'] = toId
                v['Subject'] = subject
                v['MailConId'] = mailConId
                v['CreateTime'] = timeStamp
                v['MailUserType'] = mailUserType
                vals.append(v)
                
            #result=self.db.insert_rows('tb_mail',fields,vals)
            result=self.db.insertmany('tb_mail', vals)
            Gcore.push(101,toUserIds)
        return result

    def insMailCon(self,content):
        '''添加邮件内容'''
        timeStamp=int(time.time())
        date={'MailContent':content,'MailConCreateTime':timeStamp}
        return self.db.insert('tb_mail_con',date)
       
    def inexistNickName(self,nickNames):
        '''
                    返回不存在的玩家NickName
        '''
        inexistNickName =[]
        for nickName in nickNames:
            where = "NickName='%s'"%nickName
            exist = self.db.out_field('tb_user','NickName',where)
            if not exist: #收集不存在的玩家NickName
                inexistNickName.append(nickName)
        return inexistNickName
                     
    
             
    def getToUserId(self,toUserNickNames):
        where = inString('NickName',toUserNickNames)
        return self.db.out_list('tb_user','UserId',where)

        
    #----------------- 删除邮件用到的方法---------------------

    
    def delMail(self, listType, mailIds):
        '''
                    删除邮件
        @param listType:类型1为从收件箱删除，2为从发件箱删除
        @param mailIds:
        '''
        
        if isinstance(mailIds,(tuple,list)):
            mailIds = [str(mailId) for mailId in mailIds]
            where = " MailId IN ("+str.join(",",mailIds)+")"
        else:
            where = ' MailId=%s '% mailIds

        if listType==1:
            sql='UPDATE tb_mail SET MailStatus=CASE WHEN MailStatus=0 THEN 2 WHEN MailStatus=1 THEN 3 ELSE MailStatus END WHERE ToUserId=%s AND %s'%(self.uid,where)
        elif listType==2:
            sql='UPDATE tb_mail SET MailStatus=CASE WHEN MailStatus=0 THEN 1 WHEN MailStatus=2 THEN 3 ELSE MailStatus END WHERE FromUserId=%s AND %s'%(self.uid,where)
        return self.db.execute(sql)
    
    
    
    

    
        
    #----------------    显示邮件列表（收件箱，发件箱，换页查看）---------

    def getMailList(self,listType,page,pagePerNum):
        '''
                    获取邮件列表
        @param listType:列表类型1为收件箱子，2为发件箱
        @param page:页数
        @param pagePerNum:每页数量
        '''
        
        fields=['MailId','Subject','m.CreateTime','ReadStatus','MailUserType']
        if listType==1:#收件箱
            fields=['MailId','Subject','m.CreateTime','ReadStatus','MailUserType','FromUserId']
            where="m.ToUserId=%s and m.ToUserId=u.UserId and m.MailStatus not in(2,3) order by ReadStatus ASC,m.CreateTime DESC"%self.uid
        elif listType==2:#发件箱
            fields=['MailId','Subject','m.CreateTime','ReadStatus','MailUserType','u.NickName as NickName']
            where="m.FromUserId=%s and m.ToUserId=u.UserId and m.MailStatus not in(1,3) order by m.CreateTime DESC"%self.uid
        else:
            where=0
        where+=' LIMIT %s,%s'%((page-1)*pagePerNum,pagePerNum)
        mailList=self.db.out_rows('tb_mail m,tb_user u',fields,where)
        
        if listType == 1: #为收件箱，添加是否有附件的信息
            for mailData in mailList:
                fromUserId = mailData['FromUserId']
                #如果是系统邮件，则不发送昵称
                if fromUserId:
                    userNickName = self.db.out_field('tb_user', 'NickName', 'UserId=%s'%fromUserId)
                    mailData['NickName'] = userNickName
                mailId = mailData['MailId']
                mailData['HasAttachment']= self.hasAttachment(mailId)
        return mailList
    
    def mailCountByType(self,mailType):
        '''
                        收件箱/发件箱邮件总数
        '''
        where = '0'
        if mailType == 1: #收件箱
            where = "ToUserId=%s AND (MailStatus=0 OR MailStatus=1)"%(self.uid)
        elif mailType == 2: #发件箱
            where = "FromUserId=%s AND (MailStatus=0 OR MailStatus=2)"%(self.uid)
            
        return self.db.count('tb_mail',where)
    
    def finMailDatas(self,mailDatas,subjShowMax):
        '''
        '''
        for datas in mailDatas:
            subject = datas.get('Subject')
            attachmentId = datas.get('AttachmentId')
            mailType = datas.get('MailUserType')
#            print subject
            #系统邮件不对主题进行处理
            if subject and mailType != 1:
                length = len(subject)
                subject = '%s...'%subject[:6] if length>subjShowMax else subject #这里一个汉字也是一个字符
                datas['Subject'] = subject
#                print length,subject
            if attachmentId: #附件
                datas['attachments'] = self.getAttachments(attachmentId)
    
    
    
    
    def hasAttachment(self,mailId):
        '''邮件是否有附件'''
        count = self.db.count('tb_attachment',' MailId=%s '%mailId)
        
        return 1 if count else 0
            
    

    
    def getAttachments(self,attachmentId):
        '''
                    得到值大于0所有附件 dict表
        '''
        fields =['*']
        where = 'AttachmentId=%s'%attachmentId
        attachs = self.db.out_fields('tb_attachment',fields,where)
        self.filterAttachments(attachs)
        
        return attachs
    
    def filterAttachments(self,attachs):
        '''
                    过滤掉不大于0的所有附件,并删除无关附件的内容
        '''
        if attachs.has_key('AttachmentId'):
            del attachs['AttachmentId']
        for key in attachs.keys():
            if not attachs[key]:
                del attachs[key]
    
    #------------------- 显示邮件 -----------------
    
    def getMailInfo(self,mailId):
        '''
                    获取邮件详细信息
        @param mailId:
        '''
        

        fields=['MailId','Subject','MailContent','FromUserId','ToUserId']
        where="m.MailId=%s AND m.MailConId=c.MailConId"%(mailId)
        mailInfo=self.db.out_fields('tb_mail m,tb_mail_con c',fields,where)
        attachments=self.getMailAttachMents(mailId)
        #if attachments is None:
            #attachments=()
        mailInfo['attachments']=attachments
        return mailInfo
    
    def updateReadStatus(self,mailId):
        '''更改阅读状态'''
        rows={'ReadStatus':1}
        where='MailId=%s'%mailId
        self.db.update('tb_mail',rows,where)
        
    def getMailAttachMents(self,mailId):
        '''
                    获取附件信息
        @param mailId:
        '''
        fields = ["AttachmentId","GoodsType","GoodsId","GoodsNum"]
        where = ' MailId=%s '%mailId
        attachs = self.db.out_rows('tb_attachment',fields,where)
        return attachs
    
    
    #---------------------- 接收附件-----------------------
    def removeAttachment(self,attachmentId):
        '''
                    删除附件
        @param attachmentId:
        '''
        where='attachmentId=%s'%attachmentId
        return self.db.delete('tb_attachment',where)
    
    
    def receiveAttachment(self,attachIds,optId,classMethod,param):
        '''
                    获取附件
        @param attachIds:附件ID
        @param optId:
        @param classMethod:
        @param param:
        @return 返回成功接收的附件 
        GoodsType1装备，2道具，3资源 
        GoodsId 装备类型ID,道具类型ID,资源类型ID
        GoodsNum 物品数量
        EquipId 装备ID,其他类型该值为0
        '''
        
        fields=['AttachmentId','GoodsType','GoodsId','GoodsNum']
        if isinstance(attachIds,(tuple,list)):
            attachIds = [str(attachId) for attachId in attachIds]
            where = " AttachmentId IN ("+str.join(",",attachIds)+")"
        else:
            where = ' AttachmentId=%s '% attachIds
        attachDicts = self.db.out_rows('tb_attachment',fields,where)
        successSend=[]
        for attachDict in attachDicts:
            row = {'AttachmentLock': 1}
            where = 'AttachmentId=%s and AttachmentLock=0'%attachDict['AttachmentId']
            affectedrows = self.db.update('tb_attachment', row, where)
            if affectedrows:
                result=0
                if attachDict['GoodsType'] == 1 or attachDict['GoodsType'] == 2:
                    modBag=Gcore.getMod('Bag',self.uid)
                    result = modBag.addGoods(attachDict['GoodsType'],attachDict['GoodsId'],attachDict['GoodsNum'],False)
                    if result==0:
                        row = {'AttachmentLock': 0}
                        where = 'AttachmentId=%s and AttachmentLock=1'%attachDict['AttachmentId']
                        self.db.update('tb_attachment', row, where)
                        return -1
                    if not result<0:
                        attachDict['EquipId']=result[0]
                        successSend.append(attachDict)
                        self.removeAttachment(attachDict['AttachmentId'])
                    
#                 if attachDict['GoodsType'] ==2:
#                     modBag=Gcore.getMod('Bag',self.uid)
#                     result = modBag.addGoods(attachDict['GoodsType'],attachDict['GoodsId'],attachDict['GoodsNum'],False)
#                     if result==0:
#                         row = {'AttachmentLock': 0}
#                         where = 'AttachmentId=%s and AttachmentLock=1'%attachDict['AttachmentId']
#                         self.db.update('tb_attachment', row, where)
#                         return -1
#                     if not result <=0:
#                         attachDict['EquipId']=0
#                         successSend.append(attachDict)
#                         self.removeAttachment(attachDict['AttachmentId'])
                    
                if attachDict['GoodsType'] == 3:
                    if attachDict['GoodsId'] == 5:    #加荣誉
                        pMod = Gcore.getMod('Player', self.uid)
                        result = pMod.gainHonour(attachDict['GoodsNum'], optId)
                    elif attachDict['GoodsId'] == 6:  #加贡献
                        clubMod = Gcore.getMod('Building_club', self.uid)
                        clubBuildInfo = clubMod.getClubBuildingInfo()
                        clubId = clubMod.getUserClubId()
                        if clubBuildInfo and clubId:
                            result = clubMod.gainDeveote(clubId, 3, devoteNum=attachDict['GoodsNum'])
                        else:
                            result = 1  #没有外使院或者军团，该附件直接删除
                    else:
                        modCoin=Gcore.getMod('Coin',self.uid)
                        result=modCoin.GainCoin(optId,attachDict['GoodsId'],attachDict['GoodsNum'],classMethod,param)
                    if not result<=0:
                        attachDict['EquipId']=0
                        successSend.append(attachDict)
                        self.removeAttachment(attachDict['AttachmentId'])
                    else:
                        row = {'AttachmentLock': 0}
                        where = 'AttachmentId=%s and AttachmentLock=1'%attachDict['AttachmentId']
                        self.db.update('tb_attachment', row, where)
        
        return successSend
        

    def countUnReadNum(self):
        '''
                    获取未读邮件数量
        '''
        where='ToUserId=%s AND ReadStatus=0 AND (MailStatus=0 OR MailStatus=1)'%self.uid
        res=self.db.out_field('tb_mail','count(1)',where)
        if res is None:
            res=0
        return res
    

    def getRelatedUsers(self):
        '''
                    获取联系用户
        '''
        modFriend = Gcore.getMod('Friend', self.uid)
        friends = modFriend.getFriends() #好友
        modClub = Gcore.getMod('Building_club', self.uid)
        clubMembers = modClub.getClubMembers()
        
        return friends,clubMembers   



            
                    
def _test1():
    uid= 1012
    m = MailMod(uid)
#    print m.getToUserId(['Nicknn','sadas','asdas','sad'])
#    print m.inexistUserId([1092,1999,2223,2221])
#    print m.inexistNickName(['Nicknn','sadas','asdas','sad'])
    print m.sendAttachment(43438,[{'GoodsType':2,'GoodsId':101,'GoodsNum':99},{'GoodsType':2,'GoodsId':102,'GoodsNum':5},{'GoodsType':1,'GoodsId':2,'GoodsNum':1}],'mod发送附件测试','奖励道具')
#    print m.sendMail(['43299'], 'mod sendMail2', 'System Test2', 1)
#    print m.getMailList(1,1,2)
#    print m.getMailInfo(261)
#    print m.getRelatedUsers()
#    print m.receiveAttachment([274,273,272],11099,'MailMod.Test',{})
#    m.delMail(1,261)

    return
    for i in range(9):
        m.sendSysMail(userNickNames=['NickName1011'],
                      subject='系统%s'%i,
                      mailCon='奖励%s'%i,
                      attachList=[{'GoodsType':2,'GoodsId':1,'GoodsNum':1},
                                  {'GoodsType':1,'GoodsId':103,'GoodsNum':1},
                                  {'GoodsType':2,'GoodsId':11,'GoodsNum':3},
                                  {'GoodsType':3,'GoodsId':4,'GoodsNum':110},
                                  {'GoodsType':1,'GoodsId':101,'GoodsNum':11},
                                  {'GoodsType':1,'GoodsId':201,'GoodsNum':12},
                                  {'GoodsType':1,'GoodsId':102,'GoodsNum':10}]
                      )
        
def _test2():
    uid = 43508
    m = MailMod(uid)
    #m.sendMail([1001,43668,43744], 'test', 'test')
#     m.sendFreeHoldMail(ToUserId=1011, HolderName='nnn')
    m.sendSystemMail(1011, [], 19003, other=['nnnn',])
    
if __name__ == "__main__":
    #_test1()
    _test2()
    
    
    