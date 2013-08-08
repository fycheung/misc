#coding:utf8
#author:zhoujingjiang
#date:2013-05-09
#公用类库

import json
import gzip
from cStringIO import StringIO
import time

import bson
import chardet
import gevent

def Asynch(func): #作为装饰器使用：对函数，再开一个协程，返回Greenlet
    '''异步执行函数'''
    def wrapFunc(*args, **kwargs):
        return gevent.spawn(func, *args, **kwargs)
    return wrapFunc

class Singleton(object): #继承这个类的类只有一个实例
    '''单例模式'''
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance

def str2unicode(s):
    '''将字符串s解码成unicode。不是字符串返回None，无法判断编码返回原字符串，否则返回unicode字符串。'''
    if isinstance(s, unicode):
        return s
    if isinstance(s, str):
        code = chardet.detect(s)['encoding']
        try:
            return unicode(s, code)
        except Exception:
            return s

def error(optId, message, body={}):
    '''错误返回格式'''
    data = {}
    data['flag'] = 2
    data['opt_id'] = optId
    data['retime'] = int(time.time())
    data['message'] = {message:''}
    if body:
        data['body'] = body
    return data

def out(optId, body={}):
    '''正确返回格式'''
    data = {}
    data['flag'] = 1
    data['opt_id'] = optId
    data['retime'] = int(time.time())
    if body:
        data['body'] = body
    return data

def decodePacket(packet):
    """解包"""
    try:
        recv_data = json.loads(packet)
        assert isinstance(recv_data, dict), '应该是字典'

        optId = int(recv_data['opt_id'])
        optKey = recv_data['opt_key']
        
        if not isinstance(recv_data.get('para'), dict):
            para = {}
        else:
            para = recv_data['para']

        if 'stime' in recv_data:
            #此处校验客户端与服务器时间
            # + todo
            para['ClientTime'] = int(recv_data['stime'])
        else:
            para['ClientTime'] = int(time.time())

        return optId, optKey, para
    except Exception, e:
        print 'decodePacket 异常!无法解压数据 > ', e, packet 
        return False
    
def decodePacket_bson(packet):
    """解包"""
    try:
        packet = StringIO(packet)
        fp = gzip.GzipFile(mode='rb', fileobj=packet)
        packet = fp.read()
        fp.close()
        recv_data = bson.loads(packet)
        
        assert isinstance(recv_data, dict), 'recv_data should be a dict'

        optId = int(recv_data['opt_id'])
        optKey = recv_data['opt_key']
        
        if not isinstance(recv_data.get('para'), dict):
            para = {}
        else:
            para = recv_data['para']

        if 'stime' in recv_data:
            #此处校验客户端与服务器时间
            # + todo
            para['ClientTime'] = int(recv_data['stime'])
        else:
            para['ClientTime'] = int(time.time())

        return optId, optKey, para
    except Exception, e:
        print 'decodePacket 异常!无法解压数据 > ', e, packet 
        return False

def encodePacket(packet):
    """封包"""
    try:
        return json.dumps(packet)
    except Exception, e:
        print 'encodePacket 异常!无法解压数据 > ', e, packet
        return False

def encodePacket_bson(packet):
    """封包"""
    try:
        packet = bson.dumps(packet)
        buf = StringIO()
        fp = gzip.GzipFile(mode='wb', fileobj=buf)
        fp.write(packet)
        fp.close()
        packet = buf.getvalue()
        return packet
    except Exception, e:
        print 'encodePacket 异常!无法序列化数据 > ', e, packet
        return False
