#coding:utf8
#author:zhoujingjiang
#date:2013-5-22
#发送邮件

import smtplib
from email.mime.text import MIMEText   
from email.mime.multipart import MIMEMultipart

import config

class MailSender(object):
    '''发送邮件'''
    def __init__(self, host, port=25, user='', passwd=''):
        '''构造函数'''
        self.smtp = smtplib.SMTP() #smtp对象
        self.islogin = False #是否已登陆
        
        self.host = host #smtp主机
        self.port = int(port) #smtp端口
        self.user = user #帐号
        self.passwd = passwd #密码
        
        #登陆：登陆失败也不抛出异常
        self.islogin = self.login()

    def login(self):
        '''连接并登陆'''
        try: #尝试连接并登陆
            self.smtp.connect(host=self.host, port=self.port)
            self.smtp.login(self.user, self.passwd)
        except Exception: #登录失败
            return False
        else: #登陆成功
            return True
    
    def sendmail(self, frm_addr, to_addrs, subject='', body=''):
        '''发送'''
        #邮件消息
        msg = MIMEMultipart()   
        msg['From'] = frm_addr #发件人
        msg['To'] = to_addrs #收件人
        msg['Subject'] = subject #主题
        if body: #邮件内容
            msg.attach(MIMEText(str(body)))

        try:
            status = self.smtp.sendmail(frm_addr, to_addrs, msg.as_string()) 
        except Exception: #发送失败
            self.login() #重连
            if not self.islogin: #登陆没成功
                return False
            status = self.smtp.sendmail(frm_addr, to_addrs, msg.as_string()) #再发送
        return status # 返回发送状态：如果所有的收件人都收到了返回空字典
                        # + 否则返回errorcode等信息

    def __del__(self):
        '''析构函数'''
        self.smtp.quit()
#end class MailSender

ms = MailSender(host=config.SMTP_HOST,
                port=config.SMTP_PORT,
                user=config.SMTP_USER,
                passwd=config.SMTP_PASSWD)

sendmail = lambda subject, body='': ms.sendmail(config.SMTP_USER, 
                                                config.SMTP_RECEIVER, 
                                                subject, body)
