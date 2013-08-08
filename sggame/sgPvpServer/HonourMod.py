#coding:utf8
#author:zhoujingjiang
#date:2013-5-16
#竞技场荣誉模型

import datetime
import time

import MySQLMod as db

_honour_table = 'tb_pvp_honour' #竞技场荣誉表

def getWeekHonour(userid, serverid, timestamp=None):
    '''获取本周所得的荣誉'''
    timestamp = timestamp if timestamp else time.time()
    fields = '*'
    where = 'UserId=%s AND ServerId=%s' % (userid, serverid)
    record = db.out_fields(_honour_table, fields, where)
    if record is None:
        #没有该用户的记录，插入。
        initdata = {'UserId':userid, "ServerId":serverid, 'HonourNum':0,
               "LastChangeDate":datetime.date.fromtimestamp(timestamp)}
        db.insert(_honour_table, initdata)
        return 0
    lastchangedate, honornum = record['LastChangeDate'], record['HonourNum']
    monday = getMondayDate(timestamp)
    
    if lastchangedate >= monday:
        return honornum
    return 0

def getMondayDate(t):
    '''获取给定日期所在周的周一，返回datetime.date类型'''
    if isinstance(t, (datetime.date, datetime.datetime)):
        pass
    elif isinstance(t, basestring): #日期串:'%Y-%m-%d
        t = datetime.datetime.strptime(t, '%Y-%m-%d')
    elif isinstance(t, (int, float, long)): #时间戳
        t = datetime.datetime.fromtimestamp(t)
    else:
        raise TypeError, '参数应该是时间戳，日期串或日期类型'
    
    monday = t - datetime.timedelta(t.weekday())
    if isinstance(monday, datetime.datetime):
        return monday.date()
    return monday

def addHonour(userid, serverid, addnum, timestamp=None):
    '''增加荣誉'''
    if addnum <= 0:
        return #增加的荣誉值小于等于0，直接返回。
    timestamp = timestamp if timestamp else time.time()
    honournum = getWeekHonour(userid, serverid, timestamp)
    honournum += addnum
    honournum = 2000 if honournum > 2000 else honournum #每周所能获得的荣誉上限是2000
    newdata = {"LastChangeDate":datetime.date.fromtimestamp(timestamp),
               "HonourNum":honournum}
    where = 'UserId=%s AND ServerId=%s' % (userid, serverid)
    stat = db.update(_honour_table, newdata, where)
    if not stat:
        return stat
    return honournum #返回增加后的荣誉值