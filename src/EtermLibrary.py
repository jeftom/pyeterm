# -*- coding:utf-8 -*-
'''
Created on Oct 16, 2014

@author: czl
'''

import struct
import socket
from utils import hex_print
import uuid
import ConfigParser
import codecs

class EtermLibrary(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        self.sock = socket.socket()
        self.debug_level = 0
        
    def __getMac(self):
        node = uuid.getnode()
        mac = uuid.UUID(int=node)
        return mac.hex[-12:]
        
    def connect(self, host, port, user, password):
        self.sock.connect((host, port))
        
        buf = chr(0x1) + chr(0xa2)
        buf += user.ljust(16, chr(0))
        buf += password.ljust(32, chr(0))
        
        mac = self.__getMac()
        buf += mac.ljust(12, chr(0))
        
        localip = self.sock.getsockname()[0]
        buf += localip.ljust(16, chr(0x20))
        buf += "3832010.000000"
        buf = buf.ljust(162, chr(0))
        
        self.sock.send(buf)
        response = self.sock.recv(2048)
        if self.debug_level > 0:
            hex_print(response)


if __name__ == "__main__":
    config = ConfigParser.ConfigParser()
    config.readfp(codecs.open('config.cgi', 'r', 'utf-8-sig'))
    
    server = config.get("eterm", "server")
    port = config.getint("eterm", "port")
    username = config.get("eterm", "username")
    password = config.get("eterm", "password")
    
    el = EtermLibrary()    
    el.debug_level = 1 
    el.connect(server, port, username, password)   
    
    
        