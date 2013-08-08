# -*- coding:utf-8 -*-
# author:Lijs
# date:2013-3-28
# 游戏内部接口:邮件系统

import time
import json

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
    optId = str(optId) + '_' + str(subopt) if subopt else str(optId)
    
    mailId = OptId2MailType.get(optId, '')
    mailId = mailId if mailId else OptId2MailType.get('10000')  #默认背包已满
    
    otherparam = param.get('other', [])
    if type(otherparam) not in (list, tuple):
        otherparam = [otherparam,]
    
    content = map(str, otherparam)
    content.insert(0, mailId)
    return ';'.join(content)

class MailMod(Base):
    '''邮件系统'''
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
    
    def sendSystemMail(self, toUserId, goods, optId, **param):
        '''主要用于发送有模板的邮件，服务后台请用sendOtherMail
           toUserId: 收件人ID(单人)
           goods:  {‘GoodsType’:type, 'GoodsId': id, 'GoodsNum': num}组成的列表,没有附件则[]
           optId:  操作ID，用于查找邮件模板的ID
           param:  字典，格式如：{'subopt': subopt, 'other':[]}如果一个协议有两个操作，则需要用到subopt
           return: 返回邮件ID
        '''
        content = formatContent(optId, **param)
        if not content or not toUserId:
            return 0
        mailConId = self.insMailCon(content, goods)
        timeStamp = int(time.time())
        data = {
                'FromUserId': 0,
                'Subject': content,
                'ToUserId': toUserId,
                'MailConId': mailConId,
                'CreateTime': timeStamp,
                'MailUserType': 1,
                }
        mailId = self.db.insert('tb_mail', data)
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
        
        
    def sendOtherMail(self, toUserIds = [], goods = [], subject = 'system', content = 'system award', mailtype = 3):
        '''
                      发带有附件的邮件 ,可用于服务后台发放补偿、奖励
        toUserId:UserId列表 ,为空，则发放全服
        goods元素 {'GoodsType':,'GoodsId':,'GoodsNum':}列表
        '''
        sysId = 0
        timeStamp = int(time.time())
        if not toUserIds:
            toUserIds = self.db.out_list('tb_user', 'UserId')
        for i in xrange(0, len(toUserIds), 200):
            datalist = []
            for uid in toUserIds[i: i + 200]:
                mailConId = self.insMailCon(content, goods)
                data = {'FromUserId': sysId,
                        'Subject': subject,
                        'ToUserId': uid,
                        'MailConId': mailConId,
                        'CreateTime': timeStamp,
                        'MailUserType': mailtype,
                        }
                datalist.append(data)
            self.db.insertmany('tb_mail', datalist)
        Gcore.push(101, toUserIds)
    
    
    def sendMail(self, toUserIds, subject, content, mailUserType=2):
        '''
                     发送邮件
        @param toUserIds:发送对象Id，列表类型
        @param subject:标题
        @param content:内容
        @param mailUserType:邮件类型1为系统邮件，2为私人邮件
        @return 返回成功发送个数
        '''
        if mailUserType == 1:
            fromUserId = 0
        else:
            fromUserId = self.uid
        timeStamp = int(time.time())
        mailConId = self.insMailCon(content)
        result = 0
        if len(toUserIds) and mailConId:
            vals = []
            for toId in toUserIds:
                v = {}
                v['FromUserId'] = fromUserId
                v['ToUserId'] = toId
                v['Subject'] = subject
                v['MailConId'] = mailConId
                v['CreateTime'] = timeStamp
                v['MailUserType'] = mailUserType
                vals.append(v)
            
            result = self.db.insertmany('tb_mail', vals)
            Gcore.push(101, toUserIds)
        return result
    

    def insMailCon(self, content, goodslist = []):
        '''添加邮件内容'''
        timeStamp = int(time.time())
        if goodslist:
            for i in range(len(goodslist)):
                goodslist[i]['AttachmentId'] = i
            attachment = json.dumps(goodslist)
            data = {'MailContent': content, 'Attachment': attachment, 'MailConCreateTime': timeStamp}
        else:
            data = {'MailContent': content, 'MailConCreateTime': timeStamp}
        return self.db.insert('tb_mail_con', data)                     
             
    def getToUserId(self, toUserNickNames):
        where = self.db.inWhere('NickName', toUserNickNames)
        return self.db.out_list('tb_user', 'UserId', where)

    
    def delMail(self, listType, mailIds):
        '''
                    删除邮件
        @param listType:类型1为从收件箱删除，2为从发件箱删除
        @param mailIds:
        '''
        if isinstance(mailIds,(tuple,list)):
            mailIds = [str(mailId) for mailId in mailIds]
            where = " MailId=" + str.join(" OR MailId=", mailIds)
        else:
            where = ' MailId=%s '% mailIds

        if listType==1:
            sql='UPDATE tb_mail SET MailStatus=CASE WHEN MailStatus=0 THEN 2 WHEN MailStatus=1 THEN 3 ELSE MailStatus END WHERE ToUserId=%s AND %s'%(self.uid,where)
        elif listType==2:
            sql='UPDATE tb_mail SET MailStatus=CASE WHEN MailStatus=0 THEN 1 WHEN MailStatus=2 THEN 3 ELSE MailStatus END WHERE FromUserId=%s AND %s'%(self.uid,where)
        return self.db.execute(sql)
    

    def getMailList(self, listType, page, pagePerNum):
        '''
                    获取邮件列表
        @param listType:列表类型1为收件箱子，2为发件箱
        @param page:页数
        @param pagePerNum:每页数量
        '''
        
        fields = ['MailId', 'Subject', 'm.CreateTime', 'ReadStatus', 'MailUserType']
        if listType == 1:#收件箱
            fields = ['MailId','Subject','m.CreateTime','ReadStatus','MailUserType','FromUserId']
            where = "m.ToUserId=%s and m.ToUserId=u.UserId and m.MailStatus not in(2,3) order by ReadStatus ASC,m.CreateTime DESC"%self.uid
        elif listType == 2:#发件箱
            fields = ['MailId','Subject','m.CreateTime','ReadStatus','MailUserType','u.NickName as NickName']
            where = "m.FromUserId=%s and m.ToUserId=u.UserId and m.MailStatus not in(1,3) order by m.CreateTime DESC"%self.uid
        else:
            where = 0
        where += ' LIMIT %s,%s'%((page - 1)*pagePerNum, pagePerNum)
        mailList = self.db.out_rows('tb_mail m,tb_user u', fields, where)
        
        if listType == 1: #为收件箱，添加是否有附件的信息
            for mailData in mailList:
                fromUserId = mailData['FromUserId']
                #如果是系统邮件，则不发送昵称
                if fromUserId:
                    userNickName = self.db.out_field('tb_user', 'NickName', 'UserId=%s'%fromUserId)
                    mailData['NickName'] = userNickName
                mailId = mailData['MailId']
                mailData['HasAttachment'] = self.hasAttachment(mailId)
        return mailList
    
    def mailCountByType(self, mailType):
        '''
                        收件箱/发件箱邮件总数
        '''
        where = '0'
        if mailType == 1: #收件箱
            where = "ToUserId=%s AND (MailStatus=0 OR MailStatus=1)"%(self.uid)
        elif mailType == 2: #发件箱
            where = "FromUserId=%s AND (MailStatus=0 OR MailStatus=2)"%(self.uid)
            
        return self.db.count('tb_mail', where)
    
    def finMailDatas(self, mailDatas, subjShowMax):
        '''对邮件主题进行处理'''
        for datas in mailDatas:
            subject = datas.get('Subject')
            #attachmentId = datas.get('AttachmentId')    #?有AttachmentId这个字段吗？
            mailType = datas.get('MailUserType')
#            print subject
            #系统邮件不对主题进行处理
            if subject and mailType not in (1, 3):
                length = len(subject)
                subject = '%s...'%subject[:6] if length>subjShowMax else subject #这里一个汉字也是一个字符
                datas['Subject'] = subject
    
    
    def hasAttachment(self, mailId):
        '''邮件是否有附件 (仅查看收信箱的邮件是否含有附件)'''
        
        where = 'ToUserId=%s AND MailId=%s AND m.MailConId = c.MailConId'%(self.uid, mailId)
        attachment = self.db.out_field('tb_mail_con c, tb_mail m', 'Attachment', where)
        return 1 if attachment else 0
    
    
    def getMailInfo(self, mailId):
        '''
                    获取邮件详细信息
        @param mailId:
        '''
        fields = ['MailId', 'Subject', 'MailContent', 'FromUserId', 'ToUserId', 'Attachment']
        where = "m.MailId=%s AND m.MailConId=c.MailConId"%(mailId)
        mailInfo = self.db.out_fields('tb_mail m,tb_mail_con c',fields,where)
        
        attachments = mailInfo.pop('Attachment')
        attachments = json.loads(attachments) if attachments else {}
        #mailInfo['attachments'] = attachments['Attachment']
        mailInfo['attachments'] = attachments
        return mailInfo
    
    def updateReadStatus(self, mailId):
        '''更改阅读状态'''
        rows={'ReadStatus': 1}
        where='MailId=%s'%mailId
        self.db.update('tb_mail', rows, where)
    
    
    def receiveAttachment(self, mailId, optId, classMethod, param):
        '''
                    获取附件
        @param mailId: 邮件ID
        @param optId:
        @param classMethod:
        @param param:
        @return 返回成功接收的附件 
        GoodsType1装备，2道具，3资源 
        GoodsId 装备类型ID,道具类型ID,资源类型ID
        GoodsNum 物品数量
        EquipId 装备ID,其他类型该值为0
        '''
        mailConId = self.db.out_field('tb_mail', 'MailConId', 'MailId=%s AND ToUserId=%s'%(mailId, self.uid))
        locktime = int(time.time())
        row = {'AttachmentLock': locktime}
        where = 'MailConId=%s and AttachmentLock<%s'%(mailConId, locktime - 5)  #5秒内只能有一次操作，防止并发
        affectedrows = self.db.update('tb_mail_con', row, where)
        if affectedrows:
            attachDicts = self.db.out_field('tb_mail_con', 'Attachment', 'MailConId=%s'%mailConId)
            attachDicts = json.loads(attachDicts) if attachDicts else []
            #判断背包是否有足够的格子
            modBag = Gcore.getMod('Bag', self.uid)
            modCoin = Gcore.getMod('Coin', self.uid)
            if not modBag.canAddInBag(attachDicts):
                return []
            for attachDict in attachDicts:
                if attachDict['GoodsType'] in (1, 2, 4, 5):
                    result = modBag.addGoods(attachDict['GoodsType'], attachDict['GoodsId'], attachDict['GoodsNum'], False)
                    attachDict['EquipId'] = result[0]
                elif attachDict['GoodsType'] == 3:
                    if attachDict['GoodsId'] == 5:    #加荣誉
                        pMod = Gcore.getMod('Player', self.uid)
                        pMod.gainHonour(attachDict['GoodsNum'], optId)
                    elif attachDict['GoodsId'] == 6:  #加贡献
                        clubMod = Gcore.getMod('Building_club', self.uid)
                        clubBuildInfo = clubMod.getClubBuildingInfo()
                        clubId = clubMod.getUserClubId()
                        if clubBuildInfo and clubId:
                            clubMod.gainDeveote(clubId, 3, devoteNum = attachDict['GoodsNum'])
                    else:
                        modCoin.GainCoin(optId, attachDict['GoodsId'], attachDict['GoodsNum'], classMethod, param)
                    attachDict['EquipId'] = 0
            #更新附件
            self.db.update('tb_mail_con', {'Attachment': ''}, 'MailConId=%s'%mailConId)
            return attachDicts
        
        return 0
        

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
        
        return friends, clubMembers   



def _test():
    uid = 44495
    m = MailMod(uid)
    #print m.hasAttachment(10100)
    
#    m.receiveAttachment(10104, 18005, 'receiveAttachment', {'MailId': 10104})
    goods = [{'GoodsType': 1, 'GoodsId': 8, 'GoodsNum': 10},
             {'GoodsType': 2, 'GoodsId': 103, 'GoodsNum': 2},
             {'GoodsType': 2, 'GoodsId': 303, 'GoodsNum': 2},
             {'GoodsType': 3, 'GoodsId': 1, 'GoodsNum': 200},
             {'GoodsType': 3, 'GoodsId': 2, 'GoodsNum': 2000},
             {'GoodsType': 3, 'GoodsId': 3, 'GoodsNum': 2000},
             {'GoodsType': 3, 'GoodsId': 4, 'GoodsNum': 50}]
    m.sendOtherMail([1011,], goods, subject='测试邮件')
#    m.sendMail([1001,43668,43744], 'test', 'test')
#    m.sendFreeHoldMail(ToUserId=1011, HolderName='nnn')
#    m.sendSystemMail(1011, [], 19003, other=['nnnn',])
    
if __name__ == "__main__":
    _test()
    
    
    