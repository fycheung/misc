#coding:utf8
#author:zhoujingjiang
#date:2013-5-15
#读取竞技场相关配置

import MySQLMod as db
import common

class CfgReader(common.Singleton):
    '''读取竞技场相关配置'''
    #竞技场相关的配置表
    tables = ['tb_cfg_soldier', 'tb_cfg_pvp_pos',
              'tb_cfg_general', 'tb_cfg_soldier_up',
              'tb_cfg_skill', 'tb_cfg_honour']
    cfgs = {} #保存配置
    
    def load_cfg(self):
        '''将配置读入字典'''
        for table in self.__class__.tables:
            self.__class__.cfgs[table] = {}
            
            results = db.query('DESC %s' % table)
            if not results:
                continue
            pris = [result['Field'] for result in results if result['Key'] == 'PRI']

            results = db.out_rows(table)
            if not results: #读表失败
                continue
            for result in results:
                row_key = tuple([result[pri] for pri in pris])
                if len(row_key) == 1:
                    row_key = row_key[0]
                self.__class__.cfgs[table][row_key] = result
    
    def get_cfg(self, table, key=None, field=None):
        '''读取配置'''
        if key is None: #读取整个配置表
            return self.__class__.cfgs.get(table)
        if field is None: #读取整行
            return self.__class__.cfgs.get(table, {}).get(key)
        return self.__class__.cfgs.get(table, {}).get(key, {}).get(field) #读取一列
#end class CfgReader

cr = CfgReader() #单例
cr.load_cfg() #模块第一次被导入时，加载配置进内存。