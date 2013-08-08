#!/usr/bin/env python
# -*- coding:utf-8 -*-
# author: qiudx
# date: 2013/07/30
# 更新建筑费用为Null的数据

import json
from sgLib.core import Gcore


class UpdateRobot(object):
    '''用于查找和更新建筑费用为NULL的类'''
    
    def __init__(self):
        self.db = Gcore.getNewDB()
        self.fd = None  #将修改过的数据写入文件，备份,防止出错
        
    def checkAndUpdate(self, table):
        '''查找并更新数据库中建筑费用为NULL的数据'''
        fields = ['BuildingId', 'UserId', 'BuildingType', 'BuildingLevel', 'CoinType', 'BuildingPrice', 'LastChangedTime', 'CompleteTime']
        where = ' CoinType is NULL or BuildingPrice is NULL or LastChangedTime is NULL OR CoinType = 0 OR BuildingPrice = 0 '
        tmpRows = self.db.out_rows(table, fields, where)
        if tmpRows:
            for row in tmpRows:
                #print '==PrimaryData:',row
                tmpData = json.dumps(row) + '\n'
                self.fd.write(tmpData)
                if not row['CoinType']:
                    row['CoinType'] = Gcore.getCfg('tb_cfg_building', row['BuildingType'], 'CoinType')
                if not row['BuildingPrice']:
                    row['BuildingPrice'] = Gcore.getCfg('tb_cfg_building_up', (row['BuildingType'], row['BuildingLevel']), 'CostValue')
                if not row['LastChangedTime'] and row['LastChangedTime'] != 0:
                    if row['CompleteTime']:
                        row['LastChangedTime'] = row['CompleteTime'] - Gcore.getCfg('tb_cfg_building_up', (row['BuildingType'], row['BuildingLevel']), 'CDValue')
                    else:
                        row['LastChangedTime'] = 0
                    if row['LastChangedTime'] < 0:
                        row['LastChangedTime'] = 0
                where = 'BuildingId=%s'%row['BuildingId']
                data = {'CoinType': row['CoinType'], 'BuildingPrice': row['BuildingPrice'], 'LastChangedTime': row['LastChangedTime']}
                self.db.update(table, data, where)
                #print '==ModifiedData:',data
                tmpData = json.dumps(data) + '\n'
                self.fd.write(tmpData)
                
    def run(self):
        self.fd = open('building_data_bk.txt', 'w')
        tb_num = Gcore.config.TBNUM
        for i in xrange(tb_num):
            tb_name = 'tb_building%s'%i
            self.checkAndUpdate(tb_name)
        self.fd.close()
        
        
def main():
    robot = UpdateRobot()
    print 'Run UpdateRobot...'
    robot.run()
    print 'Over!'

if '__main__'==__name__:
    main()
        