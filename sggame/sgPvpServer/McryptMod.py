#coding:utf8
#author:李志荣
#加密，解密模型。

import base64
import json
import hashlib

import config
DATA_MIN_LEN = 4 #需要加密数据的最小长度

def getTokenMsg(tokenStr):
    try:
        tokenStr = decode(tokenStr, config.SECRET_KEY)
        tokenDic = json.loads(tokenStr)
        
        LockTime = str(tokenDic['LockTime'])
        mt=hashlib.md5()
        mt.update(LockTime)
        mt.update(config.SECRET_KEY)
        OutKey=mt.hexdigest()
        mt=hashlib.md5()
        mt.update(OutKey[1:19])
        mt.update(config.SECRET_KEY)
        OutKey=mt.hexdigest()
        
        if OutKey==tokenDic['LockKey']:
            tokenDic.pop('LockKey')
            return tokenDic
        else:
            return False
    except Exception:
        return False

def encode(data, key):
    '''
    #给数据加密
    @param data:原始数据
    @param key:加密的key，长度为8的字符串
    '''
    if len(data) < DATA_MIN_LEN:
        return data
    else:
        return _encode(data, key)

def decode(data, key):
    '''
    #给数据解密
    @param data:加密后的数据
    @param key:解密的key，长度为8的字符串
    '''
    if len(data) < DATA_MIN_LEN:
        return data
    else:
        return _decode(data, key)

def _encode(data, key):
    '''
    #给数据加密
    @param data:原始数据
    @param key:加密的key，长度为8的字符串
    '''
    en_data = map(ord, data)
    key = map(ord, key)
    en_data[0] = en_data[0] ^ key[0]
    count = len(data)
    for i in xrange(1, count):    
        en_data[i] = en_data[i] ^ en_data[i-1] ^ key[i&7]
    en_data[3] = en_data[3]^key[2];
    en_data[2] = en_data[2]^en_data[3]^key[3]
    en_data[1] = en_data[1]^en_data[2]^key[4]
    en_data[0] = en_data[0]^en_data[1]^key[5]
    
    mcrypt = "".join(map(chr, en_data))
    return base64.b64encode(mcrypt)

def _decode(data, key):
    '''
    #给数据解密
    @param data:加密后的数据
    @param key:解密的key，长度为8的字符串
    '''
    data = base64.b64decode(data)
    de_data = map(ord, data)
    key = map(ord, key)
    de_data[0] = de_data[0]^de_data[1]^key[5]
    de_data[1] = de_data[1]^de_data[2]^key[4]
    de_data[2] = de_data[2]^de_data[3]^key[3]
    de_data[3] = de_data[3]^key[2]
    count = len(data) - 1
    for i in xrange(count, 0, -1):
        de_data[i] =  de_data[i] ^ de_data[i-1] ^ key[i&7]
    de_data[0] = de_data[0] ^ key[0]
    return "".join(map(chr, de_data))