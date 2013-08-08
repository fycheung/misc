# -*- coding: utf-8 -*-

#from datetime import datetime, timedelta
from time import time
class Timer:
    """
    用Tag标记的分段计时，可以用来测试某几段代码执行所用的时间
    """
    def __init__(self, name=None):
        self.__name = name;
        self.reset()
        
    def __tdSeconds(self, td):
        return td.seconds+td.days*3600*24;
    
    def timeit(self, tag=None):
        """
        将上次记录（或初始化）到现在时间累加到tag中，如果tag=None，则将这段时间丢弃
        返回：此tag的累计秒数
        """
        if tag is None:
            # self.__startTime=datetime.now();
            self.__startTime=time();
            
            return 0;
        if tag not in self.__tts:
            #self.__tts[tag] = (0, timedelta());
            self.__tts[tag] = (0, time());
        # delta = datetime.now() - self.__startTime;
        delta = round(time() - self.__startTime,3);
        # self.__startTime = datetime.now();
        self.__startTime = time();
        t, v = self.__tts[tag];
        self.__tts[tag] = (t+1, delta);
        # self.__tts[tag] = (t+1, v + delta);
        # return (self.__tts[tag][0], self.__tdSeconds(self.__tts[tag][1]));
        return (self.__tts[tag][0], self.__tts[tag][1]);
        
    def reset(self):
        """
        丢弃所有的计时，并将计时开始时间设为现在
        """
        # self.__startTime=datetime.now();
        self.__startTime=time();
        self.__tts = {};
        
    def __str__(self):
        #print self.__tts;
        s = "Timer:%s\n" % (self.__name or 'No name', );
        maxKeylen = max([len(str(k)) for k in self.__tts.keys()]);
        '''s += '\n'.join( [" %s: %s[%dS][avg:%s][times:%d]" % (str(k).rjust(maxKeylen), v, self.__tdSeconds(v), v/t, t) 
                         for k, (t,v) in self.__tts.iteritems() ]);'''

        s += '\n'.join( [" %s: %s" % (str(k).rjust(maxKeylen), v) 
                         for k, (t,v) in self.__tts.iteritems() ]);
        return s;


if __name__ == "__main__":
    def test(): #使用例子
        from time import sleep;
        tt = Timer('TestSleep');
        #sleep(1);
        sum(range(1,1000000))
        tt.timeit('sleep1');
        
        # sleep(2);
        #sum(range(1,10000000))
        tt.timeit('sleep2for');
        
        for i in range(2):
            '''sleep(1);
            tt.timeit();#丢弃这段代码消耗的时间
            sleep(2);
            sum(range(1,1000000))
            tt.timeit('sleep2for');'''
        
        
        print tt;
    
    test();