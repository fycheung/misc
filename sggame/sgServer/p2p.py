from socket import *
import time
from threading import Thread

sock = socket(AF_INET, SOCK_DGRAM)
for i in [1, 2]:
    remote_addr = "183.61.135.52", 40000
    sock.sendto("clientA", remote_addr)

    #sock = socket(AF_INET, SOCK_DGRAM)
    remote_addr = "103.5.57.52", 40000
    sock.sendto("clientA", remote_addr)
    time.sleep(3)


while 1:
    data = sock.recvfrom(1024)
    print 'data', data
    time.sleep(1)
