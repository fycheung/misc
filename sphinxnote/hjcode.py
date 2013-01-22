#coding=utf-8
import string
from array import array

def encode(s):
    temps = s.split(",")
    for i in range(0,len(temps)):
        temp = array('b')
        temp.fromstring(temps[i][::-1])
        n = len(temp)
        # nb = bytearray(n)
        for j in range(0,n):
            b1 = temp[j]
            if b1 == 90:
                b1=65
            elif b1 == 122:
                b1 = 97
            elif (b1>=65 and b1<90)or(b1>=97 and b1<122):
                b1+=1
            temp[j]=b1
        temps[i] = temp.tostring()
    news = string.join(temps,",")
    return(news)

def decode(s):
    temps = s.split(",")
    for i in range(0,len(temps)):
        temp = array('b')
        temp.fromstring(temps[i][::-1])
        n = len(temp)
        # nb = bytearray(n)
        for j in range(0,n):
            b1 = temp[j]
            if b1 == 65:
                b1=90
            elif b1 == 97:
                b1 = 122
            elif (b1>65 and b1<=90)or(b1>97 and b1<=122):
                b1-=1
            temp[j]=b1
        temps[i] = temp.tostring() 
    news = string.join(temps,",")
    return(news)