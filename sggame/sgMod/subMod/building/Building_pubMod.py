#coding:utf8
#author:zhoujingjiang
#date:2013-1-3
#游戏内部接口:招贤馆

import random
import datetime

from sgLib.core import Gcore
from sgLib.base import Base

class Building_pubMod(Base):
    '''招贤馆模型'''
    def __init__(self, uid):
        Base.__init__(self, uid)
        self.uid = uid
    
    def getInvite(self):
        '''获取招募记录'''
        return self.db.out_fields('tb_general_invite', '*', 'UserId=%s' % self.uid)
    
    def cacSpeedCount(self, SpeedCount, LastSpeedDate, TimeStamp):
        '''计算加速次数'''
        return SpeedCount if datetime.date.fromtimestamp(TimeStamp) == LastSpeedDate else 0
        
    def chooseGenerals(self, GeneralNum=3, IsFirst=False):
        '''随机选择GeneralNum个武将'''
        GeneralCfg = Gcore.getCfg('tb_cfg_general')

        if IsFirst:
            Nodes = [{'Id':k, 'Ratio':v['ChanceRatio']} for k, v in GeneralCfg.iteritems()
                     if v['ChanceRatio'] > 0 and v['GeneralSort'] == 0]
        else:
            Nodes = [{'Id':k, 'Ratio':v['ChanceRatio']} for k, v in GeneralCfg.iteritems()
                     if v['ChanceRatio'] > 0]
        return [ChosenNode['Id'] for ChosenNode in Gcore.common.Choice(Nodes, GeneralNum)]
    
    def updateInvite(self, ChosenGenerals, BuildingLevel, RefreshTimeStamp, SpeedCount = 0):
        '''更新招募记录'''        
        RefreshValue = Gcore.getCfg('tb_cfg_building_up', key = (13, BuildingLevel), field = 'RefreshValue')
        setClause = {
                     "StartTime":RefreshTimeStamp,
                     "EndTime":RefreshTimeStamp + RefreshValue,
                     "GeneralId1":ChosenGenerals[0],
                     "GeneralId2":ChosenGenerals[1],
                     "GeneralId3":ChosenGenerals[2],
                    }
        if SpeedCount:
            setClause['SpeedCount'] = SpeedCount
            setClause['LastSpeedDate'] = datetime.date.fromtimestamp(RefreshTimeStamp)
        return self.db.update('tb_general_invite', setClause, 'UserId=%s' % self.uid)
        
    def insertInvite(self, ChosenGenerals, BuildingLevel, RefreshTimeStamp):
        '''插入招募记录'''
        RefreshValue = Gcore.getCfg('tb_cfg_building_up', key = (13, BuildingLevel), field = 'RefreshValue')
        valueClause = {
                       "StartTime":RefreshTimeStamp,
                       "EndTime":RefreshTimeStamp + RefreshValue,
                       "GeneralId1":ChosenGenerals[0],
                       "GeneralId2":ChosenGenerals[1],
                       "GeneralId3":ChosenGenerals[2],
                       "UserId":self.uid
                      }
        return self.db.insert('tb_general_invite', valueClause)
    
    def getFreeGeneralHomes(self, TimeStamp=None):
        '''返回空闲的点将台ID列表'''
        modBuilding = Gcore.getMod('Building', self.uid)
        GeneralHomes = modBuilding.getBuildingByType(18, TimeStamp=TimeStamp)
        GeneralHomes = [GeneralHome['BuildingId'] for GeneralHome in GeneralHomes 
                        if GeneralHome['BuildingState'] != 1]

        GeneralHomesUsed =self.db.out_rows(self.tb_general(), "Location", 
                                           'UserId=%s AND GeneralState!=%s' % (self.uid, 3))
        GeneralHomesUsed = [GeneralHomeUsed['Location'] for GeneralHomeUsed in GeneralHomesUsed]

        return [GeneralHome for GeneralHome in GeneralHomes 
                if GeneralHome not in GeneralHomesUsed]
    
    def patch2item(self, patch_id):
        '''获得碎片ID对应的武将卡的ItemID'''
        #没有该碎片，没有返回False
        try:
            patch_cfg = Gcore.getCfg('tb_cfg_general_patch')
            for item in patch_cfg.values():
                for k in item:
                    if k.startswith('PatchId') and item[k] == patch_id:
                        return item['ItemId']
            return False
        except Exception:
            return False
    
    def getPatchNum(self, flag=False):
        '''获取碎片的数量'''
        #flag-True只从数据库中查出有碎片的行
        table = 'tb_patch'
        if flag:
            where = 'UserId=%s AND (Patch1>0 OR Patch2>0 OR Patch3>0 OR Patch4>0)' % self.uid
        else:
            where = 'UserId=%s' % self.uid
        fields = ['ItemId', 'Patch1', 'Patch2', 'Patch3', 'Patch4']
        return self.db.out_rows(table, fields, where)

    def exchangeGeneralCard(self, item_id):
        '''兑换武将卡'''
        # 不满足兑换所需的数量返回False，
        # + 满足兑换所需的数量，减少相应的数量，并返回碎片的当前数量
        table = 'tb_patch'
        where = 'UserId=%s AND ItemId=%s' % (self.uid, item_id)
        #查出碎片数量
        fields = ['Patch1', 'Patch2', 'Patch3', 'Patch4']
        patch_num = self.db.out_fields(table, fields, where)
        if not patch_num:
            return False
        try:
            #从配置中查出所需的碎片数量
            item = Gcore.getCfg('tb_cfg_general_patch', item_id)
            
            for k in item:
                if k.startswith('PatchNum'):
                    column_name = 'Patch%d' % int(k[-1])
                    patch_num[column_name] -= item[k] #减少相应的数量
                    if patch_num[column_name] < 0:
                        return False
            
            #更新数据库
            self.db.update(table, patch_num, where)
            return patch_num         
        except Exception: return False
        else: return True

    #v1.1 - 已优化：同一ItemId对应的碎片数量改变，只更新一次数据库。
    #v1.0 - 已优化：参数patchs设计为字典，增加扩展性。
    def changePatchNum(self, patchs, flag=True):
        '''增加或减少碎片的数量'''
        # flag-True-增加，False-减少，默认是增加。
        # + 减少碎片时，如果任一种碎片数量不足，则返回False
        # + 参数不正确返回False，参数patchs(dict)：{碎片类型(int):数量(int), ...}
        try:
            assert isinstance(patchs, dict), '第一个参数是字典'
            cur_patch_num = self.getPatchNum()
            
            updates = {}
            for patch_type in patchs:
                item_id = self.patch2item(patch_type)
                if not item_id:
                    return False #没有这种碎片
                column_name = 'Patch%d'%(patch_type % 10)
                
                cur_num = 0 #碎片的当前数量
                tag = False #数据库中是否有该ItemId的记录
                for item in cur_patch_num:
                    if item['ItemId'] == item_id:
                        tag = True
                        cur_num = item[column_name]

                cur_num = cur_num + patchs[patch_type] if flag \
                            else cur_num - patchs[patch_type] #碎片的最新的数量
                cur_num = min(cur_num, 999) #碎片的最大数量 - 读配置
                if not flag and cur_num < 0: #减少碎片
                    return False #碎片数量不足
                
                d = updates.setdefault(item_id, {})
                d[column_name] = cur_num
                d['status'] = tag
            
            #更新数据库
            table = 'tb_patch'
            for item_id in updates:
                status = updates[item_id].pop('status')
                if status: #数据库中已有记录，更新
                    where = 'UserId=%s AND ItemId=%s' %(self.uid, item_id)
                    self.db.update(table, updates[item_id], where)
                else: #插入
                    updates[item_id].update({"ItemId":item_id, 
                                      "UserId":self.uid})
                    self.db.insert(table, updates[item_id])
            return True
        except Exception, e:
            print e
            return False #增加碎片失败 
        
    def getGeneralCardNum(self):
        '''获取背包中武将卡的数量'''
        item_ids = Gcore.getCfg('tb_cfg_general_patch').keys()
        modBag = Gcore.getMod('Bag', self.uid)
        return modBag.countGoodsNum(item_ids)
    
    def randDescPatch(self, num=1):
        '''随机减少num个碎片 
        @return: {碎片类型:减少的数量, }
        @remark: 攻城被抢夺
        '''
        patchs_num = self.getPatchNum(flag=True)
        if not patchs_num:
            return -1 #没有碎片
        patchs_num = list(patchs_num)

        chosens = []
        delete = []
        for _ in range(1, num+1, 1):
            c1 = random.choice(patchs_num)
            c2 = random.choice([k for k, v in c1.iteritems() 
                                if v > 0 and k.startswith('Patch')])
            chosens.append((c1['ItemId'], int(c2[-1])))
            c1[c2] -= 1
            
            remained = sum([v for k, v in c1.iteritems() 
                            if v > 0 and k.startswith('Patch')])
            if remained <= 0:
                delete.append(c1)
                patchs_num.remove(c1)
            if not patchs_num:
                break

        #更新数据库
        if delete:
            patchs_num.extend(delete)
        if patchs_num:
            sql = ' UPDATE tb_patch SET '
            patch1 = ' Patch1 = CASE ItemId '
            patch2 = ' Patch2 = CASE ItemId '
            patch3 = ' Patch3 = CASE ItemId '
            patch4 = ' Patch4 = CASE ItemId '
            for patch_num in patchs_num:
                patch1 += ' WHEN %s THEN %s ' % (patch_num['ItemId'], patch_num['Patch1'])
                patch2 += ' WHEN %s THEN %s ' % (patch_num['ItemId'], patch_num['Patch2'])
                patch3 += ' WHEN %s THEN %s ' % (patch_num['ItemId'], patch_num['Patch3'])
                patch4 += ' WHEN %s THEN %s ' % (patch_num['ItemId'], patch_num['Patch4'])
            patch1 += ' ELSE Patch1 END , '
            patch2 += ' ELSE Patch2 END , '
            patch3 += ' ELSE Patch3 END , '
            patch4 += ' ELSE Patch4 END '
            where = ' WHERE UserId=%s ' % self.uid
            
            sql += patch1 + patch2 + patch3 + patch4 + where
            self.db.execute(sql)

        #将碎片列表转成字典
        patchs = {}
        for cell in chosens:
            PatchId = Gcore.getCfg('tb_cfg_general_patch', cell[0],
                                   'PatchId%s'%cell[1])
            patchs[PatchId] = patchs.setdefault(PatchId, 0) + 1
        return patchs
#end class BuildingMod
