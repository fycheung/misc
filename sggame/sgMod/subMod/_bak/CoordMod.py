#-*- coding:utf-8 -*-
from __future__ import division
import math

tileWidth = 43
tileHeight = 30
class CoordMod(object):

#    def pixel2coord(self,pixel):
#        '''像素转坐标'''
    
    @staticmethod
    def Coord2Pixel(x,y):
        '''坐标转为格子'''

        #偶数行tile中心
        tileCenter = (x * tileWidth) + tileWidth/2
        #x像素  如果为奇数行加半个宽
        xPixel = tileCenter + (y&1) * tileWidth/2
        #y像素
        yPixel = (y + 1) * tileHeight/2
        return (xPixel, yPixel)
    
    @staticmethod
    def ExpandCoord(x,y,xSize,ySize=None):
        '''扩展坐标，x,y为起始坐标，size为尺寸， 支持矩形
        @Author:Zhanggh 2013-4-11'''
        if ySize:#任何矩形坐标
            return CoordMod.calCoords(x, y, xSize, ySize)
        else:#正方形坐标
            return CoordMod.ExpandSquare(x, y, xSize)
    
    @staticmethod
    def ExpandSquare(x,y,size):
        '''扩展坐标，x,y为起始坐标，size为尺寸，只支持正方型
        @Author:Zhanggh 2013-4-11'''
        area = [(x,y)] #将起始坐标放到第一位
        for i in xrange(1,size+1): #每行的格子数
            #print '每行的格子数 i',i
            rd = size - i #与中间行的距离
            yt = y+rd
            xt = CoordMod.IncreaseX(x,y,rd) #将x向右上移动步数
            for j in xrange(i):
                if not (xt==x and yt==y):
                    area.append((xt,yt))
                    if rd>0:
                        area.append((xt,yt-2*rd)) #映射
                xt+=1
        if len(area)!=size*size:
            raise Exception('error expand ExpandCoord('+str(x)+','+str(y)+','+str(size)+')')
        #print area
        return area
    
    @staticmethod
    def IncreaseX(x,y,step):
        '''右上或左下移动step步的时候增加x
        @param step:大于0右上 , 小于0左下 
        '''
        if bool(y%2):
            x = x+math.ceil(step/2)
        else:
            x = x+step/2
        return int(x)
    
    @staticmethod
    def IncreaseLeftX(x,y,step):
        '''左上或右下移动step步的时候增加x
        @param step:大于0左上 , 小于0右下 
        '''
        if bool(y%2)==0:
            x = x-math.ceil(step/2)
        else:
            x = x-step/2
        return int(x)

    @staticmethod
    def Get9Coord(x,y,space=1,isSelf=True): 
        ''' 给出9宫格中心坐标和间隔，获取周边的军队中心坐标
        @param x:中心坐标x
        @param y:中心坐标y
        @param space: 军队间隔
        @param isSelf: True已方  False敌方 
        
        @return dict 包含9宫格的字典
        '''
        CoordDict = {}
        ix = space+3
        iy = (space+3)*2
        
        #第一行
        CoordDict[1] = (x,y+iy)
        CoordDict[2] = (CoordMod.IncreaseX(x, y, ix),y+ix)
        CoordDict[3] = (x+ix,y)
        #第二行 
        CoordDict[4] = (CoordMod.IncreaseLeftX(x, y, ix),y+ix)
        CoordDict[5] = (x,y) #中心
        CoordDict[6] = (CoordMod.IncreaseLeftX(x, y, -ix),y-ix)
        #第三行
        CoordDict[7] = (x-ix,y)
        CoordDict[8] = (CoordMod.IncreaseX(x, y, -ix),y-ix)
        CoordDict[9] = (x,y-iy)
        
        if not isSelf: #若是NPC作映射
            opCoordDict = {}
            opCoordDict[1] = CoordDict[9]
            opCoordDict[2] = CoordDict[8]
            opCoordDict[3] = CoordDict[7]
            opCoordDict[4] = CoordDict[6]
            opCoordDict[5] = CoordDict[5]
            opCoordDict[6] = CoordDict[4]
            opCoordDict[7] = CoordDict[3]
            opCoordDict[8] = CoordDict[2]
            opCoordDict[9] = CoordDict[1]
            CoordDict = opCoordDict
        '''
        if space == 1:
            #第一行
            CoordDict[1] = (x,y+8)
            CoordDict[2] = (CoordMod.IncreaseX(x, y, 4),y+4)
            CoordDict[3] = (x+4,y)
            #第二行 
            CoordDict[4] = (CoordMod.IncreaseLeftX(x, y, 4),y+4)
            CoordDict[5] = (x,y) #中心
            CoordDict[6] = (CoordMod.IncreaseLeftX(x, y, -4),y-4)
            #第三行
            CoordDict[7] = (x-4,y)
            CoordDict[8] = (CoordMod.IncreaseX(x, y, -4),y-4)
            CoordDict[9] = (x,y-8)
        elif space == 2:
            #第一行
            CoordDict[1] = (x,y+10)
            CoordDict[2] = (CoordMod.IncreaseX(x, y, 5),y+5)
            CoordDict[3] = (x+5,y)
            #第二行 
            CoordDict[4] = (CoordMod.IncreaseLeftX(x, y, 5),y+5)
            CoordDict[5] = (x,y) #中心
            CoordDict[6] = (CoordMod.IncreaseLeftX(x, y, -5),y-5)
            #第三行
            CoordDict[7] = (x-5,y)
            CoordDict[8] = (CoordMod.IncreaseX(x, y, -5),y-5)
            CoordDict[9] = (x,y-10)
        
        elif space == 3:
            #第一行
            CoordDict[1] = (x,y+12)
            CoordDict[2] = (CoordMod.IncreaseX(x, y, 6),y+6)
            CoordDict[3] = (x+6,y)
            #第二行 
            CoordDict[4] = (CoordMod.IncreaseLeftX(x, y, 6),y+6)
            CoordDict[5] = (x,y) #中心
            CoordDict[6] = (CoordMod.IncreaseLeftX(x, y, -6),y-6)
            #第三行
            CoordDict[7] = (x-6,y)
            CoordDict[8] = (CoordMod.IncreaseX(x, y, -6),y-6)
            CoordDict[9] = (x,y-12)
        '''
        return CoordDict
    
    @staticmethod
    def calCoords(x,y,xsize,ysize):
        '''
        :生成矩形拓展
        @param x:X坐标
        @param y:Y坐标
        @param xsize:X尺寸
        @param ysize:Y尺寸
        @Author:Zhanggh 2013-4-10
        '''
        coords = []
        xCoords = CoordMod.expandXY(x, y, xsize,'X')
        for x in xCoords:
            yCoords = CoordMod.expandXY(x[0],x[1],ysize,'Y')
            coords+=yCoords
        return coords
    
    @staticmethod
    def expandXY(x,y,count=1,direct='Y'):
        '''
        :往X,Y方向拓展一行坐标
        @param x:X坐标
        @param y:Y坐标
        @param direct:X方向，Y方向
        @param count:拓展格仔数量
        @Author:Zhanggh 2013-4-10
        '''
        clist = [(x,y)]
        p = (x,y)
        while count>1:
            if direct=='Y':
                p =(p[0],p[1]+1) if p[1]%2==0 else (p[0]+1,p[1]+1)
            else:
                p =(p[0],p[1]-1) if p[1]%2==0 else (p[0]+1,p[1]-1)
            clist.append(p)
            count-=1
        return clist

    
def test():
    #c = CoordMod()
    #print c.getBuidingCoords((18,39),5) #从坐标(2,2)开始取3*3的方格
    # c.pixel2coord((100,100))
#    print CoordMod.ExpandCoord(2,7,2,2)
#    print CoordMod.Get9Coord(11,46,2)
    #print CoordMod.IncreaseLeftX(11,46,1)
#    print CoordMod.calCoords(3, 4,2,2)
    print '1,4',CoordMod.Coord2Pixel(1, 4)
    print '1,3',CoordMod.Coord2Pixel(1, 3)
    print '1,2',CoordMod.Coord2Pixel(1, 2)
    print '1,1',CoordMod.Coord2Pixel(1, 1)
    
if __name__ == '__main__':
    test()