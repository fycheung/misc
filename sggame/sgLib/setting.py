#-*-coding:utf-8-*-  
#author:Lizr
#date:2013-6-8
#设置静态类 

class Setting():
    Database = None #自定义数据库  兼容一套装备用于多服
    GatewayPort = None #
    BattlePort = None #
    
    @staticmethod
    def developer(ip):
        '''开发者默认ID'''
        uid = 0
        from sgLib.core import Gcore
        if Gcore.TEST:
            if ip == '10.1.1.31': #李志荣
                uid = 1001
            elif ip == '10.1.1.151': #
                uid = 1002
            elif ip == '10.1.1.111': #张光辉
                uid = 1003 
            elif ip == '10.1.1.149': #叶威
                uid = 0 #1012
            elif ip == '10.1.1.34': #周井江
                uid = 1006 
            '''
            elif ip == '10.1.1.22': #黄国剑
                uid = 1004
            elif ip == '10.1.1.124xxx': #吴明添
                uid = 1005
            elif ip == '10.1.1.200' or ip == '10.1.1.238': #王永乾
                uid = 1006
            elif ip == '10.1.1.199' or ip == '10.1.1.119': #李忆凡
                uid = 1008
            elif ip == '10.1.1.169': #骆泉 ipad
                uid = 1009
            elif ip == '10.1.1.221': #李忆凡 ipad
                uid = 1010
            elif ip == '10.1.1.142': #黄国剑他弟
                uid = 1011 
            '''
        return uid #用户ID
    
    @staticmethod
    def setDatabase(database):
        Setting.Database = database
    
    @staticmethod
    def getDatabase():
        return Setting.Database
    #----------------------------
    @staticmethod
    def setGatewayPort(port):
        Setting.GatewayPort = port

    @staticmethod
    def getGatewayPort():
        return Setting.GatewayPort
    
    #-----------------------------
    @staticmethod
    def setBattlePort(port):
        Setting.BattlePort = port

    @staticmethod
    def getBattlePort():
        return Setting.BattlePort
    
    