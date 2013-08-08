#coding:utf8
#author:zhoujingjiang
#date:2013-1-3
#游戏内部接口：建筑通用

import time

from sgLib.core import Gcore
from sgLib.base import Base

class BuildingMod(Base):
    ''' 建筑模型'''
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid

    def createBuilding(self, p): #返回BuildingId
        data = {}
        data['LastOptType'] = 0
        data['BuildingType'] = p['BuildingType']
        data['BuildingLevel'] = 1
        data['UserId'] = self.uid
        data['CoinType'] = p['CoinType']
        data['BuildingPrice'] = p['CostValue']
        data['x'] = p['x']
        data['y'] = p['y']
        data['xSize'] = p['xSize']
        data['ySize'] = p['ySize']
        data['LastChangedTime'] = p['LastChangedTime']
        data['CompleteTime'] = p['LastChangedTime'] + p['CDValue']
        return self.db.insert(self.tb_building(), data)
    
    def getWorkerNum(self):
        '''获取总工匠数量'''
        return self.db.out_field('tb_user',
                                 'WorkerNumber',
                                 "UserId='%s'" % self.uid)
        
    def sizeExplode(self,size):
        '''展开size字符串'''
        xSize,ySize = size.split('*')
        return int(xSize), int(ySize)

    def getBuildingByCoord(self,x,y):
        '''根据坐标获取建筑ID'''
        BuildingId = self.db.out_field(self.tb_building(), 
                    'BuildingId', 
                    "UserId=%s AND x=%s AND y=%s"%(self.uid, x, y))
        return BuildingId if BuildingId else 0

    def updateBuildingById(self, UpInfo, BuildingId):
        '''根据BuildingId更新建筑'''
        where = 'UserId=%s AND BuildingId=%s' % (self.uid, BuildingId)
        return self.db.update(self.tb_building(), UpInfo, where)
    
    def deleteBuildingById(self, BuildingId):
        '''根据BuildingId删除建筑'''
        return self.db.execute('''DELETE FROM %s 
            WHERE UserId=%s AND BuildingId=%s''' % (
                            self.tb_building(), self.uid, 
                            BuildingId))
        
    def getBuildingById(self, BuildingIds=None, fields='*', TimeStamp=None):
        '''获取建筑等级和状态接口
        @para: BuildingIds - None or 建筑ID or 建筑ID序列
        @para: fields - 字符串或列表
        @para: TimeStamp - 时间戳
        @return: 元组或字典
            BuildingRealLevel - 建筑真正等级   
            BuildingState - 建筑状态：0空闲 ，1建造中 ，2升级中
        '''
        TimeStamp = TimeStamp if TimeStamp else time.time()
        if not isinstance(fields, (list, tuple)):
            fields = [fields]

        where = 'UserId = %s' % self.uid
        if isinstance(BuildingIds, (list, tuple)):
            where += ' AND ( BuildingId=' + ' OR BuildingId='.join(map(str, BuildingIds))+' )'
        elif BuildingIds:
            where += ' AND BuildingId=%s' % BuildingIds
        else : pass
    
        table = self.tb_building()
        sql = " SELECT " + ",".join(fields) + """ , IF(CompleteTime<=%s, BuildingLevel, 
        BuildingLevel-1) AS BuildingRealLevel, IF(CompleteTime>%s, IF(BuildingLevel=1, 1, 2), 
        0) AS BuildingState FROM %s WHERE %s"""%(TimeStamp, TimeStamp, table, where)
        
        if isinstance(BuildingIds, (list, tuple)) or BuildingIds is None:
            return self.db.fetchall(sql)
        return self.db.fetchone(sql)

    def getBuildingByType(self, BuildingTypes, fields='*', TimeStamp=None):
        '''获取建筑等级和状态接口
        @para: BuildingTypes - 建筑类型或建筑类型序列
        @para: fields - 字符或列名列表
        @return:元组
            BuildingRealLevel - 建筑真正等级   
            BuildingState - 建筑状态：0空闲 1建造中 2升级中
        '''
        TimeStamp = TimeStamp if TimeStamp else time.time()
        if not isinstance(fields, (list, tuple)):
            fields = [fields]
        
        if isinstance(BuildingTypes, (list, tuple)):
            where = 'UserId=%s'%self.uid + ' AND ( BuildingType= ' + \
                    ' OR BuildingType= '.join(map(str, BuildingTypes))+' ) '
        else:
            where = 'UserId=%s AND BuildingType=%s' % (self.uid, BuildingTypes)
        
        table = self.tb_building()
        sql = " SELECT " + ",".join(fields) + """ , IF(CompleteTime <= %s, BuildingLevel, 
            BuildingLevel - 1) AS BuildingRealLevel, IF(CompleteTime > %s, 
            IF(BuildingLevel = 1, 1, 2), 0) AS BuildingState 
            FROM %s WHERE %s"""%(TimeStamp, TimeStamp, table, where)
        return self.db.fetchall(sql)

    # 下面的不知道是谁在用
    def getBuildingIdByType(self,Type):
        '''通过类型获得建筑ID，只能用于只可存在一座同类型的建筑 如理藩院
        @author: Lizr
        '''
        try:
            BuildingId = self.getBuildingByType(Type,'BuildingId')[0].get('BuildingId')
        except:
            BuildingId = 0
            
        return BuildingId
 
    def getHomeLevel(self):
        '''获取我的将军府等级'''
        tb_building = self.tb_building()
        now = time.time()
        where = "UserId=%s AND BuildingType=1"%self.uid
        sql = "SELECT IF(CompleteTime<=%s,BuildingLevel,BuildingLevel-1) as BuildingRealLevel FROM %s WHERE %s"%(now,tb_building,where)
        row = self.db.fetchone(sql)
        return row['BuildingRealLevel']
      
    def getBuildingByWhere(self,where,fields='*',TimeStamp=None):
        '''获取建筑相关内容通用接口
        @para:where 查询条件 字符串 别忘了加是查自己的
        @para:fields 字段 (字符或列表)
        '''
        tb_building = self.tb_building()
        if not isinstance(fields, (list, tuple)):
            fields = [fields]
        now = time.time() if TimeStamp is None else TimeStamp
        sql = "SELECT "+str.join(",",fields)+",IF(CompleteTime<=%s,BuildingLevel,BuildingLevel-1) as BuildingRealLevel,\
        IF(CompleteTime>=%s,IF(BuildingLevel=1,1,2),0) AS BuildingState FROM %s WHERE %s"%(now,now,tb_building,where)
        return self.db.query(sql)

    #弃用
    def getFreeWorkerNum(self, TimeStamp = None):
        '''获取空闲工匠数量'''
        TimeStamp = time.time() if TimeStamp is None else TimeStamp
        where = "Speed=%s AND UserId=%s AND StopTime>%s" % (0, self.uid, TimeStamp)
        WorkerBusyNum = self.db.out_field('tb_process_record', 'count(*)', where)
        WorkerNum = self.getWorkerNum()
        return WorkerNum - WorkerBusyNum

    def countBuildingType(self,BuildindType):
        '''统计某类建筑的数量'''
        tb_building = self.tb_building()
        BuildingNum = self.db.out_field(tb_building, 'count(*)', "BuildingType=%s AND UserId=%s"%(BuildindType, self.uid))
        return BuildingNum

    def getAllBuildingCoord(self):
        ''' 获取所有建筑的坐标和尺寸'''
        curStorage = Gcore.getMod('Building_resource',self.uid).getAllStorage()
        rows = self.getBuildingById(None)
        arr = []
        for row in rows:
            BuildingId = row.get('BuildingId')
            r = {}
            r['BuildingId'] = BuildingId
            r['x'] = row.get('x')
            r['y'] = row.get('y')
            r['BuildingType'] = row.get('BuildingType')
            r['BuildingLevel'] = row.get('BuildingRealLevel') #注意要用建筑的真正等级
            r['CompleteTime'] = row.get('CompleteTime')
            r['BuildingState'] = row.get('BuildingState') #0空闲 1建筑中 2升级中 3停产中
            if BuildingId in curStorage:
                arrCollect = curStorage.get(BuildingId)
                r['Storage'] = arrCollect.get('Storage')
                if r['Storage']<0:
                    r['BuildingState'] = 3 #停产中
                r['CalTime'] = arrCollect.get('CalTime')
            else:
                r['Storage'] = 0
                r['CalTime'] = 0 
            arr.append(r)
        return arr
    
    def getResourceOutBuilding(self):
        '''获取资源产出建筑信息  by Lizr'''
        curStorage = Gcore.getMod('Building_resource',self.uid).getAllStorage()
        
        rows = self.getBuildingByType([2,5])
        arr = []
        for row in rows:
            BuildingId = row.get('BuildingId')
            r = {}
            r['BuildingId'] = BuildingId
            if BuildingId in curStorage:
                arrCollect = curStorage.get(BuildingId)
                r['Storage'] = arrCollect.get('Storage')
                r['CalTime'] = arrCollect.get('CalTime')
            else:
                r['Storage'] = 0
                r['CalTime'] = 0 
            arr.append(r)
        return arr
        
        
    def cacStorageSpace(self, CoinType):
        '''计算军资或铜币的最大存储容量'''
        CoinType = int(CoinType)
        buildingCfg = Gcore.loadCfg( Gcore.defined.CFG_BUILDING ) #将军府初始量
        StorageSpace =  buildingCfg['InitJcoin'] if  CoinType == 2 else buildingCfg['InitGcoin']
        
        if CoinType == 2 or CoinType == 3: #军资或铜币
            BuildingType = 3 if CoinType == 2 else 4
            QueryTpl = self.getBuildingByType(BuildingType)
            if not QueryTpl: #用户没有军资库或钱庄
                return StorageSpace
            for building in QueryTpl:
                if building['BuildingState'] == 1:
                    continue
                StorageSpace += Gcore.getCfg('tb_cfg_building_up', 
                                             (BuildingType, building["BuildingRealLevel"]))["SaveValue"]
            return StorageSpace
        return False #资源类型不是军资或铜币
    
    def AvgDistAlgo(self, TotalNum, Nodes, Rel = []):
        '''平均分配算法
        param：-TotalNum -int   -待分配的数量
               -Nodes    -list  -结构 :[{"Num":可分配数量,"Name":节点标识}]
               -Rel      -list  -保存返回结果字典的列表，不要传值。
        return value：        -list  -结构:[{"Num":可分配数量,"Name":节点标识,"DistNum":分配数量}]
        '''
        SpaceLst = [Node["Num"] for Node in Nodes]
        if TotalNum >= sum(SpaceLst): #待分配数量大于所有节点可分配数量的和
            for Node in Nodes:
                Node["DistNum"] = Node["Num"]
            return Nodes
        if TotalNum <= len(SpaceLst)*min(SpaceLst):
            for Node in Nodes:
                Node["DistNum"] = int(TotalNum/len(SpaceLst))
                Rel.append(Node)
            remainder = TotalNum % len(SpaceLst)
            for Node in Rel:
                if remainder == 0:
                    break
                if Node["DistNum"] < Node["Num"]:
                    Node["DistNum"] += 1
                    remainder -= 1
            return Rel
        for Node in Nodes:
            if Node["Num"] <= TotalNum/len(SpaceLst):
                Nodes.remove(Node)
                Node["DistNum"] = Node["Num"]
                TotalNum -= Node["Num"]
                Rel.append(Node)
        return self.AvgDistAlgo(TotalNum, Nodes, Rel)
#end class BuildingMod

def _test():
    '''测试方法'''
    uid = 1003
    c = BuildingMod(uid)
    #print c.getBuildingById()
#     print c.getResourceOutBuilding()
    print c.getBuildingById(BuildingIds=126)

if __name__ == '__main__':
    _test()
    Gcore.runtime()
