# -*- coding:utf-8 -*-
'''
Created on Oct 16, 2014

@author: czl
'''

from utils import hex_print
import uuid
import ConfigParser
import codecs
from matiplib import MATIP

class EtermLibrary(object):
    '''
    classdocs
    '''

    ver = 1

    def __init__(self, host, port):
        '''
        Constructor
        '''
        self.matip = MATIP(host, port)
        self.ascus = []
        self.currentSessionIndex = 0
        
    def __getMac(self):
        node = uuid.getnode()
        mac = uuid.UUID(int=node)
        return mac.hex[-12:]
        
    def login(self, username, password):
        ## 构造登录报文
        content = chr(self.ver)    # version
        content += chr(0xa2)       # 内容长度162个字节
        
        assert(len(username) <= 16)
        assert(len(password) <= 32)
        content += username.ljust(16, chr(0))
        content += password.ljust(32, chr(0))
        
        mac = self.__getMac()
        content += mac.ljust(12, chr(0))
        localip = self.sock.getsockname()[0]
        content += localip.ljust(16, chr(0x20))
        content += "3832010.000000"  #the magic code
        content = content.ljust(162, chr(0))
        
        ## 登录并记录session id
        self.matip.send(content)
        h1s = set()
        while 1:
            resp = self.matip.getreply()
            if ord(resp[0]) == 0 and ord(resp[1]) == len(resp):
                self.sessionCount = ord(resp[4])
                for i in range(self.sessionCount):
                    ind = 5+5*i
                    self.ascus.append(resp[ind:ind+5]) # save the H1 H2 A1 A2
                    
                    if resp[ind] != chr(0):
                        h1s.add(id)
                break
        
        ## ascus open
        content = self.matip.getSessionOpenPacket(cd=4, styp=1, mpx=0, hdr=0, pres=2, h1=0, h2=0)
        self.matip.send(content)
        resp = self.matip.getreply()
        
        content = ''
#         for h1 in (chr(0x0c), chr(0x29), chr(0x20)):
        for h1 in list(h1s):
            content += self.matip.getSessionOpenPacket(cd=4, styp=1, mpx=0, hdr=0, pres=2, h1=ord(h1), h2=0)
        self.matip.send(content)
        resp = self.matip.getreply()
                
    def changeToSession(self, index):
        self.currentSessionIndex = index - 1
    
    def sendCmd(self, cmd):
        data = "\x1b\x0b\x36\x20\x00\x0f\x1e"
        data += cmd.strip()
        data += "\x20"
        content = self.matip.getDataPacket(self.ascus[self.currentSessionIndex], data)
        resp = self.matip.send(content)
        return resp

if __name__ == "__main__":
    config = ConfigParser.ConfigParser()
    config.readfp(codecs.open('config.cgi', 'r', 'utf-8-sig'))
    
    server = config.get("eterm", "server")
    port = config.getint("eterm", "port")
    username = config.get("eterm", "username")
    password = config.get("eterm", "password")
    
    el = EtermLibrary(server, port)    
    el.login(username, password)
    el.sendCmd("da:")
    
       
    
    
        