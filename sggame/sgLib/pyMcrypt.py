# -*- coding:utf-8 -*-
# author:Lizr
# date:2013-3-28
# 可逆加密

DATA_MIN_LEN = 4  #需要加密数据的最小长度

import base64
import json
import hashlib
import zlib

#from sgCfg.config import SECRET_KEY
from sgCfg.config import SECRET_DATA_KEY


class TokenDecode:
    """解密总服发给客户端，客户端发给分服的信息"""

    def getTokenMsg(self,tokenStr=''):
        '''检查Token是否有效
        @param tokenStr: 客户端在总服登录成功的加密串
        @return: dict or False
        '''
        from sgLib.core import Gcore
        SECRET_KEY = Gcore.loadCoreCfg('Encryption')
        
        timeOut = 180 #密码有效时间
        try:
            #tokenStr='JV4vUlQXUyNsPQ5GCExEWENQISwvSQxNDkNOAEUKAh4GCWseUA5FD3YwAlUdVBt0OjtBQldPR01FNhpaAk0VejQ1T15TWz16Pj9FVVhQNn82fnUxaWFxdWkoWUlfRl4dVUE1cTIsY31gegtLDEIKHAQXbnk6Jm16cn0fcjx1NEYFS25tdm10ZHljGg8eDRRP'
            tokenStr = base64.b64decode(tokenStr) #base64从decode encode中抽离
            tokenStr = decode(tokenStr,SECRET_KEY)
            #print 'tokenStr',tokenStr
            tokenDic = json.loads(tokenStr)
            #print 'tokenDic',tokenDic
            
            #PHPcode: $s_LockKey = md5( substr( md5($i_LockTime.$Encryptionkey), 1, 18 ).$Encryptionkey );
            #tokenDic: {u'TotalServiceId': u'42', u'LoginMode': 2, u'PlayerId': 0, u'LoginVersion': 101, u'Lan': 1, u'LockTime': 1367994093, u'LockKey': u'6b11732eb74eb4e8791afdb02096b6a1'}
            LockTime = str(tokenDic['LockTime'])
            mt=hashlib.md5()
            mt.update(LockTime)
            mt.update(SECRET_KEY)
            OutKey=mt.hexdigest()
            mt=hashlib.md5()
            mt.update(OutKey[1:19]) #substr(1,18)
            mt.update(SECRET_KEY)
            OutKey=mt.hexdigest()
#            print 'OutKey',OutKey
#            print 'LockKey',tokenDic['LockKey']
            #if (int(time.time())-int(LockTime))>timeOut: #分服登录-过期后重启去总服登录#@todo
            #    return False
            
            if OutKey==tokenDic['LockKey']:
                tokenDic.pop('LockKey')
                return tokenDic
            else:
                return False
        except:
            return False
        
        print tokenDic
    
    def makeLockKey(self):
        '''组成服务器通讯加密串'''
        
        from sgLib.core import Gcore
        SECRET_KEY = Gcore.loadCoreCfg('Encryption')
        
        import time
        LockTime = int(time.time())
        LockTime = str(LockTime)
        mt=hashlib.md5()
        mt.update(LockTime)
        mt.update(SECRET_KEY)
        OutKey=mt.hexdigest()
        mt=hashlib.md5()
        mt.update(OutKey) #substr(1,18)
        mt.update(SECRET_KEY)
        OutKey=mt.hexdigest()
            
        d =  {}
        d['TokenLockTime'] = LockTime
        d['Tokenkey'] = OutKey
        return d
        #PHPcode: $s_ThisToken = md5( md5( $i_LockTime.$Encryptionkey ). $Encryptionkey  );
        
    
def encode(data, key=SECRET_DATA_KEY, iszip=False):
    '''
    #给数据加密
    @param data:  原始数据
    @param key:   加密的key，长度为8的字符串
    @param zip:   是否压缩
    '''
    if len(data) < DATA_MIN_LEN:
            return data
    else:
            return _encode(data, key, iszip)

def decode(data, key=SECRET_DATA_KEY, iszip=False):
    '''
    #给数据解密
    @param data:  加密后的数据
    @param key:   解密的key，长度为8的字符串
    '''
    if len(data) < DATA_MIN_LEN:
            return data
    else:
            return _decode(data, key, iszip)

def _encode(data, key, iszip):
    '''
    #给数据加密
    @param data:  原始数据
    @param key:   加密的key，长度为8的字符串
    '''
    if iszip:
        data = zlib.compress(data)
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
    return mcrypt
    #return base64.b64encode(mcrypt)

def _decode(data, key, iszip):
    '''
    #给数据解密
    @param data:  加密后的数据
    @param key:   解密的key，长度为8的字符串
    '''
    #data = base64.b64decode(data)
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
    #print 'de_data',de_data
    data = "".join(map(chr, de_data))
    if iszip:
        return zlib.decompress(data)
    else:
        return data

def getVK(VT):
    '''战斗同步加密方法  VT时间戳'''
    mt=hashlib.md5()
    mt.update(base64.b64encode(str(VT)))
    VK = mt.hexdigest()
    #print 'VK',VK
    VK = VK[5:10]
    #print 'VK',VK
    return VK

def checkVK(VT,VK):
    #print VK,getVK(VT)
    return VK == getVK(VT)

def checkListenKey(VK):
    from sgLib.core import Gcore
    SECRET_KEY = Gcore.loadCoreCfg('Encryption')
    
    mt=hashlib.md5()
    mt.update(SECRET_KEY)
    t = mt.hexdigest()
    
    mt=hashlib.md5()
    mt.update(t)
    t = mt.hexdigest()
    if VK!=t:
        print VK,t
    return VK == t

    
if __name__ == '__main__':
    '''调试'''
#    s = encode('hello',iszip=True)
#    print s
#    print decode(s,iszip=True)
    from sgLib.core import Gcore
    for i in xrange(100000):
        #getVK(1363830329)
        checkVK('1363830329', 'ac030')
    Gcore.runtime()
