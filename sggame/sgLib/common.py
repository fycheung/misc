#-*- coding:utf-8 -*-
#   note:公共类库和方法
#   date:2012年5月15日
#   version:v1.0

import chardet
import time
import random
import json
import struct
import math
#import ForbiddenTrees
#-------------------------------------------- 类 ------------------------------------------------
#-------------------------------------------- 函数 -----------------------------------------------
def json_encode(ParamDict):
    return json.dumps(ParamDict)

def json_decode(ParamStr):
    return json.loads(ParamStr)

def trace( msg ):
    """调试打印输出"""
    msg=msg.decode("utf-8")
    print " >>> TRACE["+time.strftime("%Y-%m-%d %H:%M:%S")+" ("+str(time.time())+")]  "+msg+""

    
def decodePacket(data):
    """解包"""
    try:
        jsTmp = json.loads(data)
        #print 'jsTmp',jsTmp
        if not isinstance(jsTmp, dict):
            raise Exception("loads json fail")
        optId=int(jsTmp['opt_id']) #保证协议号为整形
        optKey=jsTmp['opt_key']
        if 'para' not in jsTmp or type(jsTmp.get('para')) is not dict:
            para = {}
        else:
            para=jsTmp['para']
        if 'stime' in jsTmp:
            para['ClientTime'] = jsTmp['stime']
        else:
            para['ClientTime'] = int(time.time())
        return (optId,optKey,para)
    except Exception,e:
        print 'DecodePacket Error!> ',e,data
        return False


def datetime(curtime=None):
    '''获取当前日期时间  返回str'''
    if not curtime:
        curtime = time.time()
    return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(curtime))

def now(curtime=None):
    '''更便捷方法,代替datetime()'''
    return datetime(curtime)

def nowtime():
    '''获取时间戳，整型'''
    return int(time.time())

def today(curtime=None):
    '''获取当前日期 返回str'''
    if not curtime:
        curtime = time.time()
    return time.strftime('%Y-%m-%d',time.localtime(curtime))

def today0time():
    '''获取当天0点的时间戳 Lizr'''
    t = time.localtime(time.time())
    time0 = time.mktime(time.strptime(time.strftime('%Y-%m-%d 00:00:00', t),'%Y-%m-%d %H:%M:%S'))
    return int(time0)

def str2unicode(s):
    '''将字符串s解码成unicode。不是字符串返回None，无法判断编码返回原字符串，否则返回unicode字符串。'''
    #author : zhoujingjiang
    if isinstance(s, unicode):
        return s
    if isinstance(s, str):
        code = chardet.detect(s)['encoding']
        try:
            return unicode(s, code)
        except Exception:
            return s

def filterInput( s_Content, i_Min = 2, i_Max = 8, b_Replace = False ,b_chat = False, arr_legal = [] ):
    '''检测用户输入字符串是否满足要求，长度，特殊字符，敏感字符'''
    s_Content = str2unicode(s_Content.strip()) #fixed by zhoujingjiang
    i_Length = ( len(s_Content)+len(s_Content.encode('u8')) )/2
    if i_Length < i_Min or i_Length  > i_Max:
        return -1
    
    if b_chat:
        #arr_FWord = ['\'','\r','<','>','&nbsp;','&lt;','\\n','\\r','\n']
        arr_FWord = [] #聊天不屏蔽特殊字符 by 曾
    else:
        arr_FWord = ['\'', '"','\r','<','>','|',',','\\','\/','/','`','^','&nbsp;','&','\\n','\\r','\n','%',
                     '☺','☎','♠','♣','♥','♦','♨','↘','↙','▪','▫','❤','✌','☝','☀','☁','✂','➡','↗',
                     '↖','↘','↙','◀','▶','✴','✳','♈','♉','♋','♌','♍','♎','♏','♐','♑','♒','♓',  
                     ]
    for s_FWord in arr_FWord:
        if arr_legal and s_FWord in arr_legal:
            continue
        if s_FWord in s_Content:
            return -2
    #@todo 过滤敏感字符  很黄很暴力 ...
    s_Content = s_Content.decode('utf8')
    
    return filterForbidden(s_Content,b_Replace)

def filterForbidden(string,b_Replace,replaceStr = '*'):
    tree = WORDTREE
    temp=tree
    result = ''
    for s in string:
        index = ord(s)
        temp = temp[0].get(index)

        if temp == None:
            result = s
            temp = tree[0].get(ord(s), [{}, 0])
        else:
            result += unichr(index)

        if temp[1] == 1:
            print '含有敏感词', result
            if b_Replace:
                string = string.replace(result, replaceStr)
            else:
                return -3
    return string


def createWordTree():
    '''生成屏蔽字符树,改变屏蔽字库的时候生成一次'''
    print 'ps createWordTree()'
    from sgCfg.config import SYSTEM_ROOT
    FilePath = SYSTEM_ROOT+'/sgLib/ForbiddenWords'
    def loadDataFrmFile(filePath=FilePath, sep='\n'):
        try:
            with open(filePath, 'rb') as fd:
                return fd.read().decode('utf8').split(sep)
        except Exception:
            with open('/trunk/sgLib/ForbiddenWords', 'rb') as fd:
                return fd.read().decode('utf8').split(sep)          
    wordsList = loadDataFrmFile()
    wordTree = [{}, 0]
    for word in wordsList:
        tree = wordTree[0]
        for i  in range(0,len(word)):
            index = ord(word[i])

            if i ==  len(word) - 1: #最后一个字母
                tree[index] = [{}, 1]
            else:
                tree.setdefault(index, [{}, 0])
                tree = tree[index][0]
    import sys
    #print 'size', sys.getsizeof(wordTree)
    return wordTree

#    f=open('/data1/sg_game/trunk/sgLib/ForbiddenTrees.py','w')
#    f.write('wordTree = '+str(wordTree)+'\n')
#    f.close()


def Choice(nodes, count=1, Ratio='Ratio'):
    '''根据概率份额选择节点 (节点为字典)
    @author: zhoujj
    @param nodes:由node组成的序列，node -dict：Ratio份额
    @param count:要选出的节点数目。
    @param Ratio:概率份额的键名
    @return : 1个节点 或多个节点的列表 
    '''
    iter(nodes)
    assert isinstance(count, (int, long)) and count > 0 and len(nodes) >= count

    RetLst = []
    totalRatio = sum([int(node[Ratio]) for node in nodes])
    while len(RetLst) < count:
        RandomInt = random.randrange(1, totalRatio + 1, 1)
        for node in nodes:
            RandomInt -= node[Ratio]
            if RandomInt <= 0 and node not in RetLst:
                RetLst.append(node)
                break
    return RetLst.pop(0) if count == 1 else RetLst

def gen01Dict(chance,skillId):
    '''获取概率的字典
    @author: Lizr
    @param chance: 出现技能ID的概率  可以是小数或整数  0.2=20=20%概率
    @param skillId: 技能ID 
    @return: {1:24,2:0,3:0,4:24....}
    '''
    import random
    if chance<1:
        chance*=100
    lis01 = []
    for i in xrange(100):
        if i<=chance:
            lis01.append(skillId)
        else:
            lis01.append(0)
    random.shuffle(lis01)
    dict01 = dict(zip(xrange(1, len(lis01) + 1, 1),lis01))
    dict1 = {}
    for k,v in dict01.iteritems():
        if v:
            dict1[k] = v
    return dict1

def list2dict(lst,offset=1):
    '''将列表转换成字典：key为元素的位置
    @param offset: 第一个元素序号
    @example list2dict(['a','b','c']) >> {1: 'a', 2: 'b', 3: 'c'}
    '''
    assert isinstance(lst, (list, tuple)), '参数是列表或元组'
    return dict(zip(xrange(offset, len(lst) + offset, 1),lst))
    #另一方法: dict(enumerate(lst, start=1)) 

def getWeekSort(SoldierSort):
    '''获取对应的克制类型 
    :弓克步 步克骑 骑克弓
    ''' 
    if SoldierSort==1: #步
        return 3
    elif SoldierSort==2: #弓
        return 1
    elif SoldierSort==3: #骑
        return 2
    else:
        return 0

def calSpeedCost(SType,STime):
    '''
    :计算加速费用
    @param SType:加速类型加速类型: 1建造（升级）加速   2 科技学习加速   3  士兵训练加速  4 武将训练加速  5 器械制造（工坊）
    @param STime:加速时间/秒
    @return: 所需费用
    '''
    from sgLib.core import Gcore
    cfg = Gcore.getCfg('tb_cfg_speed',SType)
    cost = cfg['k1']*(STime**cfg['k2']-STime**cfg['k3'])+cfg['k4']
    return int(math.ceil(cost))

WORDTREE = createWordTree()
#print 'WORDTREE',WORDTREE
    
if __name__ == '__main__':
    '''调试'''
    from sgLib.core import Gcore
    print calSpeedCost(1, 5200)
