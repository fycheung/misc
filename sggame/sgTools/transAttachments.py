#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: qiudx
# date: 2013/08/05
# 用来将邮件附件从tb_attachment转移到tb_mail_con里
# 外网运行前需要在tb_mail_con里添加两字段Attachment,AttachmentLock

import json
from sgLib.core import Gcore

class TransTools(object):
    '''转移附件的类'''
    
    def __init__(self):
        self.db = Gcore.getNewDB()
        self.mailConId2Goods = {}
        
    def checkAttachment(self):
        '''将所有含有附件的邮件内容ID和附件对应'''
        fileds = ['m.MailId as MailId', 'm.MailConId as MailConId', 'GoodsType', 'GoodsId', 'GoodsNum']
        where = 'm.MailId = a.MailId'
        res = self.db.out_rows('tb_mail m, tb_attachment a', fileds, where)
        for e in res:
            good = {}
            good['GoodsType'] = e['GoodsType']
            good['GoodsId'] = e['GoodsId']
            good['GoodsNum'] = e['GoodsNum']
            if e['MailConId'] not in self.mailConId2Goods:
                self.mailConId2Goods[e['MailConId']] = []
            self.mailConId2Goods[e['MailConId']].append(good)
            
    def transAttachment(self):
        '''将所有附件更新到tb_mail_con表中'''
        for mailConId in self.mailConId2Goods:
            attachments = self.mailConId2Goods[mailConId]
            data = json.dumps(attachments)
            self.db.update('tb_mail_con', {'Attachment': data}, 'MailConId=%s'%mailConId)
    
    def run(self):
        '''附件转移'''
        print 'Check now...'
        self.checkAttachment()
        if not self.mailConId2Goods:
            print 'No attachment to be transferred'
            return
        for mailConId in self.mailConId2Goods:
            print '===MailConId: ', mailConId
            for goods in self.mailConId2Goods[mailConId]:
                print goods
        self.transAttachment()
        print 'All over...'
        

def main():
    t = TransTools()
    t.run()
    
if '__main__' == __name__:
    main()
    
    