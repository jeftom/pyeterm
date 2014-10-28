# -*- coding:utf-8 -*-
'''
Created on Oct 16, 2014

@author: czl
'''

from PyEterm.utils import hex_print
import uuid
import ConfigParser
import codecs
import os
from PyEterm.matiplib import MATIP
import re
import logging

class PyEtermLibrary(object):
    '''
    classdocs
    '''

    ver = 1
    debug_level = 0
    eterm_print_pattern = re.compile(r"([^\r]{80})")

    def __init__(self):
        '''
        Constructor
        '''
        self.matip = MATIP()
        self.ascus = []
        self.currentSessionIndex = 0
        
    def connect(self, host, port):
        if not isinstance(port, int):
            port = int(port)
        self.matip.connect(host, port)
        return "connect success"
        
    def __getMac(self):
        node = uuid.getnode()
        mac = uuid.UUID(int=node)
        return mac.hex[-12:]
        
    def login(self, username, password):
        if isinstance(username, unicode):
            username = username.encode("ascii", "ignore")
        if isinstance(password, unicode):
            password = password.encode("ascii", "ignore")
        
        ## 构造登录报文
        content = chr(self.ver)  # version
        content += chr(0xa2)  # 内容长度162个字节
        
        assert(len(username) <= 16)
        assert(len(password) <= 32)
        content += username.ljust(16, chr(0))
        content += password.ljust(32, chr(0))
        
        mac = self.__getMac()
        content += mac.ljust(12, chr(0))
        localip = self.matip.sock.getsockname()[0]
        content += localip.ljust(16, chr(0x20))
        content += "3832010.000000"  #the magic code
        content = content.ljust(162, chr(0))
        
        ## 登录并记录session id
        
        h1s = []
        while 1:
            self.matip.send(content)
            resp = self.matip.getreply()
            if ord(resp[0]) == 0 and ord(resp[1]) == len(resp) and ord(resp[2]) == 1:
                self.sessionCount = ord(resp[4])
                for i in range(self.sessionCount):
                    ind = 5 + 5 * i
                    self.ascus.append(resp[ind:ind + 5])  # save the H1 H2 A1 A2
                    if resp[ind] != chr(0):
                        h1s.append(resp[ind])
                break
            else:
                logging.error("login error")
        
        ## ascus open
        content = self.matip.getSessionOpenPacket(cd=4, styp=1, mpx=0, hdr=0, pres=2, h1=0, h2=0)
        self.matip.send(content)
        resp = self.matip.getreply()
        
        content = ''
#         for h1 in (chr(0x0c), chr(0x29), chr(0x20)):
        for h1 in h1s:
            content += self.matip.getSessionOpenPacket(cd=4, styp=1, mpx=0, hdr=0, pres=2, h1=ord(h1), h2=0)
        self.matip.send(content)
        resp = self.matip.getreply()
        resp = self.matip.getreply()
        return "login success"
                
    def changeToSession(self, index):
        if not isinstance(index, int):
            index = int(index)
        self.currentSessionIndex = index - 1
    
    def eterm_print(self, cmd, text):
        beginIndex = text.find("\x1b\x4d") + 2
        endIndex = text.rfind("\x1e\x1b\x62")
        content = ">" + cmd + "\r" + text[beginIndex:endIndex] + ">"
        content = self.eterm_print_pattern.sub(r"\1\r", content)
        content = content.replace('\x0d', os.linesep)
        print content
        return content
        
    def sendCmd(self, cmd):
        data = "\x02\x1b\x0b\x20\x20\x00\x0f\x1e"
        data += cmd.strip()
        data += "\x20"
        content = self.matip.getDataPacket(self.ascus[self.currentSessionIndex], data)
        
        if self.debug_level > 0:
            hex_print(content)
        self.matip.send(content)
        
        resp = self.matip.getreply()
        return self.eterm_print(cmd, resp)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.info("hello")
    
    config = ConfigParser.ConfigParser()
    config.readfp(codecs.open('../config.cgi', 'r', 'utf-8-sig'))
    
    server = config.get("eterm", "server")
    port = config.getint("eterm", "port")
    username = config.get("eterm", "username")
    password = config.get("eterm", "password")
    
    el = PyEtermLibrary()
    el.connect(server, port)   
    el.login(username, password)
    resp = el.sendCmd("da")
    resp = el.sendCmd("av:canpek/30oct/cz")
#    el.sendCmd("IHD:CA")
       
    
    
        
